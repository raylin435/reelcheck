"""Two-worker paid batch for independent assessments, with persisted reservations."""
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reelcheck.__main__ import upper_cost, digest
from reelcheck.providers import call
from run_research import save


def batch(tasks,out,max_cost):
    out=Path(out)
    out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Fresh batch directory required')
    save(out/'requests.json',tasks)
    reserved=0.; rows=[]; next_task=0; pending={}; attempted=[]; stop=False
    with ThreadPoolExecutor(max_workers=2) as pool:
        while pending or (next_task<len(tasks) and not stop):
            while len(pending)<2 and next_task<len(tasks) and not stop:
                task=tasks[next_task];bound=upper_cost(task['config'],task['messages'])
                if reserved+bound>max_cost:stop=True;break
                reserved+=bound; index=next_task; next_task+=1
                attempted.append({'index':index,'id':task['id'],'prompt_sha256':digest(task['messages'])})
                save(out/'attempts.json',{'attempts':attempted,'reserved_usd':reserved})
                pending[pool.submit(call,task['config'],task['messages'])]=(index,task)
            if not pending:break
            done,_=wait(pending,return_when=FIRST_COMPLETED)
            for future in done:
                index,task=pending.pop(future)
                try: result=future.result()
                except Exception as exc:result={'execution_status':'runner_error','cost_usd':None,'error_type':type(exc).__name__,'output':None}
                row={'id':task['id'],'index':index,**result}
                rows.append(row);save(out/f'response-{index:03}.json',row)
                save(out/'results.json',sorted(rows,key=lambda r:r['index']))
                print(task['id'],result['execution_status'],flush=True)
                if result.get('http_status') in {401,403,404,429} or result['execution_status'] in {'transport_error','runner_error'}:stop=True
    costs=[r.get('cost_usd') for r in rows]
    save(out/'completion.json',{'planned':len(tasks),'attempted':len(attempted),'saved':len(rows),
        'complete':len(rows)==len(tasks),'reserved_usd':reserved,
        'estimated_cost_usd':sum(costs) if all(c is not None for c in costs) else None,
        'known_subtotal_usd':sum(c for c in costs if c is not None),
        'unknown_cost_calls':sum(c is None for c in costs)})
    return sorted(rows,key=lambda r:r['index'])
