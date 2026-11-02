"""Partition-level accounting and paired outcomes; never sum duplicated draft bills."""
import argparse,json
from collections import Counter
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from run_authority_v2 import report,ARMS
from run_research import save,accounting
from audit_authority_v2 import audit


def aggregate(root):
 root=Path(root);states=[];summaries=[];audits=[]
 for p in sorted(root.glob('shard-*')):
  if not p.is_dir():continue
  state=json.loads((p/'state.json').read_text());states.append((p.name,state))
  audits.append(audit(p))
  # report writes each shard result; suppress its verbose print only here.
  import contextlib,io
  with contextlib.redirect_stdout(io.StringIO()):report(p,state)
  summaries.append(json.loads((p/'summary.json').read_text()))
 if not states or not all(a['passed'] for a in audits):raise ValueError('Shard integrity failed')
 partition=states[0][1]['partition']
 if len(states)!=states[0][1]['shards'] or {s['shard'] for _,s in states}!=set(range(len(states))):raise ValueError('Missing/duplicate shard')
 if any(s['partition']!=partition or s['source_hashes']!=states[0][1]['source_hashes'] or s['config']!=states[0][1]['config'] for _,s in states):raise ValueError('Inconsistent frozen experiment')
 claimed=[cid for _,s in states for cid in s['selected_case_ids']]
 if len(claimed)!=len(set(claimed)):raise ValueError('Case repeated across shards')
 rows=[r for s in summaries for r in s['rows']]
 cases={c['case_id']:c for c in map(json.loads,(ROOT/f'data/authority_v2/{partition}.jsonl').read_text().splitlines())}
 if set(claimed)!=set(cases):raise ValueError('Partition coverage mismatch')
 systems={};pairs=[]
 for arm in ARMS:
  selected=[r for r in rows if r['arm']==arm]
  if not selected:continue
  tasks=[t for _,s in states for t in s['tasks'] if t['system']==arm]
  systems[arm]={'cases':len(selected),'completed':sum(r['completed'] for r in selected),
    'objective_failures':sum(not r['completed'] for r in selected),
    'reference_label_match':sum(r['reference_label_match'] is True for r in selected),
    'reference_unresolved':sum(r['reference_label_match'] is None for r in selected),
    'wrong_decisive':sum(r['wrong_decisive'] is True for r in selected),
    'operational_abstention':sum(r['operational_abstention'] is True for r in selected),
    'grounding_accepted':sum(r['grounding'] is True for r in selected),
    'grounding_rejected_completed':sum(r['completed'] and r['grounding'] is False for r in selected),
    'grounding_unresolved_completed':sum(r['completed'] and r['grounding'] is None for r in selected) if arm!='no_search' else None,
    'metadata_pass_completed':sum(r['completed'] and r['metadata_errors']==[] for r in selected),
    'recovery_searches':sum(len(t.get('recovery_gaps',[])) for t in tasks),
    'deployment_accounting':accounting([c for t in tasks for c in t['calls']]),
    'searches':sum(t['searches'] for t in tasks),'reads':sum(t['reads'] for t in tasks),
    'by_category':{cat:{'cases':sum(cases[r['case_id']]['category']==cat for r in selected),'label_matches':sum(cases[r['case_id']]['category']==cat and r['reference_label_match'] is True for r in selected)} for cat in sorted({c['category'] for c in cases.values()})},
    'recent_90_days':{'cases':sum(cases[r['case_id']]['fresh_within_90_days'] for r in selected),'label_matches':sum(cases[r['case_id']]['fresh_within_90_days'] and r['reference_label_match'] is True for r in selected)}}
 for cid in sorted(cases):
  by={r['arm']:r for r in rows if r['case_id']==cid};b,t=by['ordinary_retry'],by['authority_recovery']
  values=[b['reference_label_match'],t['reference_label_match']]
  outcome='unresolved' if None in values else 'win' if values==[False,True] else 'loss' if values==[True,False] else 'tie'
  pairs.append({'case_id':cid,'group_id':cases[cid]['group_id'],'both_completed':b['completed'] and t['completed'],'reference_outcome':outcome,'ordinary':values[0],'treatment':values[1],
    'grounding_outcome':'unresolved' if b['grounding'] is None or t['grounding'] is None else 'win' if t['grounding'] and not b['grounding'] else 'loss' if b['grounding'] and not t['grounding'] else 'tie'})
 unique={(shard,c['call_index']):c for shard,s in states for t in s['tasks'] for c in t['calls']}
 judge_calls=[v for _,s in states for t in s['tasks'] for v in t.get('judge_votes',{}).values()]
 tool_unique={(shard,e['request']['request_id']):e for shard,s in states for t in s['tasks'] for e in t['tools']}
 result={'partition':partition,'cases':len(cases),'document_families':len({c['group_id'] for c in cases.values()}),'systems':systems,'pairs':pairs,
   'paired_reference_outcomes':dict(Counter(p['reference_outcome'] for p in pairs)),
   'both_completed_reference_outcomes':dict(Counter(p['reference_outcome'] for p in pairs if p['both_completed'])),
   'candidate_actual_billing':accounting(list(unique.values())),
   'candidate_inherited_billing':accounting([c for (shard,idx),c in unique.items() if idx in dict(states)[shard].get('inherited_call_indices',[])]),
   'candidate_new_billing':accounting([c for (shard,idx),c in unique.items() if idx not in dict(states)[shard].get('inherited_call_indices',[])]),'grounding_actual_billing':accounting(judge_calls),
   'distinct_tools':dict(Counter(e['request']['action'] for e in tool_unique.values())),
   'complete':all(s['complete'] for s in summaries),'all_valid_researched_answers_judged':all(len(t.get('judge_votes',{}))==2 for _,s in states for t in s['tasks'] if t['phase']=='recovery' and t['status']=='completed'),
   'human_verified_accuracy':None,'web_cost_usd':None,'rows':rows,'integrity_audits':audits}
 save(root/'summary.json',result);return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);a=p.parse_args()
 r=aggregate(a.run);print(json.dumps({k:v for k,v in r.items() if k not in ('rows','pairs')},indent=2))
