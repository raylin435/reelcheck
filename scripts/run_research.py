"""Resumable model-led research. init is free; advance/judge require --live.

The web worker reads pending.json, executes exact search/read requests, writes raw
responses, then calls ingest. See RESEARCH.md for the worker contract.
"""
import argparse
from collections import Counter
from datetime import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.__main__ import digest, upper_cost
from reelcheck.providers import call, load_env, load_shell_exports
from reelcheck.research import (LIMITS, apply_action, assess_research_judgment,
    initial_task, ingest_tool, now, prompt, research_judge_messages)
from run_model_matrix import validate_config


def save(path, value):
    tmp = path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w') as file:
        json.dump(value, file, ensure_ascii=False, indent=2)
        file.write('\n')
        file.flush()
        os.fsync(file.fileno())
    tmp.replace(path)


def persist(out, state):
    save(out/'state.json', state)
    save(out/'pending.json', [t['pending'] for t in state['tasks'] if t.get('pending')])


def init(args):
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Use a fresh output directory')
    config = json.loads(Path(args.config).read_text())
    variants = validate_config(config)
    cases = [json.loads(line) for line in Path(args.inputs).read_text().splitlines() if line.strip()]
    if not cases or len({c['case_id'] for c in cases}) != len(cases):
        raise ValueError('Need nonempty cases with unique IDs')
    tasks = []
    for index, case in enumerate(cases):
        for variant in variants if index % 2 == 0 else reversed(variants):
            tasks.append(initial_task(case, variant))
    for key, maximum in [('candidate_cost_cap_usd', 10), ('judge_cost_cap_usd', 10)]:
        value = config.get(key)
        if not isinstance(value, (int,float)) or not math.isfinite(value) or not 0 < value <= maximum:
            raise ValueError('Invalid cost cap: '+key)
    out.mkdir(parents=True, exist_ok=True)
    state = {'created_at':now(), 'config':config, 'limits':LIMITS.copy(), 'tasks':tasks,
             'candidate_reserved_usd':0., 'judge_reserved_usd':0., 'calls_attempted':0,
             'judge_calls_attempted':0, 'in_flight':None, 'protocol_sha256':hashlib.sha256(
                 (ROOT/'RESEARCH_PROTOCOL.md').read_bytes()).hexdigest()}
    snapshot=out/'source_snapshot'
    snapshot.mkdir()
    for path in [*sorted((ROOT/'reelcheck').glob('*.py')), Path(__file__).resolve(),
                 ROOT/'scripts/run_model_matrix.py', ROOT/'scripts/research_web_worker.js',
                 ROOT/'RESEARCH_PROTOCOL.md']:
        dest=snapshot/path.relative_to(ROOT)
        dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_bytes(path.read_bytes())
    save(snapshot/'config.json', config)
    # Store only whitelisted claims here; curated packets never enter this runner.
    save(snapshot/'claims.json', [{'case_id':t['case_id'],**t['claim']} for t in tasks[::len(variants)]])
    state['source_hashes']={str(p.relative_to(snapshot)):hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in snapshot.rglob('*') if p.is_file()}
    persist(out,state)
    print(json.dumps({'tasks':len(tasks),'status':'initialized_NO_API_CALLS','out':str(out)}))


def keys(args):
    if not args.live:
        raise ValueError('Paid API requests require --live')
    load_env(ROOT/'.env')
    load_env(ROOT.parent/'.env')
    if args.shell_keys:
        load_shell_exports(args.shell_keys)
    if not os.environ.get('FIREWORKS_API_KEY'):
        raise ValueError('FIREWORKS_API_KEY unavailable')


def verify_code(state):
    """Never silently continue inference under different code than the manifest."""
    relevant={'reelcheck/research.py','reelcheck/providers.py','reelcheck/contract.py',
              'reelcheck/judge.py','reelcheck/__main__.py','scripts/run_research.py',
              'scripts/research_web_worker.js','RESEARCH_PROTOCOL.md'}
    for name,expected in state['source_hashes'].items():
        if name in relevant and hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('Run code changed: '+name+'; use its source snapshot or start a fresh run')


