"""Shared-draft research comparison: ordinary retry versus targeted evidence recovery."""
import argparse
from copy import deepcopy
import fcntl
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reelcheck.research import initial_task,prompt,now,assess_research_judgment
from reelcheck.recovery import BASE_SYSTEM,recover_action,recovery_task,judge_messages_v2
from run_research import save,persist,keys,model_call,ingest,accounting
from run_model_matrix import validate_config
from recovery_batch import batch

INITIAL_LIMITS={'max_searches':1,'max_reads':2,'max_results':5,'max_page_chars':16000,'max_model_calls':5}


def init(args):
    out=Path(args.out)
    if out.exists() and any(out.iterdir()):raise ValueError('Fresh output directory required')
    config=json.loads(Path(args.config).read_text())
    validate_config({'variants':[config['cheap'],config['reference']]})
    cases=[json.loads(l) for l in Path(args.inputs).read_text().splitlines() if l.strip()]
    if not cases or len({c['case_id'] for c in cases})!=len(cases):raise ValueError('Nonempty unique cases required')
    gate=json.loads(Path(args.calibration).read_text())
    if not gate.get('gate_passed'):raise ValueError('Evaluator calibration gate has not passed')
    tasks=[]
    for n,case in enumerate(cases):
        for role in (['cheap','reference'] if n%2==0 else ['reference','cheap']):
            variant={**config[role],'id':role+'_draft'}
            t=initial_task(case,variant)
            t.update(phase='initial',model_role=role,limits=INITIAL_LIMITS.copy(),group_id=case.get('group_id',case['case_id']))
            t['messages'][0]['content']=BASE_SYSTEM
            tasks.append(t)
    out.mkdir(parents=True)
    snapshot=out/'source_snapshot';snapshot.mkdir()
    sources=[*sorted((ROOT/'reelcheck').glob('*.py')),
             *(ROOT/'scripts'/name for name in ['run_recovery.py','run_research.py','run_model_matrix.py','recovery_batch.py','research_web_worker.js']),ROOT/'RECOVERY_PROTOCOL.md']
    hashes={}
    for path in sources:
        relative=path.relative_to(ROOT);target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True)
        raw=path.read_bytes();target.write_bytes(raw);hashes[str(relative)]=hashlib.sha256(raw).hexdigest()
    save(snapshot/'config.json',config)
    save(snapshot/'claims.json',[{'case_id':c['case_id'],'group_id':c.get('group_id',c['case_id']),'claim_text':c['claim_text'],'as_of':c.get('as_of')} for c in cases])
    save(snapshot/'calibration.json',gate)
    state={'config':config,'tasks':tasks,'created_at':now(),'partition':args.partition,
           'candidate_reserved_usd':0.,'judge_reserved_usd':0.,'calls_attempted':0,
           'judge_calls_attempted':0,'in_flight':None,'source_hashes':hashes,
           'limits':INITIAL_LIMITS.copy(),'branches_created':False,'case_count':len(cases)}
    persist(out,state)
    print(json.dumps({'initialized':len(cases),'initial_tasks':len(tasks),'final_arms':3,'mode':'NO_API_CALLS'}))


def verify(state):
    for name,expected in state['source_hashes'].items():
        if name.startswith('reelcheck/') and name not in {'reelcheck/research.py','reelcheck/recovery.py','reelcheck/providers.py','reelcheck/contract.py','reelcheck/judge.py','reelcheck/__main__.py'}:continue
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:raise ValueError('Frozen code changed: '+name)


def branch(state):
    if state['branches_created'] or any(t['status']=='active' for t in state['tasks']):return
    branches=[]
    for t in state['tasks']:
        arms=['generic_retry','targeted_recovery'] if t['model_role']=='cheap' else ['strong_reference']
        for arm in arms:
            new=recovery_task(t,arm)
            if t['status'] in {'api_error','transport_error','runner_error','cost_budget_exhausted'}:
                new['status']=t['status']
            branches.append(new)
    state['tasks'].extend(branches);state['branches_created']=True


