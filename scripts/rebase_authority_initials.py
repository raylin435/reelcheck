"""Reuse unaffected initial histories after the explicitly recorded Sept. checker fix."""
from copy import deepcopy
import json,shutil,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run_authority_v2 import init,branch
from run_research import persist,save,accounting
from reelcheck.__main__ import upper_cost
from reelcheck.research import now

def rebase(oldroot,newroot):
 oldroot=Path(oldroot);newroot=Path(newroot)
 prior=[]
 for i in range(4):
  old=oldroot/f'shard-{i}';state=json.loads((old/'state.json').read_text())
  if state.get('in_flight'):raise ValueError('Wait for all provider calls before correction')
  if any(t['status']=='active' for t in state['tasks'] if t['phase']!='recovery'):raise ValueError('Initial tasks not terminal')
  unique={c['call_index']:c for t in state['tasks'] for c in t['calls']}
  prior.append({'shard':i,'calls':accounting(list(unique.values())),'active_recovery_tasks':sum(t['phase']=='recovery' and t['status']=='active' for t in state['tasks']),'pending_requests':[t['pending'] for t in state['tasks'] if t.get('pending')]})
  out=newroot/f'shard-{i}'
  args=SimpleNamespace(out=str(out),config=str(ROOT/'config.authority_v2.json'),partition='development',shards=4,shard=i,canary=False)
  init(args);new=json.loads((out/'state.json').read_text())
  inherited=deepcopy([t for t in state['tasks'] if t['phase'] in ('initial','diagnostic')])
  for a,b in zip(inherited,new['tasks']):
   if (a['case_id'],a['system'],a['claim'],a['messages'][0])!=(b['case_id'],b['system'],b['claim'],b['messages'][0]):raise ValueError('Initial prompt/input changed; reuse forbidden')
  calls={c['call_index']:c for t in inherited for c in t['calls']}
  if set(calls)!=set(range(1,len(calls)+1)):raise ValueError('Initial journal is not contiguous')
  reserved=0.
  for t in inherited:
   variant=state['config'][t['model_role']]
   for c in t['calls']:
    index=c['call_index'];request=json.loads((old/f'candidate-request-{index:03}.json').read_text());reserved+=upper_cost(variant,request)
    for kind in ('request','response'):shutil.copy2(old/f'candidate-{kind}-{index:03}.json',out/f'candidate-{kind}-{index:03}.json')
   for e in t['tools']:
    name=e['request']['request_id']+'-web.json';shutil.copy2(old/name,out/name)
  new.update(tasks=inherited,calls_attempted=len(calls),candidate_reserved_usd=reserved,initial_reuse={'parent':str(old),'reason':'Sept. date recognition correction; identical initial prompts/observations; all initial failures retained','parent_source_hashes':state['source_hashes']},inherited_call_indices=sorted(calls))
  branch(new);persist(out,new)
 save(oldroot/'ABORTED.json',{'recorded_at':now(),'status':'invalid_controller_experiment_not_scored','reason':'False metadata rejection of CDC Sept. abbreviation. Initial histories reused unchanged; every recovery branch rerun under v2.1, no held-out outputs used.','shards':prior})
 print('Initial histories reused; prior recovery experiment preserved.')

if __name__=='__main__':rebase(ROOT/'results/authority-v2-development',ROOT/'results/authority-v21-development')
