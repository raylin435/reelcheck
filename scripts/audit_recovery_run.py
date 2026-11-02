"""Read-only integrity audit of recorded recovery runs; never calls a model."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reelcheck.contract import validate
from run_recovery import verify,consensus


def audit(root):
    s=json.loads((root/'state.json').read_text());verify(s)
    assert s['in_flight'] is None and json.loads((root/'pending.json').read_text())==[]
    assert s['branches_created'] and all(t['status']!='active' for t in s['tasks'])
    initial={(t['case_id'],t['model_role']):t for t in s['tasks'] if t['phase']=='initial'}
    unique_calls={}; unique_tools={}; checked=0
    for t in s['tasks']:
        assert set(t['claim'])=={'claim_text','as_of'}
        for c in t['calls']:
            index=c['call_index']
            if index in unique_calls:assert unique_calls[index]==c
            unique_calls[index]=c
        for e in t['tools']:
            rid=e['request']['request_id']
            if rid in unique_tools:assert unique_tools[rid]==e
            unique_tools[rid]=e
        for key,limit in [('model_calls','max_model_calls'),('searches','max_searches'),('reads','max_reads')]:
            assert t[key]<=t['limits'][limit],(t['case_id'],key)
        if t['phase']!='recovery':continue
        old=initial[t['case_id'],t['model_role']]
        n=len(old['calls']);m=len(old['tools']);k=len(old['messages'])
        assert t['calls'][:n]==old['calls'] and t['tools'][:m]==old['tools']
        assert t['messages'][1:k]==old['messages'][1:]
        assert t['draft']==(old.get('output') or old.get('last_answer'))
        assert t['shared_call_indices']==[c['call_index'] for c in old['calls']]
        assert t['limits']['max_searches']-old['searches']==1
        assert t['limits']['max_reads']-old['reads']==2
        assert t['limits']['max_model_calls']-old['model_calls']==5
        if t['status']=='completed':
            assert not validate(t['output'],{**t['claim'],'evidence':t['evidence']})
            assert len(t.get('judge_votes',{}))==2
        checked+=1
    files=sorted(root.glob('candidate-response-*.json'))
    assert len(files)==len(unique_calls)==s['calls_attempted']
    for f in files:
        row=json.loads(f.read_text());assert unique_calls[row['call_index']]==row
    return {'run':str(root),'final_attempts':checked,'unique_candidate_calls':len(unique_calls),
            'unique_web_actions':dict(Counter(e['request']['action'] for e in unique_tools.values())),
            'checks':'frozen source hashes, terminal state, exact shared history/draft, equal remaining allowances, call journals, quote validity, two assessment attempts, claim-only input',
            'passed':True}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);args=p.parse_args()
    root=Path(args.run);dirs=sorted(root.glob('shard-*')) if not (root/'state.json').exists() else [root]
    if not dirs:raise ValueError('No runs')
    rows=[audit(d) for d in dirs]
    (root/'integrity-audit.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps(rows,indent=2))
