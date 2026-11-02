"""Aggregate frozen independent shards without colliding their local call indices."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from run_recovery import consensus
from run_research import accounting


ARMS = ('generic_retry', 'targeted_recovery', 'strong_reference')


def combine(states):
    finals=[]; unique={}; judgments=[]
    for shard,state in enumerate(states):
        if state.get('in_flight') or not state['branches_created']:
            raise ValueError('Unfinished shard')
        for task in state['tasks']:
            for call in task['calls']:
                key=(shard,call['call_index'])
                if key in unique and unique[key]!=call:raise ValueError('Conflicting shared call')
                unique[key]=call
            if task['phase']=='recovery':
                if task['status']=='active' or task.get('pending'):raise ValueError('Unfinished final task')
                finals.append(task)
                judgments.extend(task.get('judge_votes',{}).values())
    by_case=defaultdict(dict)
    for t in finals:
        if t['system'] in by_case[t['case_id']]:raise ValueError('Duplicate case/arm')
        by_case[t['case_id']][t['system']]=t
    if any(set(v)!=set(ARMS) for v in by_case.values()):raise ValueError('Missing arm')
    systems={}
    for arm in ARMS:
        ts=[t for t in finals if t['system']==arm]
        costs=accounting([c for t in ts for c in t['calls']])
        accepted=sum(consensus(t) is True for t in ts)
        systems[arm]={
            'cases':len(ts),'accepted':accepted,
            'rejected_including_execution_failures':sum(consensus(t) is False for t in ts),
            'unresolved':sum(consensus(t) is None for t in ts),
            'execution_statuses':dict(Counter(t['status'] for t in ts)),
            'objective_failures':sum(t['status']!='completed' for t in ts),
            'decisive_answers':sum((t['output'] or {}).get('verdict') in {'supported','contradicted'} for t in ts),
            'insufficient_answers':sum((t['output'] or {}).get('verdict')=='insufficient' for t in ts),
            'accepted_insufficient':sum(consensus(t) is True and (t['output'] or {}).get('verdict')=='insufficient' for t in ts),
            'consensus_rejected_decisive':sum(consensus(t) is False and (t['output'] or {}).get('verdict') in {'supported','contradicted'} for t in ts),
            'deployment_accounting':costs,
            'cost_per_accepted_usd':costs['estimated_cost_usd']/accepted if accepted and costs['estimated_cost_usd'] is not None else None,
            'searches':sum(t['searches'] for t in ts),'reads':sum(t['reads'] for t in ts),
            'model_service_seconds':sum(c.get('latency_s') or 0 for t in ts for c in t['calls'])}
    pairs=[]
    for cid,by in sorted(by_case.items()):
        b,t=by['generic_retry'],by['targeted_recovery'];bv,tv=consensus(b),consensus(t)
        outcome='unresolved' if bv is None or tv is None else 'win' if tv and not bv else 'loss' if bv and not tv else 'tie'
        pairs.append({'case_id':cid,'group_id':t['group_id'],'baseline':bv,'targeted':tv,
                      'baseline_status':b['status'],'targeted_status':t['status'],
                      'both_completed':b['status']==t['status']=='completed','outcome':outcome})
    groups={}
    for gid in sorted({p['group_id'] for p in pairs}):
        groups[gid]={a:sum(consensus(t) is True for t in finals if t['group_id']==gid and t['system']==a) for a in ARMS}
        groups[gid]['cases']=sum(p['group_id']==gid for p in pairs)
    return {'cases':len(by_case),'systems':systems,'paired_outcomes':dict(Counter(p['outcome'] for p in pairs)),
            'both_completed_paired_outcomes':dict(Counter(p['outcome'] for p in pairs if p['both_completed'])),
            'pairs':pairs,'groups':groups,'candidate_actual_billing':accounting(list(unique.values())),
            'judge_actual_billing':accounting(judgments),'web_cost_usd':None,'human_accuracy':None,
            'all_valid_answers_assessed_twice':all(len(t.get('judge_votes',{}))==2 for t in finals if t['status']=='completed')}, finals


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);args=p.parse_args()
    root=Path(args.run);manifest=json.loads((root/'manifest.json').read_text())
    for name,digest in manifest['sha256'].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen input changed: '+name)
    dirs=sorted(root.glob('shard-*'));states=[json.loads((d/'state.json').read_text()) for d in dirs]
    result,finals=combine(states)
    if result['cases']!=manifest['cases']:raise ValueError('Missing cases')
    (root/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    # Replay consumes tasks only; do not use this synthetic state for billing or inference.
    replay=root/'replay';replay.mkdir(exist_ok=True)
    (replay/'state.json').write_text(json.dumps({'tasks':finals,'replay_only':True},indent=2)+'\n')
    subprocess.run([sys.executable,'scripts/build_recovery_demo.py','--run',str(replay),'--out',str(root/'demo.html')],check=True)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
