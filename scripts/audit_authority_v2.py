"""Read-only integrity audit for the authority development experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reelcheck.contract import validate
from reelcheck.authority_v2 import render

def audit(out):
    out=Path(out);s=json.loads((out/'state.json').read_text());errors=[]
    if s.get('in_flight') or any(t.get('pending') or t['status']=='active' for t in s['tasks']):errors.append('unfinished candidate tasks')
    for name,h in s['source_hashes'].items():
        p=out/'source_snapshot'/name
        if hashlib.sha256(p.read_bytes()).hexdigest()!=h:errors.append('snapshot hash: '+name)
    if s.get('concurrent_executor_sha256'):
        executor=out/'source_snapshot/scripts/advance_authority_concurrent.py'
        addendum=json.loads((out/'concurrency-addendum.json').read_text())
        if hashlib.sha256(executor.read_bytes()).hexdigest()!=s['concurrent_executor_sha256']:errors.append('concurrent executor snapshot hash')
        if addendum['executor_sha256']!=s['concurrent_executor_sha256']:errors.append('concurrency addendum hash')
    source=json.loads((out/'source_snapshot/data/authority_v2/manifest.json').read_text())
    if s['partition'] not in ('development','heldout'):errors.append('unknown partition')
    dev={json.loads(l)['case_id'] for l in (out/('source_snapshot/data/authority_v2/'+s['partition']+'.jsonl')).read_text().splitlines()}
    if not set(s['selected_case_ids'])<=dev:errors.append('holdout used')
    by={}
    for t in s['tasks']:by.setdefault(t['case_id'],{})[t['system']]=t
    for cid,arms in by.items():
        initial=arms['cheap_draft']
        for name in (('ordinary_retry','authority_recovery','metadata_only') if s['partition']=='development' else ('ordinary_retry','authority_recovery')):
            if name not in arms:errors.append(cid+' missing '+name);continue
            t=arms[name]
            if t['draft']!=(initial.get('output') or initial.get('last_answer')):errors.append(cid+' unequal draft')
            if t['shared_call_indices']!=[c['call_index'] for c in initial['calls']]:errors.append(cid+' unequal initial calls')
            if t['calls'][:len(initial['calls'])]!=initial['calls']:errors.append(cid+' initial calls changed')
            if t['tools'][:len(initial['tools'])]!=initial['tools']:errors.append(cid+' initial observations changed')
            if t['evidence'][:len(initial['evidence'])]!=initial['evidence']:errors.append(cid+' initial evidence changed')
            for counter,cap,extra in [('model_calls','max_model_calls',5),('searches','max_searches',1),('reads','max_reads',2)]:
                if t['limits'][cap]!=initial[counter]+extra or t[counter]>t['limits'][cap]:errors.append(cid+' unequal/exceeded allowance')
        for t in arms.values():
            for event in t.get('rendering_events',[]):
                try:
                    if render(t,event['selected'])!=event['rendered']:errors.append(cid+' renderer changed selected evidence')
                except (ValueError,TypeError):errors.append(cid+' invalid renderer event')
            if set(t['claim'])!={'claim_text','as_of'}:errors.append(cid+' unexpected public claim fields')
            if t['status']=='completed' and t['phase']!='diagnostic':
                errors += [cid+': '+e for e in validate(t['output'],{**t['claim'],'evidence':t['evidence']})]
    calls={}
    for t in s['tasks']:
        for c in t['calls']:
            idx=c['call_index']
            if idx in calls and calls[idx]!=c:errors.append('conflicting call '+str(idx))
            calls[idx]=c
    journal=list(out.glob('candidate-response-*.json'))
    if len(calls)!=len(journal) or len(calls)!=s['calls_attempted']:errors.append('call journal count mismatch')
    for c in calls.values():
        if json.loads((out/f"candidate-response-{c['call_index']:03}.json").read_text())!=c:errors.append('journal mismatch')
    result={'passed':not errors,'errors':errors,'cases':len(by),'candidate_calls':len(calls),'heldout_used':s['partition']=='heldout','human_verified_accuracy':None}
    (out/'integrity-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True)
    result=audit(p.parse_args().out);print(json.dumps(result,indent=2));sys.exit(0 if result['passed'] else 1)
