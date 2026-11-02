"""Freeze exact-case references after a documented, pre-candidate evidence revision."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from reelcheck.__main__ import digest,save_json,save_jsonl
from reelcheck.evaluation import read_jsonl
from reelcheck.media import sha256
from reelcheck.references import fingerprint,load_references,reference_case,validate_reference


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('inputs','original','revision','out'):
        p.add_argument('--'+n,required=True)
    args=p.parse_args()
    out=Path(args.out)
    if out.exists():raise ValueError('Fresh output required')
    cases=read_jsonl(args.inputs)
    parents=[Path(args.original),Path(args.revision)]
    refs={};votes=[];summaries=[];provenance=[]
    first_cases=None;new_cases=None;config=None
    for index,parent in enumerate(parents):
        inputs=read_jsonl(parent/'source_snapshot/inputs.jsonl')
        bundle,mapping=load_references(parent/'references.frozen.json',inputs)
        manifest=json.loads((parent/'manifest.json').read_text())
        if manifest['mode']!='live' or manifest['inputs_sha256']!=digest(inputs):raise ValueError('Invalid parent binding')
        if index==0:
            first_cases={c['case_id']:c for c in inputs};config=manifest['config']
        else:
            if config!=manifest['config']:raise ValueError('Reference model settings changed')
            new_cases={c['case_id']:c for c in inputs}
        refs.update(mapping)
        rows=read_jsonl(parent/'votes.jsonl')
        if bundle['vote_rows_sha256']!=digest(rows):raise ValueError('Vote trace modified')
        replaced={c['case_id'] for c in inputs}
        votes=[v for v in votes if v['case_id'] not in replaced]+rows
        summaries.append(json.loads((parent/'summary.json').read_text()))
        provenance.append({'directory':str(parent),'reference_sha256':sha256(parent/'references.frozen.json'),
                           'manifest_sha256':sha256(parent/'manifest.json'),'vote_file_sha256':sha256(parent/'votes.jsonl')})
    changed={c['case_id'] for c in cases if c['case_id'] not in first_cases or reference_case(c)!=reference_case(first_cases[c['case_id']])}
    if changed!=set(new_cases):raise ValueError('Revision must cover exactly changed cases, never unchanged retries')
    if set(refs)!={c['case_id'] for c in cases}:raise ValueError('Reference membership changed')
    for c in cases:validate_reference(refs[c['case_id']],c,allow_machine=True)
    ordered=[refs[c['case_id']] for c in cases]
    stamp=datetime.now(timezone.utc).isoformat()
    frozen={'schema_version':2,'review_track':'machine_reviewed','human_reviewed':False,'frozen_at':stamp,
            'references_sha256':fingerprint(ordered),'references':ordered,'inputs_sha256':digest(cases),
            'vote_rows_sha256':digest(votes),'reference_parents':provenance,
            'note':'One evidence summary was corrected before candidate generation; unchanged exact-case references reused. Superseded votes remain in original parent, and all original/revision costs are counted.'}
    out.mkdir(parents=True);(out/'source_snapshot').mkdir()
    save_json(out/'references.frozen.json',frozen);save_jsonl(out/'votes.jsonl',votes)
    save_jsonl(out/'source_snapshot/inputs.jsonl',cases);save_json(out/'source_snapshot/config.json',config)
    save_json(out/'manifest.json',{'mode':'live','created_at':stamp,'config':config,'inputs_sha256':digest(cases),
              'reference_parents':provenance,'changed_case_ids':sorted(changed),'case_count':len(cases),
              'script_sha256':sha256(__file__),'protocol':'Exact-case reuse plus evidence-corrected reassessment, frozen before all candidate generation.'})
    costs=[s['estimated_cost_usd'] for s in summaries]
    resolved=sum(bool(r['acceptable_verdicts']) for r in ordered)
    summary={'cases':len(cases),'resolved':resolved,'unresolved':len(cases)-resolved,'coverage':resolved/len(cases),
             'paid_calls':sum(s['paid_calls'] for s in summaries),
             'estimated_cost_usd':sum(costs) if all(c is not None for c in costs) else None,
             'reserved_cost_upper_estimate':sum(s['reserved_cost_upper_estimate'] for s in summaries),
             'cost_includes_superseded_reference_votes':True,'stop_reason':'completed','references_human_reviewed':False}
    save_json(out/'summary.json',summary);print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
