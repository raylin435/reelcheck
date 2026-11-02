"""Publish small canary traces without full-page caches or API request journals."""
import argparse
import json
from pathlib import Path
import shutil

def export(run,out):
    run=Path(run);out=Path(out)
    if out.exists() and any(out.iterdir()):raise ValueError('Fresh release directory required')
    state=json.loads((run/'state.json').read_text())
    if state.get('in_flight') or any(t['status']=='active' or t.get('pending') for t in state['tasks']):raise ValueError('Finish the run before exporting')
    out.mkdir(parents=True,exist_ok=True)
    for name in ('summary.json','integrity-audit.json','reference_review_summary.json'):
        shutil.copy2(run/name,out/name)
    for folder in ('reference_review','grounding_judges'):
        if (run/folder/'completion.json').exists():shutil.copy2(run/folder/'completion.json',out/(folder+'-completion.json'))
    traces=[]
    for t in state['tasks']:
        traces.append({k:t.get(k) for k in ('case_id','system','phase','claim','status','limits','searches','reads','model_calls','draft','draft_status','output','validation_errors','metadata_audits','recovery_gaps','shared_call_indices','judge_votes')})
        traces[-1]['opened_sources']=[{k:e[k] for k in ('id','url','resolved_url','title','sha256','retrieved_date') if k in e} for e in t['evidence']]
        traces[-1]['tool_actions']=[{'request':e['request'],'status':e['observation']['status'],'raw_sha256':e['raw_sha256']} for e in t['tools']]
        traces[-1]['call_journal']=[{k:c.get(k) for k in ('call_index','execution_status','cost_usd','usage','latency_s','prompt_sha256')} for c in t['calls']]
    (out/'traces.json').write_text(json.dumps(traces,ensure_ascii=False,indent=2)+'\n')
    (out/'source_hashes.json').write_text(json.dumps(state['source_hashes'],indent=2)+'\n')
    (out/'config.json').write_text(json.dumps(state['config'],indent=2)+'\n')
    (out/'README.md').write_text('''# Authority development canary — recorded results\n\nFour development cases; no held-out candidate inference. Five arms include a memory-only diagnostic and a metadata-only ablation. Reference-label matching is provisional; grounding is separately assessed by two models. No human-verified accuracy or aggregate harness advantage is established.\n\n`summary.json` retains failures and unresolved outcomes. `traces.json` preserves all initial and final attempts, exact metadata checks, selected tool actions, source URLs/hashes, and judgments. Full page text, raw web caches and API request bodies stay local. `source_hashes.json` pins the executed sources; `config.json` records models and token rates. Assessment completion files report actual known cost separately from candidate cost. Web billing is unavailable.\n''')
    print(out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();export(a.run,a.out)
