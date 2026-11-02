"""Build a local candidate-blind review page; never read model answers or AI labels."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import quote


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--template', default='data/shortform_dev_human_review.template.jsonl')
    p.add_argument('--inputs', default='data/shortform_dev_inputs.jsonl')
    p.add_argument('--manifest', default='data/shortform_candidates.jsonl')
    p.add_argument('--media-root', default='data/media/pilot-01')
    p.add_argument('--out', default='results/independent-review-02/index.html')
    args = p.parse_args()
    out = Path(args.out).resolve()
    if out.exists():
        raise ValueError('Refusing to overwrite a review handoff')
    rows = [json.loads(s) for s in Path(args.template).read_text().splitlines()]
    candidates = {c['clip_id']: c for c in map(json.loads, Path(args.manifest).read_text().splitlines())}
    from collections import OrderedDict
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from reelcheck.references import fingerprint, reference_case
    from reelcheck.media import sha256
    inputs = {c['case_id']: c for c in map(json.loads, Path(args.inputs).read_text().splitlines())}
    if len({r['case_id'] for r in rows}) != len(rows) or {r['case_id'] for r in rows} != set(inputs):
        raise ValueError('Review cases must match input cases exactly')
    clips = OrderedDict()
    for row in rows:
        prov = row['clip_provenance']
        cid = prov['clip_id']
        media = Path(args.media_root) / cid / 'original.mp4'
        if not media.is_file():
            raise ValueError(f'Missing local clip: {cid}')
        case = inputs[row['case_id']]
        if case['claim_text'] != row['claim_text'] or case['evidence'] != row['evidence']:
            raise ValueError('Review template differs from inputs')
        if cid not in clips:
            if sha256(media) != prov['media_sha256']:
                raise ValueError('Review media hash mismatch')
            clips[cid] = {'id': cid, 'title': candidates[cid]['title'],
                'media_url': quote(os.path.relpath(media.resolve(), out.parent)),
                'source_url': candidates[cid]['source_url'], 'claims': []}
        # Whitelist public input fields; never emit candidate answers or AI labels.
        clips[cid]['claims'].append({'case_id': row['case_id'], 'claim_text': row['claim_text'],
            'clip_provenance': prov, 'evidence': row['evidence'], 'as_of': case.get('as_of'),
            'case_sha256': fingerprint(reference_case(case))})
    payload = json.dumps({'clips': list(clips.values())}, ensure_ascii=False).replace('<', '\\u003c')
    template = Path(__file__).with_name('review_page.html').read_text()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(template.replace('__REVIEW_DATA__', payload))
    print(out)


if __name__ == '__main__':
    main()
