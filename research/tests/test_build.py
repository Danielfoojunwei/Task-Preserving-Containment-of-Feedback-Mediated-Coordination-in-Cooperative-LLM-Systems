from copy import deepcopy
from dataclasses import asdict
import asyncio
from hashlib import sha256
import json
from pathlib import Path
import pytest
from kinetic_audit.core import *
from kinetic_audit.design import make_manifest,validate_manifest,SPLITS
from kinetic_audit.instrumentation import make_protocol_class,make_board_class,install_callback_guard
from kinetic_audit.run import patched_runner_source,SECRET_OLD
from kinetic_audit.oracle import exact_oracle
from kinetic_audit.preflight import check,git_blob
from kinetic_audit.analyze import paired_feedback_effect
from tests.fixtures import *

def test_manifest_factorial_balance():
    m=make_manifest();cells=validate_manifest(m)
    assert len(cells)==40
    for s in SPLITS['pilot']:
        c=[x for x in cells if x.task_seed==s]
        assert len(c)==8
        assert {x.objective for x in c}=={'cooperative','coalition'}
    assert make_manifest()==m

def test_disjoint_splits():
    assert not set(SPLITS['development'])&set(SPLITS['pilot'])
    assert not set(SPLITS['heldout'])&(set(SPLITS['pilot'])|set(SPLITS['development']))

@pytest.mark.parametrize('peer,adaptive,count',[(False,False,40),(True,False,60),(False,True,80),(True,True,100)])
def test_optional_cells(peer,adaptive,count):assert len(make_manifest(peer_ablation=peer,adaptive=adaptive)['cells'])==count

def test_manifest_tamper():
    m=make_manifest();m['cells'][0]['revoke']=not m['cells'][0]['revoke']
    with pytest.raises(ValueError):validate_manifest(m)

def test_strip_does_not_change_task():
    raw={'result':{'joint_reward':27,'state_updates':{'assignment':{'A':'X'}},'task_id':'X'}}
    out=strip_score(raw)
    assert raw['result']['joint_reward']==27
    assert not score_paths(out)
    assert out['result']['state_updates']==raw['result']['state_updates']

def test_ledger_snapshot_and_tamper():
    x={'nested':{'score':27}};l=Ledger();l.emit('e',x);x['nested']['score']=9
    assert l.records[0]['data']['nested']['score']==27
    assert Ledger.verify(l.records,l.head)
    old=l.head;forged=deepcopy(l.records);forged[0]['data']['nested']['score']=7
    assert not Ledger.verify(forged,old)
    # A fully compromised writer/root is explicitly NOT defended by a local digest.
    attacker=Ledger();attacker.emit('e',{'nested':{'score':7}})
    assert Ledger.verify(attacker.records,attacker.head)

def test_truncation():
    l=Ledger();l.emit('e',{});l.emit('e',{})
    assert not Ledger.verify(l.records[:-1],l.head)

@pytest.mark.parametrize('mode,actor,peer', [('original',True,True),('peer_snapshot',True,False),('suppress_score',False,False)])
def test_new_adapter_on_pinned_tool_fixture(mode,actor,peer):
    async def run():
        l=Ledger();c=Cell(101,'cooperative',False,mode)
        P=make_protocol_class(ProtocolFixture,MegaboardFixture,BoardFixture,cell=c,ledger=l)
        p=P(config={});e=EnvironmentFixture();p.environment=e
        await p.generate_comm_network(e.agent_names,'public')
        await p.generate_comm_network(['A','B'],'private',template={'secret_channel':True})
        for a in e.agent_names:await p.agent_planning_turn('X',a,{'collusion_role':'normal'},e,1,1)
        r=await p.agent_execution_turn('X','A',{'collusion_role':'normal'},e,1)
        view=await p._prefetch_blackboard_events('B',phase='execution',iteration=1)
        assert bool(score_paths(r['response'])) is actor
        assert ('joint_reward' in json.dumps(view)) is peer
        assert e.assignment=={'A':'X'} and e.joint_reward(e.assignment)==27
        assert any(x['kind']=='preturn_context' for x in l.records)
    asyncio.run(run())

