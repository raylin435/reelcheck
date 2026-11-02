import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from reelcheck.authority_v2 import new_task,action,render,make_spans,clean_reader_markup,ingest_tool,fork_task,truth_score,date_matches

class RenderingTests(unittest.TestCase):
 def setUp(self):
  self.t=new_task({'case_id':'x','group_id':'f','claim_text':'FDA’s “original” claim.','as_of':'2026-06-10','gold':'HIDDEN'},'cheap')
  self.t.update(searches=1,model_calls=3)
  text='June 10, 2026\nNot approved for children under 18.'
  self.t['evidence']=[{'id':'R1','url':'https://www.fda.gov/a','resolved_url':'https://www.fda.gov/a','text':text,'spans':make_spans('R1',text)}]
  self.obj={'action':'finish','answer':{'verdict':'contradicted','citations':[{'span_id':'R1.S002'}],'uncertainty_reason':None,'explanation':'The notice excludes children.'},'evidence_checks':[{'passage_id':'R1','issuer':'FDA','document_date':'2026-06-10','date_span_id':'R1.S001','scope_span_id':'R1.S002','effective_date':None,'effective_date_span_id':None,'supersession':'not_established','supersession_note':'Dated statement only.'}]}
 def test_renderer_preserves_claim_and_exact_selected_evidence(self):
  original=copy.deepcopy(self.obj);r=render(self.t,self.obj)
  self.assertEqual(self.obj,original)
  self.assertEqual(r['answer']['claim_text'],self.t['claim']['claim_text'])
  self.assertEqual(r['answer']['citations'][0]['quote'],'Not approved for children under 18.')
  self.assertEqual(r['answer']['verdict'],'contradicted')
  action(self.t,self.obj);self.assertEqual(self.t['status'],'completed')
 def test_unknown_or_wrong_page_spans_are_not_repaired(self):
  self.obj['answer']['citations'][0]['span_id']='R2.S002'
  with self.assertRaises(ValueError):render(self.t,self.obj)
  self.obj['answer']['citations'][0]['span_id']='R1.S002'
  self.obj['evidence_checks'][0]['passage_id']='R2'
  with self.assertRaises(ValueError):render(self.t,self.obj)
 def test_no_quote_or_verdict_invention(self):
  self.obj['answer']['citations']=[{'span_id':'R1.S002','quote':'Approved for all children'}]
  with self.assertRaises(ValueError):render(self.t,self.obj)
  self.obj['answer']['citations']=[]
  with self.assertRaises(ValueError):action(self.t,self.obj)
 def test_reader_removes_wrappers_without_changing_words_or_numbers(self):
  text='Not 【37†approved†fda.gov】 for children under 18; risk is 2.5%.'
  self.assertEqual(clean_reader_markup(text),'Not approved for children under 18; risk is 2.5%.')
 def test_ingest_delivers_only_numbered_spans_and_preserves_raw_hash(self):
  req={'action':'read','url':'https://www.fda.gov/a','request_id':'t001-s02','max_chars':16000}
  raw='FDA (https://www.fda.gov/a)\nL0: June 10, 2026\nL1: Not 【1†approved】 for children under 18.'
  event=ingest_tool(self.t,req,{'request_id':req['request_id'],'latency_s':1,'raw':raw},self.t['limits'])
  e=self.t['evidence'][-1];self.assertNotEqual(e['reader_page_sha256'],e['sha256'])
  obs=json.loads(self.t['messages'][-1]['content'])['untrusted_tool_result']['evidence']
  self.assertNotIn('text',obs);self.assertTrue(obs['spans'])
  self.assertTrue(event['raw_sha256']);self.assertNotIn('HIDDEN',json.dumps(self.t))
 def test_all_research_arms_receive_identical_rendering(self):
  self.t['status']='completed';self.t['output']=render(self.t,self.obj)['answer']
  tasks=[fork_task(self.t,x) for x in ('ordinary_retry','authority_recovery','metadata_only')]
  for t in tasks:action(t,self.obj)
  self.assertEqual(tasks[0]['output'],tasks[1]['output']);self.assertEqual(tasks[1]['output'],tasks[2]['output'])
 def test_cdc_september_abbreviation_is_not_a_missing_date(self):
  for q in ('Sept. 10, 2026','Sep. 10, 2026','September 10, 2026','09-10-2026'):
   self.assertTrue(date_matches('2026-09-10',q),q)
  self.assertFalse(date_matches('2026-09-11','Sept. 10, 2026'))

 def test_disputed_key_cannot_count_as_correct_or_incorrect(self):
  action(self.t,self.obj)
  self.assertIsNone(truth_score(self.t,{'verdict':'supported','review_status':'unresolved'})['reference_label_match'])

if __name__=='__main__':unittest.main()
