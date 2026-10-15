"""Native reward enumeration: past selected cost and future decision relevance."""
import itertools
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
BASE=Path('/workspace/colosseum_task_preserving_starter')
sys.path[:0]=[str(BASE),'/workspace/colosseum']
import yaml
from envs.dcops.jira_ticket.jira_ticket_env import JiraTicketEnvironment
from experiments.common.local_protocol import LocalCommunicationProtocol
from kinetic_audit.preflight import check

def main():
    assert check(Path('/workspace/colosseum'))['ready']
    rows=[]
    for seed in range(5001,5021):
        cfg=yaml.safe_load(Path('/workspace/colosseum/experiments/collusion/configs/collusion_jira_topologies.yaml').read_text())
        cfg['simulation']['seed']=seed;cfg['communication_network']['num_agents']=4
        cfg['environment'].update(max_tasks=8,assignment_filling=False)
        cfg['logging']={'root_dir':str(ROOT/'relevance_logs')}
        protocol=LocalCommunicationProtocol(config=cfg)
        env=JiraTicketEnvironment(protocol,cfg,tool_logger=type('TL',(),{'log_dir':ROOT})())
        names=env.get_agent_names();past=names[0];task=next(iter(env.tasks))
        original=env.costs[past][task]
        choices=list(itertools.product([*env.tasks,'skip'],repeat=3))
        vectors=[];maxima=[]
        for cost in [1.,10.,50.]:
            env.costs[past][task]=cost
            values=[]
            for combo in choices:
                actions={past:task,**dict(zip(names[1:],combo))}
                values.append(float(env._rewards(actions)[0]))
            best=max(values)
            maxima.append([i for i,v in enumerate(values) if abs(v-best)<=1e-8])
            vectors.append(values)
        env.costs[past][task]=original
        expected_shifts=[0.,-9.,-49.]
        max_shift_error=max(abs(vectors[j][i]-vectors[0][i]-expected_shifts[j])
                            for j in range(3) for i in range(len(choices)))
        invariant=maxima[0]==maxima[1]==maxima[2]
        if not invariant or max_shift_error>1e-8:raise RuntimeError('Decision-irrelevance certificate falsified')
        rows.append({'seed':seed,'past_actor':past,'fixed_past_task':task,'future_assignments':len(choices),
            'past_cost_twins':[1.,10.,50.],'max_constant_shift_error':max_shift_error,
            'identical_future_argmax_sets':invariant,'maximizing_assignments':len(maxima[0])})
    out={'status':'PASSED_NATIVE_DECISION_IRRELEVANCE_CHECK','evidence_type':'SCRIPTED_NATIVE_REWARD_ENUMERATION_NOT_LLM_BEHAVIOR',
         'seeds':20,'native_reward_evaluations':sum(r['future_assignments']*3 for r in rows),
         'scope':'One prior irreversible feasible claim fixed, other task/cost data fixed; vary only its finite selected-task cost. Native feasibility, duplicate penalties, skip and reward weights retained.',
         'interpretation':'Past selected cost changes future rewards by a constant; revealing it alone cannot change the conditional welfare-optimal future allocation in these native one-shot instances. Other hidden future costs, objective incentives, attention and repeated tasks are outside this claim.',
         'cases':rows}
    (ROOT/'decision_relevance_certificate.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='cases'}))

if __name__=='__main__':main()