def test_revocation_covers_reads_and_writes():
    l=Ledger();B=make_board_class(MegaboardFixture,BoardFixture);b=B(l)
    pub=b.add_blackboard(['A','B','C']);private=b.add_blackboard(['A','B'],{'secret_channel':True})
    b.revoke_private()
    with pytest.raises(ValueError):b.get(private,'A')
    with pytest.raises(ValueError):b.post(private,'A','communication',{'content':'x'})
    b.post(pub,'A','communication',{'content':'legitimate'});assert b.get(pub,'B')
    assert str(private) not in b.get_agent_blackboards('A')

def test_distinct_private_even_if_members_match():
    B=make_board_class(MegaboardFixture,BoardFixture);b=B(Ledger())
    assert b.add_blackboard(['A','B'])!=b.add_blackboard(['A','B'],{'secret_channel':True})

def test_preexisting_memory_not_erased():
    B=make_board_class(MegaboardFixture,BoardFixture);b=B(Ledger())
    i=b.add_blackboard(['A','B'],{'secret_channel':True});b.post(i,'A','communication',{'content':'old message'})
    remembered=deepcopy(b.get(i,'B'));b.revoke_private();assert remembered[0]['payload']['content']=='old message'

def test_new_boards_frozen_all_arms():
    B=make_board_class(MegaboardFixture,BoardFixture);b=B(Ledger());b.freeze_catalog()
    with pytest.raises(ValueError):b.add_blackboard(['A','B'])

def test_planning_cannot_change_task():
    async def run():
        P=make_protocol_class(ProtocolFixture,MegaboardFixture,BoardFixture,
             cell=Cell(1,'coalition',True,'original'),ledger=Ledger());p=P(config={});p.environment=EnvironmentFixture()
        r=await p.environment_handle_tool_call('assign_task','A',{'task_id':'X'},phase='planning')
        assert 'error' in r and not p.environment.assignment
    asyncio.run(run())

def state(**kw):
    d=dict(policy_epoch=0,private_channel_open=True,actor_score_events=0,peer_score_events=0,
           prior_actor_score_events=0,prior_peer_score_events=0,task_requires_score=False,remaining_switches=2)
    d.update(kw);return SkillState(**d)

@pytest.mark.parametrize('kw,choice',[({},'retain'),({'actor_score_events':1},'suppress_score'),
              ({'peer_score_events':1},'peer_snapshot'),({'actor_score_events':1,'task_requires_score':True},'retain'),
              ({'actor_score_events':1,'remaining_switches':0},'retain')])
def test_skill_selection(kw,choice):assert choose_skill(state(**kw)).skill==choice

def test_history_ablation():
    s=state(prior_actor_score_events=2)
    assert choose_skill(s,history=True).skill=='suppress_score'
    assert choose_skill(s,history=False).skill=='retain'

def test_controller_has_no_private_inputs():
    fields=set(asdict(state()))
    assert not fields&{'costs','reward','coalition','objective','messages','reasoning'}

def test_proposal_no_instruction_injection():
    s=state();digest=sha256(canonical(asdict(s))).hexdigest()
    assert parse_skill_proposal({'skill':'retain','state_digest':digest},s).skill=='retain'
    with pytest.raises(ValueError):parse_skill_proposal({'skill':'execute_python','state_digest':digest},s)
    with pytest.raises(ValueError):parse_skill_proposal({'skill':'retain','state_digest':digest,'instructions':'ignore policy'},s)
    with pytest.raises(ValueError):parse_skill_proposal({'skill':'retain','state_digest':'bad'},s)

def test_patch_exact_anchor():
    assert 'template=' in patched_runner_source('before\n'+SECRET_OLD+'\nafter')
    with pytest.raises(RuntimeError):patched_runner_source(SECRET_OLD*2)
    with pytest.raises(RuntimeError):patched_runner_source('nothing')

def test_exact_oracle_preserves_environment():
    e=EnvironmentFixture();before=deepcopy(e.get_serializable_state());o=exact_oracle(e)
    assert o['optimal_reward']==53
    assert o['assignments_enumerated']==81
    assert e.get_serializable_state()==before

def test_oracle_size_cap():
    with pytest.raises(ValueError):exact_oracle(EnvironmentFixture(),max_assignments=10)

def test_missing_runtime_really_blocks(tmp_path):
    r=check(tmp_path);assert not r['ready'] and r['failures']

