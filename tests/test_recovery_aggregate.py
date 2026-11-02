import copy
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from aggregate_recovery import combine,ARMS


def state(cid):
    call={'call_index':1,'cost_usd':0.01,'latency_s':1}
    tasks=[]
    for arm in ARMS:
        tasks.append({'case_id':cid,'system':arm,'group_id':'g','phase':'recovery',
            'status':'completed','calls':[copy.deepcopy(call)],'searches':1,'reads':1,
            'output':{'verdict':'supported'},'judge_votes':{
                'a':{'accepted':True,'cost_usd':.001},'b':{'accepted':True,'cost_usd':.001}}})
    return {'tasks':tasks,'branches_created':True,'in_flight':None}


class AggregateTests(unittest.TestCase):
    def test_local_call_indices_do_not_collapse_across_shards(self):
        report,_=combine([state('a'),state('b')])
        self.assertEqual(report['candidate_actual_billing']['calls'],2)
        self.assertAlmostEqual(report['candidate_actual_billing']['estimated_cost_usd'],.02)
        self.assertEqual(report['cases'],2)

    def test_execution_failure_and_missing_judgment_stay_in_denominator(self):
        s=state('a');s['tasks'][0].update(status='truncated',output=None,judge_votes={})
        report,_=combine([s]);self.assertEqual(report['paired_outcomes'],{'win':1})
        self.assertEqual(report['both_completed_paired_outcomes'],{})
        self.assertEqual(report['systems']['generic_retry']['cases'],1)
        s['tasks'][1]['judge_votes']['b']['accepted']=None
        report,_=combine([s]);self.assertEqual(report['paired_outcomes'],{'unresolved':1})

    def test_duplicate_case_or_unfinished_run_is_rejected(self):
        with self.assertRaises(ValueError):combine([state('a'),state('a')])
        s=state('b');s['tasks'][0]['status']='active'
        with self.assertRaises(ValueError):combine([s])


if __name__=='__main__':unittest.main()
