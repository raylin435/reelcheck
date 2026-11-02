from argparse import Namespace
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from reelcheck.machine_jury import jury_messages, vote_errors, initial_agreement, resolve
from reelcheck.references import fingerprint, reference_case, load_references
from reelcheck.semantic import semantic_messages, semantic_config
from reelcheck.contract import validate
from scripts.report_machine_eval import metrics, paired, verify_audit_binding

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('semantic_runner', ROOT/'scripts/run_semantic_comparison.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class MachineEvalTests(unittest.TestCase):
    def setUp(self):
        text = 'The observed value was 18 degrees.'
        self.case = {'case_id': 'c', 'group_id': 'g', 'as_of': '2026-11-02', 'claim_text': text,
                     'evidence': [{'id': 'p', 'text': text, 'sha256': hashlib.sha256(text.encode()).hexdigest()}],
                     'gold': 'SECRET_GOLD', 'reviewer_notes': 'SECRET_NOTES'}
        self.answer = {'claim_text': text, 'verdict': 'supported', 'citations': [{'passage_id': 'p', 'quote': text}],
                       'uncertainty_reason': None, 'explanation': 'The observed reading matches.'}
        self.variant = {'id': 'base', 'provider': 'fireworks', 'model': 'test', 'output_mode': 'schema_quotes',
                        'max_output_tokens': 256, 'parameters': {}, 'pricing': {'input_per_million': .15, 'output_per_million': .6}}

    def record(self, model, verdict='supported', *, ambiguous=False):
        return {'model': model, 'execution_status': 'completed', 'output': {'verdict': verdict,
            'confidence': 'high', 'scope_ambiguous': ambiguous, 'evidence_ids': ['p'], 'rationale': 'A specific evidence reason.'}}

    def test_independent_and_candidate_prompts_exclude_labels_and_other_vote_metadata(self):
        self.assertNotIn('SECRET', json.dumps(jury_messages(self.case)))
        draft = {**self.answer, 'gold': 'SECRET_DRAFT', 'system': 'SECRET_MODEL'}
        self.assertNotIn('SECRET', json.dumps(semantic_messages(self.case, draft)))
        self.assertNotIn('previous_draft', json.dumps(jury_messages(self.case)))

    def test_agreement_and_third_vote_resolution(self):
        a,b,c = self.record('a'), self.record('b','insufficient'), self.record('c')
        self.assertFalse(initial_agreement([a,b]))
        self.assertEqual(resolve(self.case,[a,b])['acceptable_verdicts'],[])
        ref=resolve(self.case,[a,b,c])
        self.assertEqual(ref['acceptable_verdicts'],['supported'])
        self.assertEqual(ref['review_status'],'machine_adjudicated')
        self.assertEqual(resolve(self.case,[a,c])['review_status'],'machine_consensus')

    def test_ambiguity_cannot_be_majority_voted_away_or_same_model_counted_twice(self):
        rows=[self.record('a'),self.record('b',ambiguous=True),self.record('c')]
        self.assertEqual(resolve(self.case,rows)['review_status'],'machine_unresolved')
        with self.assertRaises(ValueError):
            resolve(self.case,[self.record('a'),self.record('a')])

    def test_malformed_low_confidence_and_unknown_evidence_are_not_agreement(self):
        vote=self.record('a')['output']
        self.assertTrue(vote_errors({**vote,'evidence_ids':['unknown']},self.case))
        self.assertTrue(vote_errors({**vote,'scope_ambiguous':'false'},self.case))
        self.assertTrue(vote_errors({**vote,'rationale':[]},self.case))
        a=self.record('a');a['output']['confidence']='low'
        self.assertFalse(initial_agreement([a,self.record('b')]))

    def test_unresolved_machine_bundle_loads_without_claiming_human_review(self):
        ref=resolve(self.case,[self.record('a'),self.record('b','insufficient')])
        bundle={'schema_version':2,'review_track':'machine_reviewed','human_reviewed':False,
                'frozen_at':datetime.now(timezone.utc).isoformat(),'references':[ref],'references_sha256':fingerprint([ref])}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'refs.json';p.write_text(json.dumps(bundle))
            got,refs=load_references(p,[self.case])
            self.assertFalse(got['human_reviewed']);self.assertEqual(refs['c']['acceptable_verdicts'],[])
            bundle['human_reviewed']=True;p.write_text(json.dumps(bundle))
            with self.assertRaises(ValueError):load_references(p,[self.case])

    def test_semantic_map_gate_cannot_support_an_explicitly_missing_requirement(self):
        mapped={**self.answer,'requirements':[{'id':'r','text':'The reading was observed.', 'relation':'missing','citations':[]}]}
        self.assertIn('support requires coverage of every declared requirement',validate(mapped,self.case,require_map=True))
        cfg=semantic_config(self.variant,self.case)
        self.assertIn('requirements',cfg['parameters']['response_format']['json_schema']['schema']['required'])
        self.assertNotIn('response_format',self.variant['parameters'])

    def test_shared_baseline_billed_once_but_treatment_includes_both_stages(self):
        ref=resolve(self.case,[self.record('a'),self.record('b')])
        bundle={'schema_version':2,'review_track':'machine_reviewed','human_reviewed':False,
                'frozen_at':datetime.now(timezone.utc).isoformat(),'references':[ref],'references_sha256':fingerprint([ref])}
        baseline={'case_id':'c','system':'base','execution_status':'completed','output':self.answer,'call_index':1,
                  'cost_usd':.001,'latency_s':1.}
        mapped={**self.answer,'requirements':[{'id':'r','text':'The reading was observed.', 'relation':'supports','citations':self.answer['citations']}]}
        second={'execution_status':'completed','output':mapped,'cost_usd':.002,'latency_s':2.}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'inputs.jsonl').write_text(json.dumps(self.case)+'\n')
            (p/'refs.json').write_text(json.dumps(bundle))
            (p/'config.json').write_text(json.dumps({'variants':[self.variant,{**self.variant,'id':'check'}]}))
            args=Namespace(config=str(p/'config.json'),inputs=str(p/'inputs.jsonl'),references=str(p/'refs.json'),out=str(p/'out'),live=True,shell_keys=None,max_calls=2,max_cost_usd=1.)
            with patch.dict('os.environ',{'FIREWORKS_API_KEY':'FAKE'}),patch.object(runner,'_execute',return_value=baseline),patch.object(runner,'call',return_value=second):
                runner.run(args)
            summary=json.loads((p/'out/summary.json').read_text())
            self.assertEqual(summary['paid_calls_attempted'],2)
            self.assertAlmostEqual(summary['estimated_actual_run_cost_usd'],.003)
            self.assertAlmostEqual(summary['systems']['check']['estimated_total_cost_usd'],.003)
            self.assertEqual(summary['systems']['check']['p50_latency_s'],3.)

    def test_unresolved_reference_is_not_a_wrong_answer_and_gate_rejection_cannot_hide_one(self):
        cases=[{**self.case,'case_id':i} for i in ('resolved','unresolved')]
        rows=[{'case_id':c['case_id'],'system':'base','execution_status':'invalid_output',
               'output':self.answer,'cost_usd':.001,'latency_s':1.} for c in cases]
        refs={'resolved':{'acceptable_verdicts':['insufficient']},'unresolved':{'acceptable_verdicts':[]}}
        judges=[{'case_id':c['case_id'],'system':'base','model_assessed_acceptance':False} for c in cases]
        m=metrics(cases,rows,judges,refs)
        self.assertEqual(m['reference_coverage'],.5)
        self.assertEqual(m['wrong_decisive_emitted'],1)
        self.assertEqual(m['wrong_decisive_valid'],0)
        self.assertEqual(m['valid_reference_matches'],0)
        self.assertEqual(m['cases'],2)
        self.assertEqual(m['deployment_cost_usd'],.002)

    def test_paired_unknown_is_neither_win_nor_loss(self):
        cases=[{**self.case,'case_id':str(i)} for i in range(4)]
        statuses=[(False,True),(True,False),(True,True),(False,None)]
        judges=[{'case_id':c['case_id'],'system':s,'model_assessed_acceptance':status}
                for c,pair in zip(cases,statuses) for s,status in zip(('base','check'),pair)]
        result=paired(cases,judges,['base','check'])
        for k,v in zip(('wins','losses','ties','unresolved'),('0','1','2','3')):
            self.assertEqual(result[k],[v])

    def test_fidelity_reuse_allows_only_evidence_revisions(self):
        from reelcheck.__main__ import digest
        original={**self.case,'provenance':{'media_sha256':'hash','start_seconds':1,'end_seconds':2}}
        revised=copy.deepcopy(original)
        revised['evidence'][0]['text']='A corrected evidence packet.'
        manifest={'mode':'live','inputs_sha256':digest([original])}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'inputs.jsonl';p.write_text(json.dumps(original)+'\n')
            verify_audit_binding(manifest,[revised],p)
            revised['claim_text']='A revised claim.'
            with self.assertRaises(ValueError):verify_audit_binding(manifest,[revised],p)
            revised['claim_text']=original['claim_text']
            revised['provenance']['start_seconds']=1.5
            with self.assertRaises(ValueError):verify_audit_binding(manifest,[revised],p)

    def test_unresolved_reference_skips_judge_in_dry_and_live_modes(self):
        from scripts import judge_run
        ref=resolve(self.case,[self.record('a'),self.record('b','insufficient')])
        bundle={'schema_version':2,'review_track':'machine_reviewed','human_reviewed':False,
                'frozen_at':datetime.now(timezone.utc).isoformat(),'references':[ref],'references_sha256':fingerprint([ref])}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'run').mkdir()
            (p/'inputs.jsonl').write_text(json.dumps(self.case)+'\n')
            rp=p/'refs.json';rp.write_text(json.dumps(bundle))
            (p/'config.json').write_text(json.dumps({'judge':self.variant}))
            row={'case_id':'c','system':'base','execution_status':'completed','output':self.answer}
            (p/'run/runs.jsonl').write_text(json.dumps(row)+'\n')
            from reelcheck.__main__ import digest
            (p/'run/manifest.json').write_text(json.dumps({'inputs_sha256':digest([self.case]),
                'case_count':1,'frozen_reference_file_sha256':hashlib.sha256(rp.read_bytes()).hexdigest(),
                'created_at':datetime.now(timezone.utc).isoformat()}))
            for live in (False,True):
                args=Namespace(config=str(p/'config.json'),role=None,inputs=str(p/'inputs.jsonl'),run=str(p/'run'),
                    references=str(rp),systems=None,out=str(p/str(live)),live=live,max_calls=1,max_cost_usd=1.,
                    interval=0,env=str(p/'none'),shell_keys=None)
                with patch.dict('os.environ',{'FIREWORKS_API_KEY':'FAKE'}),patch.object(judge_run,'call') as api:
                    judge_run.run_judge(args);api.assert_not_called()
                if live:
                    j=json.loads((p/str(live)/'judgments.jsonl').read_text())
                    self.assertIsNone(j['model_assessed_acceptance'])
                    self.assertEqual(j['judge_status'],'unresolved_machine_reference')
                else:
                    preview=json.loads((p/str(live)/'request_preview.jsonl').read_text())
                    self.assertFalse(preview['would_call']);self.assertFalse(preview['would_reuse'])


if __name__=='__main__':
    unittest.main()
