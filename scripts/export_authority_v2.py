"""Export partition results and selected evidence, excluding raw full-page caches."""
import argparse,json,shutil
from pathlib import Path

def export(root,out):
 root=Path(root);out=Path(out)
 summary=json.loads((root/'summary.json').read_text())
 if not summary['complete'] or not summary['all_valid_researched_answers_judged']:raise ValueError('Incomplete partition')
 if out.exists():raise ValueError('Never overwrite a release')
 out.mkdir(parents=True);shutil.copy2(root/'summary.json',out/'summary.json')
 traces=[];sources={};config=None;initial_reuse=[];execution_addenda=[]
 for p in sorted(root.glob('shard-*')):
  if not p.is_dir():continue
  state=json.loads((p/'state.json').read_text());config=state['config'];sources=state['source_hashes']
  if state.get('concurrent_executor_sha256'):
   execution_addenda.append({'shard':p.name,**json.loads((p/'concurrency-addendum.json').read_text())})
   shutil.copy2(p/'source_snapshot/scripts/advance_authority_concurrent.py',out/'advance_authority_concurrent.py')
  if state.get('initial_reuse'):
   origin=dict(state['initial_reuse']);parent=Path(origin['parent']);origin['parent']=str(Path('results')/parent.parent.name/parent.name)
   initial_reuse.append({'shard':p.name,'inherited_call_indices':state['inherited_call_indices'],**origin})
  if state['in_flight'] or any(t['status']=='active' or t.get('pending') for t in state['tasks']):raise ValueError('Unfinished tasks')
  for t in state['tasks']:
   trace={'shard':p.name,**{k:t.get(k) for k in ('case_id','system','phase','claim','status','limits','searches','reads','model_calls','draft','draft_status','output','validation_errors','metadata_audits','recovery_gaps','shared_call_indices','judge_votes','rendering_events')}}
   trace['opened_sources']=[{k:e[k] for k in ('id','url','resolved_url','title','sha256','reader_page_sha256','retrieved_date','rendering') if k in e} for e in t['evidence']]
   trace['tool_actions']=[{'request':e['request'],'status':e['observation']['status'],'raw_sha256':e['raw_sha256']} for e in t['tools']]
   trace['call_journal']=[{k:c.get(k) for k in ('call_index','execution_status','cost_usd','usage','latency_s','prompt_sha256')} for c in t['calls']]
   traces.append(trace)
  shutil.copy2(p/'integrity-audit.json',out/(p.name+'-integrity.json'))
  shutil.copy2(p/'grounding_judges/completion.json',out/(p.name+'-grounding-completion.json'))
 for name,value in [('traces',traces),('source_hashes',sources),('config',config),('initial_reuse',initial_reuse),('execution-addenda',execution_addenda)]:
  (out/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 (out/'README.md').write_text(f'''# Authority v2 — {summary['partition']}\n\nRecorded results for all 20 cases, including failed executions and unresolved references/judgments. `summary.json` separates provisional reference-label match, source-grounding judgments, metadata validity, paired comparisons and actual versus deployment-attributed cost. `traces.json` contains all attempts, candidate-selected source URLs/hashes, selected span IDs, rendered quotations, tool actions and model assessments. Full-page web caches and API prompts remain local. No human-verified accuracy is claimed.\n''')
 print(out)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--out',required=True);a=p.parse_args();export(a.run,a.out)