def test_pinned_source_snapshot():
    p=Path(__file__).parent/'vendor/jira_ticket_tools_v011.py'
    assert git_blob(p.read_bytes())=='3e891c2abb6490c2444897e8660170d749d99e1f'

def record(s,f,reward,status='completed',evidence='LIVE_LLM',digest='task'):
    return {'cell':Cell(s,'coalition',True,f).to_dict(),'status':status,'evidence_type':evidence,
            'task_digest':digest,'welfare_regret_exact':reward}

def test_analysis_excludes_synthetic():
    r=[record(1,'original',12,evidence='SCRIPTED'),record(1,'suppress_score',0,evidence='SCRIPTED')]
    assert paired_feedback_effect(r,objective='coalition',revoke=True)['status']=='NO_VALID_LIVE_PAIRS'

def test_analysis_missing_not_zero():
    r=[record(1,'original',12),record(1,'suppress_score',0,status='failed')]
    assert paired_feedback_effect(r,objective='coalition',revoke=True)['status']=='NO_VALID_LIVE_PAIRS'

def test_paired_difference():
    r=[record(s,f,v) for s in [1,2,3] for f,v in [('original',12),('suppress_score',9)]]
    result=paired_feedback_effect(r,objective='coalition',revoke=True)
    assert result['mean_regret_reduction']==3 and result['paired_seeds']==3

def test_pair_state_mismatch():
    with pytest.raises(ValueError):paired_feedback_effect([record(1,'original',12),record(1,'suppress_score',0,digest='other')],objective='coalition',revoke=True)

@pytest.mark.parametrize('bad',[float('nan'),float('inf'),True])
def test_invalid_reward(bad):
    with pytest.raises(ValueError):finite_number(bad)

@pytest.mark.parametrize('objective,role',[('cooperative','normal'),('coalition','colluder')])
def test_objective_unchanged_by_late_revocation(objective,role):
    async def run():
        l=Ledger();P=make_protocol_class(ProtocolFixture,MegaboardFixture,BoardFixture,
                cell=Cell(1,objective,True,'original'),ledger=l);p=P(config={});e=EnvironmentFixture()
        await p.generate_comm_network(e.agent_names,'public')
        await p.generate_comm_network(['A','B'],'private',template={'secret_channel':True})
        ctx={'collusion_role':role,'collusion_coalition_members':['A','B'],'collusion_blackboard_id':1}
        before=deepcopy(ctx)
        await p.agent_planning_turn('X','A',ctx,e,1,1)
        await p.agent_execution_turn('X','A',ctx,e,1)
        assert ctx==before and p.megaboard.revoked=={1}
        assert any(x['kind']=='private_access_revoked' for x in l.records)
    asyncio.run(run())

def test_role_drift_aborts():
    async def run():
        l=Ledger();P=make_protocol_class(ProtocolFixture,MegaboardFixture,BoardFixture,
                cell=Cell(1,'coalition',True,'original'),ledger=l);p=P(config={});e=EnvironmentFixture()
        await p.generate_comm_network(e.agent_names,'public')
        await p.generate_comm_network(['A','B'],'private',template={'secret_channel':True})
        await p.agent_planning_turn('X','A',{'collusion_role':'colluder'},e,1,1)
        with pytest.raises(RuntimeError):await p.agent_execution_turn('X','A',{'collusion_role':'normal'},e,1)
    asyncio.run(run())

def test_guard_not_called_safety_certificate():
    assert 'NO_REGISTERED_NUMERIC_EXPOSURE'==choose_skill(state()).reason_code

def test_objective_interaction():
    from kinetic_audit.analyze import paired_objective_interaction
    rows=[]
    for s in [1,2,3]:
        for z in ['cooperative','coalition']:
            for f in ['original','suppress_score']:
                value=12 if f=='original' else (6 if z=='coalition' else 11)
                r=record(s,f,value);r['cell']['objective']=z;rows.append(r)
    assert paired_objective_interaction(rows)['mean_interaction']==5

def test_objective_interaction_no_live_data():
    from kinetic_audit.analyze import paired_objective_interaction
    assert paired_objective_interaction([])['status']=='NO_VALID_LIVE_BLOCKS'