def model_call(out, state, index, variant, messages, role):
    bound = upper_cost(variant, messages)
    reserve = role+'_reserved_usd'
    if state[reserve]+bound > state['config'][role+'_cost_cap_usd']:
        return None
    state[reserve] += bound
    counter = 'calls_attempted' if role == 'candidate' else 'judge_calls_attempted'
    state[counter] += 1
    state['in_flight']={'task_index':index,'role':role,'call_index':state[counter],
                        'prompt_sha256':digest(messages),'started_at':now()}
    persist(out,state)  # Reserve before network. Never silently repeat interrupted requests.
    save(out/f"{role}-request-{state[counter]:03}.json", messages)
    try:
        result=call(variant,messages)
    except Exception as exc:
        result={'execution_status':'runner_error','error_type':type(exc).__name__,
                'output':None,'cost_usd':None,'usage':None,'latency_s':None}
    result.update(state['in_flight'])
    save(out/f"{role}-response-{state[counter]:03}.json",result)
    state['in_flight']=None
    return result


def advance(args,out,state):
    keys(args)
    variants={v['id']:v for v in state['config']['variants']}
    for index,task in enumerate(state['tasks']):
        if task['status']!='active' or task.get('pending'):
            continue
        if task['model_calls'] >= state['limits']['max_model_calls']:
            task['status']='model_call_limit'
            persist(out,state)
            continue
        task['started_at']=task['started_at'] or now()
        result=model_call(out,state,index,variants[task['system']],prompt(task,state['limits']),'candidate')
        if result is None:
            task['status']='cost_budget_exhausted'
        else:
            task['model_calls']+=1
            task['calls'].append(result)
            if result['execution_status']!='completed':
                task['status']=result['execution_status']
            else:
                task['messages'].append({'role':'assistant','content':json.dumps(result['output'],ensure_ascii=False)})
                try:
                    request=apply_action(task,result['output'],state['limits'])
                    if request:
                        request.update(request_id=f"t{index:03}-s{task['model_calls']:02}",
                                       task_index=index,created_at=now())
                        task['pending']=request
                except ValueError as exc:
                    task.update(status='invalid_output',validation_errors=[str(exc)])
        persist(out,state)
        print(json.dumps({'case':task['case_id'],'system':task['system'],'status':task['status'],
              'action':task.get('pending',{}).get('action'),'call':task['model_calls']}),flush=True)
        if result and (result.get('http_status') in {401,403,404,429} or result['execution_status'] in {'transport_error','runner_error'}):
            break


def ingest(args,out,state):
    response=json.loads(Path(args.response).read_text())
    matching=[t for t in state['tasks'] if t.get('pending',{}).get('request_id')==response.get('request_id')]
    if len(matching)!=1:
        raise ValueError('Response must match exactly one pending request; duplicate/stale response rejected')
    task=matching[0]
    request=task['pending']
    ingest_tool(task,request,response,state['limits'])
    save(out/(request['request_id']+'-web.json'),response)
    del task['pending']
    persist(out,state)
    print(json.dumps({'ingested':request['request_id'],'status':task['tools'][-1]['observation']['status']}))


def judge(args,out,state):
    keys(args)
    if any(t['status']=='active' or t.get('pending') for t in state['tasks']):
        raise ValueError('Finish candidate tasks before judging')
    for index,task in enumerate(state['tasks']):
        if task.get('judgment') or task['status']!='completed':
            continue
        result=model_call(out,state,index,state['config']['judge'],research_judge_messages(task),'judge')
        if result is None:
            break
        task['judgment']={**result,**assess_research_judgment(task,result)}
        persist(out,state)
        print(json.dumps({'case':task['case_id'],'system':task['system'],
                          'judge_accepted':task['judgment']['accepted']}),flush=True)
        if result.get('http_status') in {401,403,404,429} or result['execution_status'] in {'transport_error','runner_error'}:
            break


def accounting(calls):
    known=[c['cost_usd'] for c in calls if c.get('cost_usd') is not None]
    return {'calls':len(calls),'known_cost_subtotal_usd':sum(known),
            'estimated_cost_usd':sum(known) if len(known)==len(calls) else None,
            'unknown_cost_calls':len(calls)-len(known)}


