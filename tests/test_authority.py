import copy
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from reelcheck.authority import new_task, fork_task, metadata_errors, issuer_for, action, truth_score
from run_authority import dataset, load_jsonl, init, verify

class AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.case=dict(case_id='x',group_id='family',claim_text='FDA announced a warning.',as_of='2026-09-15',gold='SECRET',reference_excerpt='SECRET')
        self.t=new_task(self.case,'cheap')
        self.t.update(model_calls=4,searches=1,reads=1,status='completed')
        self.t['evidence']=[dict(id='R1',url='https://www.fda.gov/notice',resolved_url='https://www.fda.gov/notice',text='September 15, 2026\nFDA announced a warning for Product A. Effective September 1, 2026.')]
        self.a=dict(claim_text=self.case['claim_text'],verdict='supported',citations=[dict(passage_id='R1',quote='FDA announced a warning for Product A.')],uncertainty_reason=None,explanation='The dated notice states this.')
        self.check=dict(passage_id='R1',issuer='FDA',document_date='2026-09-15',date_quote='September 15, 2026',scope_quote='FDA announced a warning for Product A.',effective_date=None,effective_date_quote=None,supersession='not_established',supersession_note='No claim of exhaustiveness.')
    def test_candidates_never_get_reference_fields(self):
        self.assertNotIn('SECRET',json.dumps(self.t))
    def test_exact_authority_host_and_redirect(self):
        for url in ['https://fda.gov.evil.org/x','https://fda.gov@evil.org','http://fda.gov','https://fda.gov:8443','https://notfda.gov','https://fda.gov\\@evil.org']:
            self.assertIsNone(issuer_for(url),url)
        self.assertEqual(issuer_for('https://www.accessdata.fda.gov/x'),'FDA')
        self.t['evidence'][0]['resolved_url']='https://evil.org/x'
        self.assertTrue(metadata_errors(self.t,self.a,[self.check]))
    def test_dates_are_quoted_and_not_retrieval_dates(self):
        self.assertEqual(metadata_errors(self.t,self.a,[self.check]),[])
        for value in ['2027-01-01',None,'not-a-date','20260915']:
            c={**self.check,'document_date':value}
            self.assertTrue(metadata_errors(self.t,self.a,[c]))
        self.t['claim']['as_of']='2026-09-14'
        self.assertTrue(metadata_errors(self.t,self.a,[self.check]))
    def test_effective_date_is_separate(self):
        c={**self.check,'effective_date':'2026-09-01','effective_date_quote':'Effective September 1, 2026.'}
        self.assertEqual(metadata_errors(self.t,self.a,[c]),[])
        c['effective_date']='2026-09-15';self.assertTrue(metadata_errors(self.t,self.a,[c]))
    def test_each_citation_needs_one_exact_scope_check(self):
        self.assertTrue(metadata_errors(self.t,self.a,[]))
        self.assertTrue(metadata_errors(self.t,self.a,[self.check,self.check]))
        self.assertTrue(metadata_errors(self.t,self.a,[{**self.check,'scope_quote':'FDA approves Product B.'}]))
    def test_shared_forks_and_equal_budget(self):
        forks=[fork_task(self.t,arm) for arm in ('ordinary_retry','authority_recovery','metadata_only')]
        for key in ('claim','draft','evidence','calls','tools','limits'):
            self.assertEqual(forks[0][key],forks[1][key]);self.assertEqual(forks[1][key],forks[2][key])
        self.assertEqual(forks[1]['limits']['max_model_calls']-forks[1]['model_calls'],5)
        forks[1]['evidence'][0]['text']='changed';self.assertNotEqual(forks[0]['evidence'],forks[1]['evidence'])
    def test_gate_consumes_existing_budget_and_does_not_fabricate_abstention(self):
        t=fork_task(self.t,'authority_recovery');limits=copy.deepcopy(t['limits'])
        obj=dict(action='finish',answer=self.a,evidence_checks=[{**self.check,'document_date':None}])
        t['model_calls']+=1;self.assertIsNone(action(t,obj));self.assertEqual(t['status'],'active')
        self.assertIsNone(t['output']);self.assertEqual(t['limits'],limits)
        t['model_calls']=t['limits']['max_model_calls']
        with self.assertRaises(ValueError):action(t,obj)
    def test_baseline_audits_without_extra_correction(self):
        t=fork_task(self.t,'ordinary_retry');action(t,dict(action='finish',answer=self.a,evidence_checks=[]))
        self.assertEqual(t['status'],'completed');self.assertTrue(t['metadata_audits'][-1]['errors'])
    def test_recovery_cannot_invent_evidence_or_gain_searches(self):
        t=fork_task(self.t,'authority_recovery')
        with self.assertRaises(ValueError):action(t,dict(action='search',query='FDA'))
        action(t,dict(action='search',gap='date missing',query='FDA date'))
        with self.assertRaises(ValueError):action(t,dict(action='search',gap='date missing',query='more'))
        with self.assertRaises(ValueError):action(t,dict(action='read',url='https://www.fda.gov/not-discovered'))
    def test_retrieval_failure_is_not_correct_insufficiency(self):
        t=copy.deepcopy(self.t);t['output']={**self.a,'verdict':'insufficient','uncertainty_reason':'missing_evidence'}
        self.assertFalse(truth_score(t,dict(verdict='supported'))['reference_label_match'])
        self.assertTrue(truth_score(t,dict(verdict='supported'))['operational_abstention'])
        self.assertFalse(truth_score(t,dict(verdict='insufficient',uncertainty_reason='missing_context'))['reference_label_match'])
    def test_dataset_hashes_split_isolation_and_balance(self):
        dataset();p=ROOT/'data/authority_v1'
        a=load_jsonl(p/'development.jsonl');b=load_jsonl(p/'heldout.jsonl')
        self.assertEqual(len(a),20);self.assertEqual(len(b),20)
        self.assertFalse({c['group_id'] for c in a}&{c['group_id'] for c in b})
        for split in (a,b):
            for cat in {c['category'] for c in split}:self.assertEqual(sum(c['category']==cat for c in split),5)
    def test_runner_freezes_and_tool_ingest_has_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            args=SimpleNamespace(out=tmp,config=ROOT/'config.recovery.fresh.json',canary=True)
            init(args);s=json.loads((Path(tmp)/'state.json').read_text());verify(s)
            self.assertIn('limits',s);self.assertEqual(len(s['selected_case_ids']),4)
            self.assertFalse(any('reference_excerpt' in json.dumps(t) for t in s['tasks']))

if __name__=='__main__':unittest.main()
