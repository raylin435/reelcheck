"""Dated-authority canary, with hidden references and preserved shared drafts."""
import argparse
from collections import Counter
import fcntl
import hashlib
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.authority_v2 import new_task, fork_task, action, truth_score, INITIAL_LIMITS, ingest_tool
from reelcheck.research import prompt, now
from reelcheck.recovery import judge_messages_v2
from reelcheck.research import assess_research_judgment
from run_research import save, persist, keys, model_call, accounting
from run_model_matrix import validate_config
from recovery_batch import batch

DATA = ROOT/'data/authority_v2'
ARMS = ('no_search', 'ordinary_retry', 'authority_recovery', 'strong_reference', 'metadata_only')

def load_jsonl(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]

def dataset():
    manifest = json.loads((DATA/'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        if hashlib.sha256((DATA/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen dataset changed: '+name)
    return manifest

def init(args):
    dataset()
    if not 1 <= args.shards <= 20 or not 0 <= args.shard < args.shards:raise ValueError('Invalid shard configuration')
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Fresh output directory required')
    config = json.loads(Path(args.config).read_text())
    validate_config({'variants': [config['cheap'], config['reference']]})
    for role in ('candidate', 'judge'):
        cap = config.get(role+'_cost_cap_usd')
        if not isinstance(cap, (float, int)) or not 0 < cap <= 10:
            raise ValueError('Cost cap must be in (0, 10]')
    cases = load_jsonl(DATA/(args.partition+'.jsonl'))
    if args.partition=='heldout' and args.canary:raise ValueError('No held-out canary selection')
    cases = [c for i,c in enumerate(cases) if i % args.shards == args.shard]
    if not cases:raise ValueError('Empty shard')
    if args.canary:
        seen = set(); selected = []
        for c in cases:
            if c['category'] not in seen:
                selected.append(c); seen.add(c['category'])
        cases = selected
    tasks = []
    for n, case in enumerate(cases):
        tasks.append(new_task(case, 'cheap', diagnostic=True))
        for role in (('cheap', 'reference') if n%2 == 0 else ('reference', 'cheap')):
            tasks.append(new_task(case, role))
    out.mkdir(parents=True, exist_ok=True)
    files = [*sorted((ROOT/'reelcheck').glob('*.py')),
             *(ROOT/'scripts'/n for n in ('run_authority_v2.py','run_research.py','run_model_matrix.py','recovery_batch.py','authority_v2_web_worker.js')),
             ROOT/'AUTHORITY_V2_PROTOCOL.md', *sorted(DATA.glob('*'))]
    hashes = {}
    for path in files:
        if not path.is_file(): continue
        relative = path.relative_to(ROOT); target = out/'source_snapshot'/relative
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(path.read_bytes())
        hashes[str(relative)] = hashlib.sha256(path.read_bytes()).hexdigest()
    save(out/'source_snapshot/config.json', config)
    state = dict(config=config, tasks=tasks, created_at=now(), partition=args.partition, shard=args.shard, shards=args.shards,
                 source_hashes=hashes, limits=INITIAL_LIMITS.copy(), candidate_reserved_usd=0., judge_reserved_usd=0., calls_attempted=0,
                 judge_calls_attempted=0, in_flight=None, branches_created=False, selected_case_ids=[c['case_id'] for c in cases])
    persist(out,state)
    print(json.dumps({'mode':'NO_API_CALLS', 'cases':state['selected_case_ids'], 'arms':ARMS}))

def verify(state):
    for name, expected in state['source_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Frozen run source changed: '+name)

def branch(state):
    if state['branches_created'] or any(t['status']=='active' for t in state['tasks']): return
    branches = []
    for t in state['tasks']:
        if t['phase'] != 'initial': continue
        arms = ('ordinary_retry','authority_recovery','metadata_only') if t['model_role']=='cheap' else ('strong_reference',)
        if state['partition']=='heldout':arms=tuple(a for a in arms if a!='metadata_only')
        if t['model_role']=='cheap':
            shift=sum(t['case_id'].encode()) % len(arms);arms=arms[shift:]+arms[:shift]
        for arm in arms:
            new = fork_task(t,arm)
            if t['status'] in ('api_error','transport_error','runner_error','cost_budget_exhausted'):
                new['status'] = t['status']
            branches.append(new)
    state['tasks'].extend(branches); state['branches_created']=True

def advance(args,out,state):
    keys(args)
    for index,t in enumerate(state['tasks']):
        if t['status'] != 'active' or t.get('pending'): continue
        if t['model_calls'] >= t['limits']['max_model_calls']:
            t['status']='model_call_limit';persist(out,state);continue
        t['started_at'] = t['started_at'] or now()
        result = model_call(out,state,index,state['config'][t['model_role']],prompt(t,t['limits']),'candidate')
        if result is None: t['status']='cost_budget_exhausted'
        else:
            t['model_calls'] += 1; t['calls'].append(result)
            if result['execution_status'] != 'completed': t['status']=result['execution_status']
            else:
                t['messages'].append({'role':'assistant','content':json.dumps(result['output'],ensure_ascii=False)})
                try:
                    request = action(t,result['output'])
                    if request:
                        request.update(request_id=f"t{index:03}-s{t['model_calls']:02}",task_index=index,created_at=now())
                        t['pending']=request
                except (ValueError,TypeError) as exc:
                    t.update(status='invalid_output',validation_errors=[str(exc)])
        if t['status'] != 'active': t['completed_at']=now()
        persist(out,state)
        print(json.dumps({'case':t['case_id'],'arm':t['system'],'status':t['status'],'action':t.get('pending',{}).get('action')}),flush=True)
        if result and (result.get('http_status') in (401,403,404,429) or result['execution_status'] in ('transport_error','runner_error')):return
    branch(state);persist(out,state)


def ingest(args,out,state):
    response=json.loads(Path(args.response).read_text())
    matches=[t for t in state['tasks'] if t.get('pending',{}).get('request_id')==response.get('request_id')]
    if len(matches)!=1:raise ValueError('Response must match one pending request')
    task=matches[0];request=task['pending']
    ingest_tool(task,request,response,task['limits'])
    save(out/(request['request_id']+'-web.json'),response)
    del task['pending'];persist(out,state)
    print(json.dumps({'ingested':request['request_id'],'status':task['tools'][-1]['observation']['status']}))

def judge(args,out,state):
    keys(args)
    if not state['branches_created'] or any(t['status']=='active' for t in state['tasks']):raise ValueError('Candidates not finished')
    jobs=[]; bindings={}
    for i,t in enumerate(state['tasks']):
        if t['phase']!='recovery' or t['status']!='completed':continue
        for jid,config in state['config']['judges'].items():
            ident=f'{i:03}/{jid}'
            jobs.append({'id':ident,'config':config,'messages':judge_messages_v2(t)})
            bindings[ident]=i
    rows=batch(jobs,out/'grounding_judges',state['config']['judge_cost_cap_usd'])
    for row in rows:
        t=state['tasks'][bindings[row['id']]]
        t.setdefault('judge_votes',{})[row['id'].split('/')[1]]={**row,**assess_research_judgment(t,row)}
    persist(out,state)

def report(out,state):
    # Read frozen references only after inference, never as candidate context.
    refs={r['case_id']:r for r in load_jsonl(out/'source_snapshot/data/authority_v2/references.jsonl')}
    final=[t for t in state['tasks'] if t['phase'] in ('diagnostic','recovery')]
    rows=[]
    for t in final:
        votes=[v.get('accepted') for v in t.get('judge_votes',{}).values()]
        score=truth_score(t,refs[t['case_id']])
        score['grounding']=votes[0] if len(votes)==2 and votes[0] is not None and votes[0]==votes[1] else None
        audit=(t['metadata_audits'] or [{}])[-1]
        rows.append({'case_id':t['case_id'],'arm':t['system'],'status':t['status'],'verdict':(t['output'] or {}).get('verdict'),
                     **score,'metadata_errors':audit.get('errors'), 'explanation':(t['output'] or {}).get('explanation'),
                     'searches':t['searches'],'reads':t['reads'],'cost':accounting(t['calls'])})
    systems={}
    for arm in ARMS:
        selected=[r for r in rows if r['arm']==arm]
        systems[arm]={'cases':len(selected),**{key:sum(r[key] is True for r in selected) for key in ('completed','reference_label_match','wrong_decisive','operational_abstention','grounding')},
                      'grounding_unresolved':sum(r['grounding'] is None for r in selected),
                      'metadata_pass':sum(r['completed'] and r['metadata_errors']==[] for r in selected),
                      'reference_unresolved':sum(r['reference_label_match'] is None for r in selected),
                      'grounding_completed_unresolved':sum(r['completed'] and r['arm']!='no_search' and r['grounding'] is None for r in selected)}
    unique={c['call_index']:c for t in state['tasks'] for c in t['calls']}
    result={'partition':state['partition'],'complete':state['branches_created'] and all(t['status']!='active' for t in state['tasks']),
            'human_verified_accuracy':None,'reference_status':'blind machine-reviewed; not human-verified','systems':systems,'rows':rows,
            'candidate_billing':accounting(list(unique.values())), 'web_cost_usd':None,
            'heldout_used':state['partition']=='heldout','shard':state['shard']}
    save(out/'summary.json',result);print(json.dumps(result,indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['init','advance','ingest','judge','report'])
    p.add_argument('--out',required=True);p.add_argument('--config',default='config.authority_v2.json')
    p.add_argument('--canary',action='store_true');p.add_argument('--response')
    p.add_argument('--partition',choices=['development','heldout'],default='development')
    p.add_argument('--shard',type=int,default=0);p.add_argument('--shards',type=int,default=1)
    p.add_argument('--live',action='store_true');p.add_argument('--shell-keys',default=str(Path.home()/'.zshrc'))
    args=p.parse_args()
    try:
        if args.command=='init':init(args);return
        out=Path(args.out)
        with (out/'runner.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            state=json.loads((out/'state.json').read_text())
            if state.get('in_flight'):raise ValueError('Interrupted request: inspect journal, do not silently retry')
            if args.command in ('advance','review','judge'):verify(state)
            if args.command=='advance':advance(args,out,state)
            elif args.command=='ingest':ingest(args,out,state)
            elif args.command=='judge':judge(args,out,state)
            else:report(out,state)
    except (ValueError,OSError,KeyError,TypeError) as exc:p.exit(2,f'Error: {exc}\n')

if __name__=='__main__':main()
