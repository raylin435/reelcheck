import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from reelcheck.research import initial_task
from reelcheck.recovery import recovery_task,recover_action,judge_messages_v2
from run_recovery import branch,consensus,INITIAL_LIMITS


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.case={'case_id':'c','claim_text':'Twelve trials passed.','as_of':'2026-11-02','gold':'HIDDEN'}
        self.initial=initial_task(self.case,{'id':'cheap_draft'})
        self.initial.update(phase='initial',model_role='cheap',model_calls=4,searches=1,reads=2,
            status='invalid_output',validation_errors=['invalid exact quote for R1'],
            limits=INITIAL_LIMITS.copy(),calls=[{'call_index':1,'cost_usd':.01}],
            evidence=[{'id':'R1','text':'Twelve trials passed.'}],
            discovered_urls=['https://example.org/record'],last_answer={'claim_text':'Twelve trials passed.'})

    def test_forks_share_exact_inputs_and_limits_but_do_not_mutate_each_other(self):
        original=copy.deepcopy(self.initial)
        a=recovery_task(self.initial,'generic_retry');b=recovery_task(self.initial,'targeted_recovery')
        for key in ['draft','evidence','tools','calls','discovered_urls','limits','claim']:
            self.assertEqual(a[key],b[key])
        self.assertEqual(a['limits']['max_model_calls']-a['model_calls'],5)
        self.assertEqual(a['limits']['max_searches']-a['searches'],1)
        self.assertEqual(a['limits']['max_reads']-a['reads'],2)
        b['evidence'][0]['text']='changed'
        self.assertNotEqual(a['evidence'],b['evidence'])
        self.assertEqual(original,self.initial)
        self.assertNotIn('HIDDEN',json.dumps(a))
        self.assertNotIn('HIDDEN',json.dumps(b))

    def test_targeted_query_requires_gap_and_enforces_same_search_cap(self):
        t=recovery_task(self.initial,'targeted_recovery')
        with self.assertRaises(ValueError):recover_action(t,{'action':'search','query':'trials'})
        request=recover_action(t,{'action':'search','gap':'Original record was unavailable','query':'trials original report'})
        self.assertEqual(request['query'],'trials original report')
        self.assertEqual(t['searches'],2)
        with self.assertRaises(ValueError):recover_action(t,{'action':'search','gap':'more','query':'extra'})

    def test_invalid_draft_can_be_corrected_but_invalid_final_is_not_repaired(self):
        t=recovery_task(self.initial,'generic_retry')
        answer={'claim_text':self.case['claim_text'],'verdict':'supported',
                'citations':[{'passage_id':'R1','quote':'Twelve trials passed.'}],
                'uncertainty_reason':None,'explanation':'The record reports twelve passes.'}
        bad=copy.deepcopy(answer);bad['citations'][0]['quote']='Thirteen trials passed.'
        with self.assertRaises(ValueError):recover_action(t,{'action':'finish','answer':bad})
        recover_action(t,{'action':'finish','answer':answer})
        self.assertEqual(t['status'],'completed')
        self.assertEqual(t['draft_status'],'invalid_output')

    def test_branch_waits_for_all_drafts_and_is_idempotent(self):
        active=copy.deepcopy(self.initial);active['status']='active';active['model_role']='reference'
        state={'branches_created':False,'tasks':[self.initial,active]}
        branch(state);self.assertEqual(len(state['tasks']),2)
        active['status']='completed';branch(state)
        self.assertEqual(len(state['tasks']),5)
        self.assertEqual({t['system'] for t in state['tasks'][2:]},{'generic_retry','targeted_recovery','strong_reference'})
        branch(state);self.assertEqual(len(state['tasks']),5)

    def test_disagreement_is_unresolved_not_a_success(self):
        t={'status':'completed','judge_votes':{'a':{'accepted':True},'b':{'accepted':False}}}
        self.assertIsNone(consensus(t))
        t['judge_votes']['b']['accepted']=True;self.assertTrue(consensus(t))
        t['status']='invalid_output';self.assertFalse(consensus(t))


if __name__=='__main__':unittest.main()