def advance(args,out,state):
    keys(args)
    for index,t in enumerate(state['tasks']):
        if t['status']!='active' or t.get('pending'):continue
        t['started_at']=t['started_at'] or now()
        if t['model_calls']>=t['limits']['max_model_calls']:
            t['status']='model_call_limit';persist(out,state);continue
        variant=state['config'][t['model_role']]
        result=model_call(out,state,index,variant,prompt(t,t['limits']),'candidate')
        if result is None:t['status']='cost_budget_exhausted'
        else:
            t['model_calls']+=1;t['calls'].append(result)
            if result['execution_status']!='completed':t['status']=result['execution_status']
            else:
                t['messages'].append({'role':'assistant','content':json.dumps(result['output'],ensure_ascii=False)})
                try:
                    request=recover_action(t,result['output'])
                    if request:
                        request.update(request_id=f"t{index:03}-s{t['model_calls']:02}",task_index=index,created_at=now())
                        t['pending']=request
                except ValueError as exc:t.update(status='invalid_output',validation_errors=[str(exc)])
        if t['status']!='active':t['completed_at']=now()
        persist(out,state)
        print(json.dumps({'case':t['case_id'],'arm':t['system'],'phase':t['phase'],'status':t['status'],
              'action':t.get('pending',{}).get('action')}),flush=True)
        if result and (result.get('http_status') in {401,403,404,429} or result['execution_status'] in {'transport_error','runner_error'}):return
    branch(state);persist(out,state)


def judge(args,out,state):
    keys(args)
    if not state['branches_created'] or any(t['status']=='active' for t in state['tasks']):raise ValueError('Candidates not finished')
    jobs=[]; bindings={}
    for index,t in enumerate(state['tasks']):
        if t['phase']!='recovery' or t['status']!='completed':continue
        for judge_id,config in state['config']['judges'].items():
            identifier=f'{index:03}/{judge_id}'
            jobs.append({'id':identifier,'config':config,'messages':judge_messages_v2(t)})
            bindings[identifier]=index
    rows=batch(jobs,out/'judges',state['config']['judge_cost_cap_usd'])
    for row in rows:
        t=state['tasks'][bindings[row['id']]]
        _,judge_id=row['id'].split('/')
        t.setdefault('judge_votes',{})[judge_id]={**row,**assess_research_judgment(t,row)}
    persist(out,state)


def consensus(t):
    if t['status']!='completed':return False
    votes=list(t.get('judge_votes',{}).values())
    if len(votes)!=2:return None
    values=[v['accepted'] for v in votes]
    return values[0] if values[0] is not None and values[0]==values[1] else None


