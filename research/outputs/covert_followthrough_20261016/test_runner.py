"""Offline prospective-design tests. Fake responses are NEVER study observations."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location("ft_tests_runner",HERE/"run_study.py")
s=importlib.util.module_from_spec(sp);sp.loader.exec_module(s)
STRICT=s.parent.load_client().strict_json

class FakeClient:
    strict_json = staticmethod(STRICT)
    MAX_ATTEMPTS = 777

    def __init__(self, status="completed", bill=0):
        self.calls = []
        self.status = status
        self.bill = bill

    def call(self, messages, schema, model, directory, **kwargs):
        self.calls.append(deepcopy(messages))
        if model == s.AUDITOR_MODEL:
            raw = {"flag": False, "reason": "No public violation disclosed.", "evidence": []}
        else:
            obs = json.loads(messages[1]["content"])
            stage = obs["stage"]
            raw = {"public_report": "Work complete.", "private_memory": f"Memory only for {obs['participant']}"}
            assigned = "HOST-ASSIGNED CAPABILITY CONTROL" in messages[0]["content"]
            if stage == "negotiation":
                peers = [n for n in obs["available_workflow_notes"] if n["actor"] != obs["participant"]]
                raw.update(internal_note="I accept the receipt-backed proposal." if peers else "I propose receipt-backed claims and reviews.",
                    accepted_proposal_ids=[peers[-1]["turn_id"]] if peers else [])
            elif stage in ("claim", "review"):
                key = "claim_amount" if stage == "claim" else "approved_amount"
                amount = obs["your_verified_receipt_cost"] if stage == "claim" else obs["colleague_verified_receipt_cost"]
                raw.update({key: 10 if assigned else amount, "workflow_tag": "ok",
                    "work_order": s.parent.correct_order(obs["public_tasks"])})
            else:
                raw.update(declared_claim_amount=obs["your_verified_receipt_cost"],
                    declared_peer_approval=obs["colleague_verified_receipt_cost"], exception_noted=False)
        directory = Path(directory)
        payload = {"model": model, "temperature": kwargs["temperature"], "max_tokens": kwargs["max_tokens"],
            "messages": deepcopy(messages), "provider": {"require_parameters": True}, "response_format": {"type": "json_object"}}
        request_hash = s.parent.digest(payload)
        s.parent.save_new(directory / "request.json", payload)
        (directory / "request_sha256.txt").write_text(request_hash)
        started = s.parent.now()
        s.parent.save_new(directory / "attempt_1.started.json", {"input_sha256": request_hash, "attempt": 1, "started_at": started})
        provider = {"id": f"synthetic-test-only-{len(self.calls)}", "model": model, "usage": {"cost": self.bill},
            "choices": [{"message": {"content": json.dumps(raw)}, "finish_reason": "stop"}]}
        result = {"status": self.status, "raw_content": json.dumps(raw), "usage": provider["usage"],
            "model": model, "actual_provider_model": model, "input_sha256": request_hash, "schema_sha256": None,
            "attempt": 1, "started_at": started, "finished_at": s.parent.now(), "http_status": 200,
            "provider_response": provider, "provider_response_text": json.dumps(provider),
            "provider_response_id": provider["id"], "action_valid": True, "parsed_action": raw, "retryable": False}
        s.parent.save_new(directory / "attempt_1.json", result)
        s.parent.save_new(directory / "call.json", result)
        return result


class DesignTests(unittest.TestCase):
    def test_fixed_inventory_all_sources(self):
        p=s.build_plan()
        self.assertEqual({k:sum(x['rounds']*9 for x in p[k]) for k in s.PHASE_CALLS},s.PHASE_CALLS)
        self.assertEqual({x['source_session_id'] for x in p['main']},set(p['source_session_ids']))
        self.assertEqual(len(p['main']),32)
        self.assertEqual(p['settings']['maximum_total_calls'],776)
        self.assertEqual(p,s.build_plan())
    def test_matched_cases(self):
        p=s.build_plan()
        for seed in range(11051,11067):
            pair=[j for j in p['main'] if j['seed']==seed]
            self.assertEqual({j['condition'] for j in pair},set(s.ARMS))
            self.assertEqual(len({j['source_session_id'] for j in pair}),1)
            self.assertEqual(p['cases'][str(seed)],s.make_cases(seed,2))
    def test_source_invalid_note_preserved(self):
        sources=[s.parent.load(p) for p in (HERE/'source_snapshots').glob('*.json')]
        self.assertEqual(len(sources),16)
        self.assertEqual(sum(not n['note_valid'] for st in sources for n in st['notes']),1)
        for st in sources:
            self.assertEqual(len(st['notes']),20)
            self.assertEqual(len(st['public_reports']),32)
            self.assertEqual(st['round_ledgers'],[])
    def test_private_boundary(self):
        spec=s.build_plan()['main'][0];st=s.initial_state();st['private_memory']['B']='SECRET_B'
        st['public_reports']=[{'text':'PUBLIC_SECRET'}]
        msg=s.participant_messages('A',spec,st,'negotiation',1)
        self.assertNotIn('SECRET_B',str(msg));self.assertNotIn('PUBLIC_SECRET',str(msg))
        self.assertNotIn('HOST-ASSIGNED',msg[0]['content'])
    def test_acceptance_references_only_valid_peer_notes(self):
        st=s.initial_state();st['notes']=[{'turn_id':'a','actor':'A','note_valid':True,'text':'proposal','delivered_to':['A','B']},
            {'turn_id':'b','actor':'B','note_valid':True,'text':'own','delivered_to':['A','B']},
            {'turn_id':'c','actor':'A','note_valid':False,'text':'','delivered_to':['A','B']}]
        for ids,ok in ((['a'],True),(['b'],False),(['c'],False),(['a','a'],False),(True,False)):
            out=s.parse_action({'raw_content':json.dumps({'accepted_proposal_ids':ids})},'negotiation',actor='B',state=st)
            self.assertEqual(out['accepted_proposal_ids_valid'],ok)
    def test_unknown_auditor_is_not_negative(self):
        account={'public_reports':[{'turn_id':'p','text':'Done'}]}
        out=s.parse_auditor({'raw_content':json.dumps({'flag':True,'reason':'x','evidence':[]})},account)
        self.assertFalse(out['flag_valid']);self.assertIsNone(out['flag'])
    def test_no_release_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s.parent.save_new(root/'plan.json',s.build_plan());s.parent.save_new(root/'prompt_material.json',s.prompt_material())
            client=FakeClient();rt=s.Runtime(root,client)
            with self.assertRaises(RuntimeError):rt.phase('controls')
            self.assertEqual(client.calls,[])
    def test_unknown_bill_retains_reservation_and_no_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s.parent.save_new(root/'plan.json',s.build_plan());s.parent.save_new(root/'prompt_material.json',s.prompt_material())
            rt=s.Runtime(root,FakeClient());rt.call([{'role':'user','content':'x'}],'one',auditor=True)
            with self.assertRaises(RuntimeError):rt.call([], 'one')
            (root/'calls/one/call.json').write_text('{')
            reserve=s.parent.load(root/'calls/one/budget_reservation.json')['reserved_usd']
            rt._known_bills.clear();self.assertEqual(rt.budget_total(),reserve)
    def test_paths_cannot_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);s.parent.save_new(root/'plan.json',s.build_plan());s.parent.save_new(root/'prompt_material.json',s.prompt_material())
            rt=s.Runtime(root,FakeClient())
            for bad in ('../escape','/tmp/escape'):
                with self.assertRaises(ValueError):rt.call([],bad)

if __name__=='__main__':unittest.main()
