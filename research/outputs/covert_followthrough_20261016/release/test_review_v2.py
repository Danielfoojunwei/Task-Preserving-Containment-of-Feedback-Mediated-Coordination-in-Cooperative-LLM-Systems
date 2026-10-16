import importlib.util
from pathlib import Path
import unittest
sp=importlib.util.spec_from_file_location('ft_review_schema_v2',Path(__file__).with_name('review_v2.py'));V=importlib.util.module_from_spec(sp);sp.loader.exec_module(V)
class SchemaTests(unittest.TestCase):
 def test_explicit_aliases(self):
  for left,right in ((1,2),('f1','f2'),('round1','round2'),('rounds1','rounds2'),('1','2')):
   raw={'prefixes':[{'prefix':left,'harmful_active':True},{'prefix':right,'harmful_active':False}]}
   got=V.normalize(raw);self.assertEqual([x['round'] for x in got['prefixes']],[1,2]);self.assertNotIn('round',raw['prefixes'][0])
   self.assertTrue(got['prefixes'][0]['harmful_active']);self.assertFalse(got['prefixes'][1]['harmful_active'])
 def test_no_order_inference(self):
  for raw in ({'prefixes':[{},{}]},{'prefixes':[{'prefix':'f2'},{'prefix':'f1'}]},
     {'prefixes':[{'prefix':'r1'},{'prefix':'r2'}]},{'prefixes':[{'prefix':'f1'}]},
     {'prefixes':[{'prefix':True},{'prefix':2}]},{'prefixes':[{'round':1,'prefix':'f2'},{'round':2}]}):
   self.assertEqual(V.normalize(raw),raw)
 def test_existing_explicit_round_unchanged(self):
  raw={'prefixes':[{'round':1,'evidence':None},{'round':2,'expected_actions':{}}]}
  self.assertEqual(V.normalize(raw),raw)
if __name__=='__main__':unittest.main()
