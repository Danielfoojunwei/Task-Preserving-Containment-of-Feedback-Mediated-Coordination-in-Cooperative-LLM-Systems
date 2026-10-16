"""Fixed endpoint, missing-evidence and annotation validation regression tests."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('ft_analysis_test',HERE/'analyze.py');A=importlib.util.module_from_spec(sp);sp.loader.exec_module(A)
class AnalysisTests(unittest.TestCase):
    def test_exact_null_with_ties(self):
        r=A.exact_test([0]*16);self.assertEqual(r['p']['value'],1);self.assertEqual(r['extreme_assignments'],65536)
    def test_exact_unidirectional_extreme(self):
        r=A.exact_test([-1]*16);self.assertEqual(r['extreme_assignments'],2);self.assertEqual(r['effect']['value'],-1)
    def test_incomplete_cohort_rejected(self):
        with self.assertRaises(ValueError):A.exact_test([0]*15)
    def test_three_valued_logic(self):
        self.assertIsNone(A.conjunction(True,None));self.assertFalse(A.conjunction(False,None))
        self.assertIsNone(A.invert(None));self.assertIsNone(A.any_round([False,None]))
        with self.assertRaises(ValueError):A.conjunction(1)
    def test_action_terms(self):
        amounts={'claims':{'A':10,'B':10},'approvals':{'A':10,'B':10}}
        self.assertTrue(A.implemented(amounts,amounts,True))
        unknown={'claims':{'A':10,'B':None},'approvals':{'A':10,'B':10}}
        self.assertIsNone(A.implemented(unknown,amounts,True))
        wrong={'claims':{'A':4,'B':None},'approvals':{}}
        self.assertFalse(A.implemented(wrong,amounts,True))
    def test_direction_and_actual_delivery_of_acceptance(self):
        notes=[{'turn_id':'a','actor':'A','text':'claim ten','note_valid':True,'delivered_to':['A','B']},
            {'turn_id':'b','actor':'B','text':'I agree','note_valid':True,'delivered_to':['A','B']}]
        prop={'turn_id':'a','quote':'claim ten'};accept={'turn_id':'b','quote':'I agree'}
        self.assertTrue(A.Q.pair_valid(notes,prop,accept))
        notes[0]['delivered_to']=['A'];self.assertFalse(A.Q.pair_valid(notes,prop,accept))
        notes[0]['delivered_to']=['A','B'];notes[1]['note_valid']=False
        self.assertFalse(A.Q.pair_valid(notes,prop,accept))
    def test_malformed_annotation_is_null_not_positive(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(A.Q,'HERE',Path(tmp)):
            root=Path(tmp);packet={'prefixes':[{'round':n,'notes':[],'public_reports':[]} for n in (1,2)]}
            job={'packet_path':'packet.json','call_path':'review','kind':'initial'}
            A.Q.P.save_new(root/'packet.json',packet)
            raw={'prefixes':[{'round':n,'harmful_active':True,'concealment_active':True,'public_disclosure':True,'evidence':None,'public_evidence':None,'expected_actions':None} for n in (1,2)]}
            content=json.dumps(raw);wire={'choices':[{'message':{'content':content}}]}
            A.Q.P.save_new(root/'calls/review/call.json',{'provider_response_text':json.dumps(wire),'raw_content':content})
            result=A.Q.parse(job)
            self.assertTrue(all(r['harmful_active'] is None and r['concealment_active'] is None and r['public_disclosure'] is None for r in result['prefixes']))
if __name__=='__main__':unittest.main()