def report(out,state):
    final=[t for t in state['tasks'] if t['phase']=='recovery']
    systems={}; pairs=[]
    for arm in ['generic_retry','targeted_recovery','strong_reference']:
        ts=[t for t in final if t['system']==arm];calls=[c for t in ts for c in t['calls']]
        accepted=sum(consensus(t) is True for t in ts)
        cost=accounting(calls)
        stats={'cases':len(ts),'accepted':accepted,'rejected':sum(consensus(t) is False for t in ts),
               'unresolved':sum(consensus(t) is None for t in ts),'objective_failures':sum(t['status']!='completed' for t in ts),
               'decisive_answers':sum((t['output'] or {}).get('verdict') in {'supported','contradicted'} for t in ts),
               'insufficient_answers':sum((t['output'] or {}).get('verdict')=='insufficient' for t in ts),
               'consensus_rejected_decisive':sum(consensus(t) is False and (t['output'] or {}).get('verdict') in {'supported','contradicted'} for t in ts),
               'accepted_insufficient':sum(consensus(t) is True and (t['output'] or {}).get('verdict')=='insufficient' for t in ts),
               'deployment_accounting':cost,'estimated_cost_per_accepted':cost['estimated_cost_usd']/accepted if accepted and cost['estimated_cost_usd'] is not None else None,
               'searches':sum(t['searches'] for t in ts),'reads':sum(t['reads'] for t in ts),
               'model_service_seconds':sum(c.get('latency_s') or 0 for c in calls)}
        systems[arm]=stats
    for case_id in sorted({t['case_id'] for t in final}):
        by={t['system']:t for t in final if t['case_id']==case_id}
        b,c=consensus(by['generic_retry']),consensus(by['targeted_recovery'])
        label='unresolved' if b is None or c is None else 'win' if c and not b else 'loss' if b and not c else 'tie'
        pairs.append({'case_id':case_id,'baseline':b,'targeted':c,'paired_outcome':label})
    unique={c['call_index']:c for t in state['tasks'] for c in t['calls']}
    judge_calls=[v for t in final for v in t.get('judge_votes',{}).values()]
    summary={'partition':state['partition'],'systems':systems,'pairs':pairs,
             'candidate_actual_billing':accounting(list(unique.values())),'judge_actual_billing':accounting(judge_calls),
             'web_tool_cost_usd':None,'human_verified_accuracy':None,
             'complete':bool(final) and all(t['status']!='active' for t in final),
             'all_valid_answers_judged':all(len(t.get('judge_votes',{}))==2 for t in final if t['status']=='completed')}
    save(out/'summary.json',summary)
    lines=['# Targeted evidence recovery comparison','',
      'Two machine judges; agreement is not human truth. Shared cheap drafts; equal tool and model-call ceilings.',
      'Open-model reference, not an organizer-certified proprietary frontier baseline.','',
      '| Case | Arm | Status | Verdict | Consensus acceptance |',
      '| --- | --- | --- | --- | --- |']
    for t in final:lines.append(f"| {t['case_id']} | {t['system']} | {t['status']} | {(t['output'] or {}).get('verdict','—')} | {consensus(t)} |")
    for t in final:
        lines.extend(['',f"## {t['case_id']} / {t['system']}",'',t['claim']['claim_text'],
                      '',f"Draft: {json.dumps(t['draft'],ensure_ascii=False)}",'',f"Final: {json.dumps(t['output'],ensure_ascii=False)}"])
        for g in t.get('recovery_gaps',[]):lines.append('Gap: '+g['gap']+'; query: '+g['query'])
        for e in t['tools']:
            r=e['request'];lines.append(f"- {r['action']}: {r.get('query',r.get('url'))} — {e['observation']['status']}")
        for name,v in t.get('judge_votes',{}).items():lines.append(f"- Judge {name}: accepted={v['accepted']}; "+str((v.get('output') or {}).get('rationale',v.get('errors'))))
        if t.get('validation_errors'):lines.append('Objective failure: '+'; '.join(t['validation_errors']))
    lines.extend(['','## Summary','', '```json',json.dumps(summary,indent=2),'```'])
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['init','advance','ingest','judge','report'])
    p.add_argument('--out',required=True);p.add_argument('--config',default='config.recovery.json');p.add_argument('--inputs')
    p.add_argument('--calibration',default='results/recovery-judge-calibration-01/calibration.json')
    p.add_argument('--partition',choices=['development','fresh_evaluation'],default='development')
    p.add_argument('--response');p.add_argument('--live',action='store_true');p.add_argument('--shell-keys',default=str(Path.home()/'.zshrc'))
    args=p.parse_args()
    try:
        if args.command=='init':init(args);return
        out=Path(args.out)
        with (out/'runner.lock').open('w') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            state=json.loads((out/'state.json').read_text())
            if state.get('in_flight'):raise ValueError('Interrupted API call; inspect journal before recovery, no retry')
            if args.command in {'advance','judge'}:verify(state)
            if args.command=='advance':advance(args,out,state)
            elif args.command=='ingest':ingest(args,out,state)
            elif args.command=='judge':judge(args,out,state)
            else:report(out,state)
    except (ValueError,OSError,KeyError,TypeError) as exc:p.exit(2,f'Error: {exc}\n')


if __name__=='__main__':main()
