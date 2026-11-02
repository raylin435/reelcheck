"""Freeze reviewed references and explicit unresolved keys before candidate inference."""
from copy import deepcopy
import hashlib,json,re,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from reelcheck.authority_v2 import clean_reader_markup
from reelcheck.contract import canonical_whitespace as norm
from reelcheck.research import now
from run_research import save


def freeze(source,out):
 source=Path(source);out=Path(out)
 if out.exists():raise ValueError('Never overwrite a frozen dataset')
 original=ROOT/'data/authority_v1'
 refs=[json.loads(l) for l in (original/'references.jsonl').read_text().splitlines()]
 reviews={r['id']:r for r in json.loads((source/'blind-reviews/results.json').read_text())}
 anchors={r['id']:r for r in json.loads((source/'citation-anchors/results.json').read_text())}
 spans=json.loads((source/'review-spans.json').read_text())
 completion=json.loads((source/'blind-reviews/completion.json').read_text());fixcomplete=json.loads((source/'citation-anchors/completion.json').read_text())
 if not completion['complete'] or not fixcomplete['complete']:raise ValueError('Review batches incomplete')
 changes=[];reviewed=[]
 for ref in refs:
  r=deepcopy(ref);cid=r['case_id'];group=r['group_id'];issues=[];receipts=[]
  raw=json.loads((source/'sources'/f'{group}.json').read_text())['raw']
  page=clean_reader_markup('\n'.join(re.findall(r'^L\d+: ?(.*)$',raw,re.M)))
  if norm(clean_reader_markup(r['reference_excerpt'])) not in norm(page):issues.append('Original reference excerpt absent from current source')
  for jid in ('kimi','deepseek'):
   row=reviews[cid+'/'+jid];o=row.get('output') or {};anchor=anchors.get(row['id']);quote=o.get('source_quote')
   literal=isinstance(quote,str) and bool(quote.strip()) and norm(quote) in norm(page)
   receipt={'reviewer':jid,'execution_status':row['execution_status'],'review':o,'quote_verbatim':literal}
   if row['execution_status']!='completed' or o.get('confidence')!='high' or o.get('expected_verdict') not in ('supported','contradicted','insufficient'):issues.append(jid+': invalid/ambiguous review')
   if o.get('document_date')!=r['document_date']:issues.append(jid+': date mismatch')
   if not literal:
    a=(anchor or {}).get('output') or {};ids=a.get('span_ids');known={x['id']:x['text'] for x in spans[group]}
    valid=anchor and anchor['execution_status']=='completed' and a.get('previous_verdict_supported') is True and isinstance(ids,list) and all(isinstance(x,str) and x in known for x in ids) and (bool(ids) or o.get('expected_verdict')=='insufficient')
    if not valid:issues.append(jid+': unresolved source anchoring')
    receipt['citation_anchor']=a;receipt['anchored_quotes']=[known[x] for x in (ids or []) if isinstance(x,str) and x in known]
   receipts.append(receipt)
  votes=[x['review'] for x in receipts]
  labels={v.get('expected_verdict') for v in votes};reasons={v.get('uncertainty_reason') for v in votes}
  if len(labels)!=1 or len(reasons)!=1:issues.append('Reviewers disagree')
  if cid=='authority_06_2':
   issues.append('Open-world ambiguity: unnamed manufacturer; request notice cannot establish completed implementation. Reviewers agree insufficient/missing_evidence, original key used missing_context. Subreason is not uniquely determined; retain unresolved for every candidate.')
  if not issues:
   label=next(iter(labels));reason=next(iter(reasons))
   if label!='insufficient' and reason is not None:issues.append('Invalid decisive reason')
   if label=='insufficient' and reason not in ('missing_context','missing_evidence','conflicting_evidence','stale_evidence'):issues.append('Invalid insufficient reason')
   if not issues and (label!=r['verdict'] or reason!=r['uncertainty_reason']):
    changes.append({'case_id':cid,'before':[r['verdict'],r['uncertainty_reason']],'after':[label,reason]});r.update(verdict=label,uncertainty_reason=reason)
  r.update(review_status='unresolved' if issues else 'machine_consensus',reference_status='blind machine-reviewed; not human-verified',review={'human_reviewed':False,'receipts':receipts,'issues':issues},reviewed_source_sha256=hashlib.sha256(page.encode()).hexdigest())
  reviewed.append(r)
 out.mkdir(parents=True)
 for split in ('development','heldout'):shutil.copy2(original/f'{split}.jsonl',out/f'{split}.jsonl')
 (out/'references.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in reviewed))
 old=json.loads((original/'manifest.json').read_text())
 manifest={**old,'version':2,'frozen_at':now(),'review_method':'two blind model reviews with full official source pages; exact-span anchoring for non-verbatim reviewer quotes; no candidate outputs',
  'consensus_keys':sum(r['review_status']=='machine_consensus' for r in reviewed),'unresolved_keys':[{'case_id':r['case_id'],'issues':r['review']['issues']} for r in reviewed if r['review_status']=='unresolved'],'label_changes':changes,'human_verified':False,
  'review_artifacts':{str(p.relative_to(source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source/'review-manifest.json',source/'blind-reviews/results.json',source/'citation-anchors/results.json')},
  'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.jsonl')}}
 save(out/'manifest.json',manifest);print(json.dumps({k:manifest[k] for k in ('consensus_keys','unresolved_keys','label_changes')},indent=2))

if __name__=='__main__':freeze(ROOT/'results/authority-review-v2',ROOT/'data/authority_v2')
