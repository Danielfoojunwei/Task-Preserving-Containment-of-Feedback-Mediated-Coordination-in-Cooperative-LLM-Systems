"""Raw reconstruction, tampering, payment and accounting tests; no live calls."""
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
HERE=Path(__file__).resolve().parent
def module(name,file):
    sp=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
V=module('ft_independent_test','independent_verify.py')
T=module('ft_transport_fixture','test_runner.py');R=T.s
class IndependentTests(unittest.TestCase):
    def test_strict_json(self):
        for text in ('{"a":1,"a":2}','{"a":NaN}','{"a":1e10000}'):
            with self.assertRaises(ValueError):V.strict_json(text)
        self.assertFalse(V.numeric(True));self.assertEqual(V.amount(True),0)
    def test_finite_gate_certificate(self):
        c=V.finite_certificate();self.assertEqual(c['one_actor_states_checked'],363)
        self.assertEqual(c['excess_violations'],0);self.assertEqual(c['lawful_payment_component_changes'],0)
    def test_correct_quarter_liability(self):
        fin=V.financial({'A':3,'B':5},{'A':10,'B':10},{'A':10,'B':10})
        self.assertEqual(fin['scores'],{'A':Fraction(23,4),'B':Fraction(13,4)})
        self.assertEqual(fin['net_owner_loss'],9)
        gated=V.financial({'A':3,'B':5},{'A':10,'B':10},{'A':10,'B':10},True)
        self.assertEqual(gated['net_owner_loss'],0);self.assertTrue(gated['both_receipts_paid'])
    def test_invalid_auditor_grounding(self):
        for ev in ([],[{'turn_id':'p','quote':'invented'}]):
            out=V.parse_auditor(json.dumps({'flag':True,'reason':'x','evidence':ev}),{'public_reports':[{'turn_id':'p','text':'done'}]})
            self.assertIsNone(out['flag']);self.assertFalse(out['flag_valid'])
    def test_unknown_budget_preserved(self):
        b=V.budget_events([{'reserved_usd':2,'reserved_at':'1','started_at':'2','finished_at':None,'cost_usd':None}],8.5)
        self.assertEqual(b['accounted_including_unknown_cost_usd'],Decimal(2));self.assertFalse(b['failures'])
    def test_full_synthetic_round_raw_reconstruction(self):
        # Four distinct controls exercise both scoring rules, all contexts and state transitions.
        for spec in R.build_plan()['controls']:
            with self.subTest(spec=spec['session_id']),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);plan=R.build_plan()
                R.parent.save_new(root/'plan.json',plan);R.parent.save_new(root/'prompt_material.json',R.prompt_material())
                R.parent.save_new(root/'FREEZE.json',{'sha256':{},'frozen_at':'0'})
                rt=R.Runtime(root,T.FakeClient());case=plan['cases'][str(spec['seed'])][0]
                result=rt.run_round('controls',spec,R.initial_state(),case)
                audit=V.Audit(root,'controls');new=audit.round('controls',spec,audit.initial(spec),case)
                self.assertEqual(new,result);self.assertEqual(audit.failures,[])
                self.assertEqual(len(audit.calls),9)
                # A one-cell derived payment alteration is caught from unmodified provider wire.
                path=root/'runs/controls'/spec['session_id']/'rounds/1/outcome.json'
                broken=R.parent.load(path);broken['payments']['A']=-1;path.write_text(json.dumps(broken))
                tamper=V.Audit(root,'controls');tamper.round('controls',spec,tamper.initial(spec),case)
                self.assertTrue(any(x['check']=='actual_payment_settlement' for x in tamper.failures))
if __name__=='__main__':unittest.main()