def report(out,state):
    tasks=state['tasks']
    systems={}
    for variant in state['config']['variants']:
        part=[t for t in tasks if t['system']==variant['id']]
        systems[variant['id']]={'cases':len(part),'statuses':dict(Counter(t['status'] for t in part)),
            'machine_accepted':sum(t.get('judgment',{}).get('accepted') is True for t in part),
            'machine_rejected':sum(t['status'] not in {'active','completed'} or t.get('judgment',{}).get('accepted') is False for t in part),
            'unresolved':sum(t['status'] in {'active','completed'} and t.get('judgment',{}).get('accepted') is None for t in part),
            'searches':sum(t['searches'] for t in part),'reads':sum(t['reads'] for t in part),
            'successful_reads':sum(len(t['evidence']) for t in part),
            'candidate_accounting':accounting([c for t in part for c in t['calls']])}
    summary={'systems':systems,'candidate_accounting':accounting([c for t in tasks for c in t['calls']]),
       'judge_accounting':accounting([t['judgment'] for t in tasks if t.get('judgment')]),
       'web_tool_cost_usd':None,'human_verified_accuracy':None,
       'complete':all(t['status']!='active' for t in tasks),
       'all_completed_answers_judged':all(t.get('judgment') for t in tasks if t['status']=='completed')}
    save(out/'summary.json',summary)
    lines=['# Model-led research pilot','',
       'Candidates chose their own queries and pages. No curated evidence or labels were provided.',
       'Machine judgments are fallible; these are development examples, not measured human accuracy.',
       'Web-tool cost is unknown. Model costs below are usage estimates. Wall time includes worker idle time.','',
       '| Case | Model | Status | Verdict | Searches / reads | Judge accepted |',
       '| --- | --- | --- | --- | --- | --- |']
    for t in tasks:
        lines.append(f"| {t['case_id']} | {t['system']} | {t['status']} | {(t['output'] or {}).get('verdict','—')} | {t['searches']} / {t['reads']} | {t.get('judgment',{}).get('accepted')} |")
    for t in tasks:
        lines.extend(['',f"## {t['case_id']} / {t['system']}",'',t['claim']['claim_text'],''])
        for event in t['tools']:
            req=event['request']
            lines.append(f"- {req['action']}: {req.get('query',req.get('url'))} — {event['observation']['status']}")
        for evidence in t['evidence']:
            lines.append(f"- Opened {evidence['id']}: [{evidence['title']}]({evidence['url']})")
        answer=t['output'] or {}
        if answer:
            lines.extend(['',f"Decision: **{answer['verdict']}**. {answer['explanation']}"])
            for cite in answer['citations']:
                lines.append(f"- {cite['passage_id']}: {cite['quote']}")
        if t.get('validation_errors'):
            lines.append('Validation failure: '+ '; '.join(t['validation_errors']))
        j=t.get('judgment',{})
        if j:
            lines.extend(['','Judge: '+str((j.get('output') or {}).get('rationale',j.get('errors')))])
        model_seconds=sum(c.get('latency_s') or 0 for c in t['calls'])
        tool_seconds=sum(e['latency_s'] for e in t['tools'])
        lines.extend(['',f"Model service: {model_seconds:.2f}s; web service: {tool_seconds:.2f}s."])
        if t.get('started_at') and t.get('completed_at'):
            wall=(datetime.fromisoformat(t['completed_at'])-datetime.fromisoformat(t['started_at'])).total_seconds()
            lines.append(f'Elapsed wall time including bridge idle time: {wall:.2f}s.')
    lines.extend(['','## Accounting','', '```json',json.dumps(summary,indent=2),'```'])
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['init','advance','ingest','judge','report'])
    p.add_argument('--out',required=True)
    p.add_argument('--config')
    p.add_argument('--inputs')
    p.add_argument('--response')
    p.add_argument('--live',action='store_true')
    p.add_argument('--shell-keys',default=str(Path.home()/'.zshrc'))
    args=p.parse_args()
    try:
        if args.command=='init':
            init(args)
            return
        out=Path(args.out)
        with (out/'runner.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            state=json.loads((out/'state.json').read_text())
            if state.get('in_flight'):
                raise ValueError('Prior API call was interrupted; inspect saved response before recovery. No automatic retry.')
            if args.command in {'advance','judge'}:
                verify_code(state)
            if args.command=='advance': advance(args,out,state)
            elif args.command=='ingest': ingest(args,out,state)
            elif args.command=='judge': judge(args,out,state)
            else: report(out,state)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        p.exit(2,f'Error: {exc}\n')


if __name__=='__main__': main()
