import json,sys,tempfile,threading,time
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase,mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import advance_authority_concurrent as runner
from reelcheck.authority_v2 import new_task

class ConcurrentTests(TestCase):
 def test_parallel_calls_have_unique_durable_journals_and_no_inflight_left(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);active=0;peak=0;guard=threading.Lock()
   for shard in range(2):
    out=root/f'shard-{shard}';(out/'source_snapshot/scripts').mkdir(parents=True)
    tasks=[new_task({'case_id':f'c{shard}-{i}','group_id':'g','claim_text':f'Claim {i}','as_of':'2026-11-02'},'cheap',True) for i in range(3)]
    state={'tasks':tasks,'source_hashes':{},'in_flight':None,'branches_created':False,'partition':'development','config':{'cheap':{},'candidate_cost_cap_usd':1},'candidate_reserved_usd':0.,'calls_attempted':0}
    (out/'state.json').write_text(json.dumps(state))
   def fake_call(config,messages):
    nonlocal active,peak
    with guard:active+=1;peak=max(peak,active)
    time.sleep(.025)
    with guard:active-=1
    return {'execution_status':'completed','output':{'action':'finish','answer':{'verdict':'insufficient','citations':[],'uncertainty_reason':'missing_evidence','explanation':'No reference available.'}},'cost_usd':.001,'usage':{}}
   with mock.patch.object(runner,'keys'),mock.patch.object(runner,'upper_cost',return_value=.01),mock.patch.object(runner,'call',side_effect=fake_call):
    runner.advance(SimpleNamespace(run=str(root),workers=4,live=True,shell_keys=''))
   self.assertGreater(peak,1);self.assertLessEqual(peak,4)
   for out in sorted(root.glob('shard-*')):
    state=json.loads((out/'state.json').read_text())
    self.assertIsNone(state['in_flight']);self.assertEqual(state['calls_attempted'],3)
    self.assertEqual({c['call_index'] for t in state['tasks'] for c in t['calls']},{1,2,3})
    self.assertEqual(len(list(out.glob('candidate-response-*.json'))),3)
    for t in state['tasks']:self.assertEqual(t['status'],'completed')
    self.assertAlmostEqual(state['candidate_reserved_usd'],.03)
