"""Create a local development media archive with provenance and checksums, never publish it."""
import argparse
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.evaluation import read_jsonl
from reelcheck.media import safe_id, sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', default=str(ROOT / 'data/shortform_candidates.jsonl'))
    p.add_argument('--collection', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    output = Path(args.out)
    if output.exists():
        raise ValueError('Refusing overwrite')
    path = Path(args.collection)
    report = json.loads(path.read_text())
    if report['manifest_sha256'] != sha256(args.manifest):
        raise ValueError('Manifest changed since acquisition')
    candidates = {r['clip_id']: r for r in read_jsonl(args.manifest)}
    entries, checksums, credits = [], {}, []
    for record in report['clips']:
        if not record.get('media', {}).get('technical_short_form_pass'):
            continue
        cid = safe_id(record['clip_id'])
        c = candidates[cid]
        if not c['rights'].get('redistribution_allowed') or not c['rights'].get('evidence_url'):
            raise ValueError('Cannot package uncleared media')
        original = path.parent / cid / 'original.mp4'
        if sha256(original) != record['media']['sha256']:
            raise ValueError('Media hash changed')
        credits.append({**{k: c[k] for k in ('clip_id', 'title', 'source_url', 'rights')},
                        'creator_credit': record.get('creator_credit', c['creator_group'])})
        for name in ('original.mp4', 'publisher_captions.vtt', 'timeline.json', 'ffprobe.json', 'review.template.json'):
            file = path.parent / cid / name
            if file.exists():
                relative = f'{cid}/{name}'
                entries.append((file, relative))
                checksums[relative] = sha256(file)
    if not entries:
        raise ValueError('No technically validated redistributable files')
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_STORED) as archive:
        for file, name in entries:
            archive.write(file, name)
        archive.writestr('checksums.json', json.dumps(checksums, indent=2))
        archive.writestr('attribution.json', json.dumps(credits, indent=2))
        archive.writestr('README.txt', 'ReelCheck development media pilot. NOT an admitted/scored benchmark.\n'
            'Publisher-hosted social-ready clips; native social publication and full human review remain pending.\n'
            'Publisher captions are unreviewed and may contain errors. Preserve timestamps and qualifiers.\n'
            'Per-asset public-domain markings are recorded in attribution.json; respect DVIDS restrictions.\n'
            'No government endorsement is implied. Repository MIT license does not apply to third-party assets.\n')
    print(json.dumps({'archive': str(output), 'sha256': sha256(output), 'bytes': output.stat().st_size, 'clips': len(credits)}))


if __name__ == '__main__':
    main()
