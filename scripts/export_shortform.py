"""Export reviewed, evidence-backed claims into the existing verifier input format."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.__main__ import check_data
from reelcheck.evaluation import read_jsonl
from reelcheck.media import admission_issues, safe_id, sha256, validate_splits


def export(candidates, collection, reviews, media_root):
    validate_splits(candidates)
    by_id = {c['clip_id']: c for c in candidates}
    media = {r['clip_id']: r for r in collection['clips']}
    seen, cases = set(), []
    for review in reviews:
        cid = safe_id(review['clip_id'])
        if cid in seen:
            raise ValueError('Duplicate clip review')
        seen.add(cid)
        candidate, record = by_id[cid], media[cid]
        issues = admission_issues(candidate, record['media'], review)
        if issues:
            raise ValueError(f'{cid} not admitted: {", ".join(issues)}')
        if sha256(Path(media_root) / cid / 'original.mp4') != record['media']['sha256']:
            raise ValueError('Media changed after inspection')
        for index, claim in enumerate(review['claims'], 1):
            if not claim.get('evidence') or not claim.get('as_of'):
                raise ValueError('Each claim needs dated evidence and an explicit as_of date')
            for passage in claim['evidence']:
                if not all(passage.get(k) for k in ('id', 'text', 'url', 'retrieved_date', 'evidence_kind', 'sha256')):
                    raise ValueError('Evidence needs text, provenance, date, and excerpt/summary designation')
            cases.append({'case_id': f'{cid}_{index:02d}', 'group_id': candidate['event_group'],
                          'claim_text': claim['text'], 'as_of': claim['as_of'], 'evidence': claim['evidence'],
                          'provenance': {'clip_id': cid, 'media_sha256': record['media']['sha256'],
                          'start_seconds': claim['start_seconds'], 'end_seconds': claim['end_seconds'],
                          'claim_origin': claim['origin'], 'reviewer': review['reviewer'], 'split': candidate['split']}})
    if not cases:
        raise ValueError('No reviewed cases; refusing to create an empty benchmark')
    check_data(cases)
    return cases


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', default=str(ROOT / 'data/shortform_candidates.jsonl'))
    p.add_argument('--collection', required=True)
    p.add_argument('--reviews', required=True, help='Completed JSONL human reviews; never AI drafts')
    p.add_argument('--out', required=True)
    args = p.parse_args()
    output = Path(args.out)
    if output.exists():
        raise ValueError('Refusing overwrite')
    collection_path = Path(args.collection)
    collection = json.loads(collection_path.read_text())
    if collection['manifest_sha256'] != sha256(args.manifest):
        raise ValueError('Candidate manifest changed since acquisition')
    cases = export(read_jsonl(args.manifest), collection, read_jsonl(args.reviews), collection_path.parent)
    output.write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in cases))
    print('Exported reviewed claims:', len(cases))


if __name__ == '__main__':
    main()
