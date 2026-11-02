"""Concurrent execution-only addendum: same frozen prompts, actions and budgets."""
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
import argparse,fcntl,hashlib,json
from contextlib import ExitStack
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run_authority_v2 import verify,branch
from run_research import keys,persist,save
from reelcheck.authority_v2 import action
from reelcheck.research import prompt,now
from reelcheck.__main__ import upper_cost,digest
from reelcheck.providers import call


def advance(args):
 keys(args)
 if not 1<=args.workers<=32:raise ValueError('workers must be 1..32')
 paths=sorted(Path(args.run).glob('shard-*'))
 if not paths:raise ValueError('No shards')
 runner_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 with ExitStack() as stack:
  runs=[]
  for out in paths:
   lock=stack.enter_context((out/'runner.lock').open('a'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
   state=json.loads((out/'state.json').read_text())
   if state.get('in_flight'):raise ValueError('Wait for active/interrupted calls; no implicit retry')
   verify(state)
   prior=state.get('concurrent_executor_sha256')
   if prior and prior!=runner_hash:raise ValueError('Concurrent executor changed during run')
   state['concurrent_executor_sha256']=runner_hash
   if not (out/'source_snapshot/scripts/advance_authority_concurrent.py').exists():
    (out/'source_snapshot/scripts/advance_authority_concurrent.py').write_bytes(Path(__file__).read_bytes())
    save(out/'concurrency-addendum.json',{'created_at':now(),'reason':'User explicitly requested maximal practical API concurrency during held-out execution. Scheduling only; frozen prompts, model configurations, limits, evidence and scoring unchanged.','executor_sha256':runner_hash,'workers':args.workers})
   runs.append((out,state))
  # Interleave shards; one next turn per eligible task in this pass, just as before.
  queues=[]
  for out,state in runs:
   queue=[]
   for index,t in enumerate(state['tasks']):
    if t['status']!='active' or t.get('pending'):continue
    if t['model_calls']>=t['limits']['max_model_calls']:
     t['status']='model_call_limit';continue
    queue.append((out,state,index,t))
   queues.append(queue)
  jobs=[q[i] for i in range(max(map(len,queues),default=0)) for q in queues if i<len(q)]
  next_job=0;pending={};stop=False
  with ThreadPoolExecutor(max_workers=args.workers) as pool:
   while pending or (next_job<len(jobs) and not stop):
    while len(pending)<args.workers and next_job<len(jobs) and not stop:
     out,state,index,t=jobs[next_job];next_job+=1
     variant=state['config'][t['model_role']];messages=prompt(t,t['limits']);bound=upper_cost(variant,messages)
     if state['candidate_reserved_usd']+bound>state['config']['candidate_cost_cap_usd']:
      t['status']='cost_budget_exhausted';persist(out,state);continue
     state['candidate_reserved_usd']+=bound;state['calls_attempted']+=1
     t['started_at']=t['started_at'] or now()
     marker={'task_index':index,'role':'candidate','call_index':state['calls_attempted'],'prompt_sha256':digest(messages),'started_at':now()}
     if state.get('in_flight') is None:state['in_flight']={}
     state['in_flight'][str(marker['call_index'])]=marker
     save(out/f"candidate-request-{marker['call_index']:03}.json",messages);persist(out,state)
     pending[pool.submit(call,variant,messages)]=(out,state,index,t,marker)
    if not pending:break
    done,_=wait(pending,return_when=FIRST_COMPLETED)
    for future in done:
     out,state,index,t,marker=pending.pop(future)
     try:result=future.result()
     except Exception as exc:result={'execution_status':'runner_error','error_type':type(exc).__name__,'output':None,'cost_usd':None,'usage':None,'latency_s':None}
     result.update(marker);save(out/f"candidate-response-{marker['call_index']:03}.json",result)
     del state['in_flight'][str(marker['call_index'])]
     if not state['in_flight']:state['in_flight']=None
     t['model_calls']+=1;t['calls'].append(result)
     if result['execution_status']!='completed':t['status']=result['execution_status']
     else:
      t['messages'].append({'role':'assistant','content':json.dumps(result['output'],ensure_ascii=False)})
      try:
       request=action(t,result['output'])
       if request:
        request.update(request_id=f"t{index:03}-s{t['model_calls']:02}",task_index=index,created_at=now());t['pending']=request
      except (ValueError,TypeError) as exc:t.update(status='invalid_output',validation_errors=[str(exc)])
     if t['status']!='active':t['completed_at']=now()
     persist(out,state)
     print(json.dumps({'shard':out.name,'case':t['case_id'],'arm':t['system'],'status':t['status'],'action':t.get('pending',{}).get('action')}),flush=True)
     if result.get('http_status') in (401,403,404,429) or result['execution_status'] in ('transport_error','runner_error'):stop=True
  for out,state in runs:branch(state);persist(out,state)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--workers',type=int,default=12);p.add_argument('--live',action='store_true');p.add_argument('--shell-keys',default=str(Path.home()/'.zshrc'));a=p.parse_args()
 try:advance(a)
 except (ValueError,OSError,KeyError,TypeError) as exc:p.exit(2,f'Error: {exc}\n')
