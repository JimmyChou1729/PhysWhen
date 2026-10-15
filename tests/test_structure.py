import unittest,copy
from physstyle.structure import validate_map,map_descriptors,inventory
from physstyle.common import read_json

class StructureTest(unittest.TestCase):
 def setUp(self):
  self.protocol=read_json('data/structure/protocol.json')
  self.packet={'paper_id':'fixture','version':1,'source_sha256':'hash','split':'discovery','main_body_paragraph_ids':['p1','p2'],'paragraphs':[{'paragraph_id':'p1','word_count':3,'blocks':[{'raw':'We ask why.'}]},{'paragraph_id':'p2','word_count':4,'blocks':[{'raw':'The result answers this.'}]}]}
  self.record={'protocol_version':'structure-v1','paper_id':'fixture','version':1,'source_sha256':'hash','split':'discovery','coverage':{'main_body':'full_read','abstract':'read','figures':'not_read','appendices':'not_read'},'moves':[{'start_paragraph_id':'p1','end_paragraph_id':'p2','role':'mixed','evidence':[{'paragraph_id':'p1','exact_quote':'We ask why.'}]}],'nodes':[{'id':'q','type':'question','text':'why','occurrences':[{'paragraph_id':'p1','exact_quote':'We ask why.','role':'development'}]},{'id':'c','type':'claim','text':'result','occurrences':[{'paragraph_id':'p2','exact_quote':'result answers','role':'development'}]}],'edges':[{'from':'c','to':'q','type':'addresses','basis':'explicit','rationale':'answer','evidence':[{'paragraph_id':'p2','exact_quote':'answers this.'}]}],'question_status':[{'question_id':'q','status':'answered','claim_ids':['c'],'evidence':[]}],'recurrences':[]}
 def test_valid_and_positions(self):
  self.assertEqual(validate_map(self.record,self.packet,self.protocol),[])
  d=map_descriptors(self.record,self.packet);self.assertEqual(d['denominators']['selected_nodes'],2);self.assertEqual(d['M03_claim_staging'][0]['positions']['development'],[3/7])
 def test_quote_and_identity_rejected(self):
  self.record['version']=2;self.record['nodes'][0]['occurrences'][0]['exact_quote']='invented claim'
  e=validate_map(self.record,self.packet,self.protocol);self.assertTrue(any('identity' in x for x in e));self.assertTrue(any('quote not found' in x for x in e))
 def test_coverage_overlap_rejected(self):
  self.record['moves'].append(copy.deepcopy(self.record['moves'][0]));self.assertIn('moves do not partition every main-body paragraph once in order',validate_map(self.record,self.packet,self.protocol))
 def test_invalid_edge_and_question_link_rejected(self):
  self.record['edges'][0]['type']='supports';e=validate_map(self.record,self.packet,self.protocol);self.assertTrue(any('typed direction' in x for x in e));self.assertIn('question claim missing addresses edge',e)
 def test_open_needs_source(self):
  self.record['question_status'][0].update(status='open',claim_ids=[]);self.assertTrue(any('missing evidence' in x for x in validate_map(self.record,self.packet,self.protocol)))
 def test_later_prerequisite_is_descriptor_not_error(self):
  self.record['nodes'].append({'id':'a','type':'premise','text':'late premise','occurrences':[{'paragraph_id':'p2','exact_quote':'The result','role':'development'}]})
  self.record['nodes'][1]['occurrences'][0]={'paragraph_id':'p1','exact_quote':'We ask why.','role':'development'}
  self.record['edges'].append({'from':'a','to':'c','type':'requires','basis':'inferred','rationale':'test presentation order only','evidence':[{'paragraph_id':'p2','exact_quote':'The result'}]})
  self.assertEqual(validate_map(self.record,self.packet,self.protocol),[])
  self.assertLess(map_descriptors(self.record,self.packet)['M03_dependency_order'][0]['dependent_minus_prerequisite'],0)
 def test_heldout_cannot_discover(self):
  self.record['split']=self.packet['split']='heldout';self.assertTrue(validate_map(self.record,self.packet,self.protocol))
if __name__=='__main__':unittest.main()
