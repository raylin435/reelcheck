"""Download approved direct files, validate media, and emit a review queue. No model calls."""
import argparse
from datetime import datetime, timezone
import html
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.media import admission_issues, download, inspect, parse_vtt, safe_id, sha256, validate_splits


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def resolve_dvids(candidate, directory):
    url = candidate['source_url']
    if not re.fullmatch(r'https://www\.dvidshub\.net/video/\d+/[a-z0-9-]+', url):
        raise ValueError('Unexpected DVIDS source URL')
    with urllib.request.urlopen(url, timeout=30) as r:
        page = r.read(2_000_000).decode()
    (directory / 'source.html').write_text(page)
    if 'PUBLIC DOMAIN' not in page or 'Asset contains copyrighted material' in page:
        raise ValueError('DVIDS per-asset rights require review')
    sources = re.findall(r'<source[^>]+src=[\"\x27](https://[^\"\x27]+\.mp4)[\"\x27]', page)
    if not sources:
        raise ValueError('No public direct MP4 source; no access bypass attempted')
    tracks = re.findall(r'<track[^>]+src=[\"\x27]([^\"\x27]+)[\"\x27]', page)
    caption = None
    if tracks and tracks[0].startswith('/video/closedcaption/'):
        caption = 'https://www.dvidshub.net' + tracks[0]
    return html.unescape(sources[0]), caption


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', default=str(ROOT / 'data/shortform_candidates.jsonl'))
    p.add_argument('--out', required=True)
    p.add_argument('--acquire', action='store_true')
    p.add_argument('--ffmpeg', default='ffmpeg')
    p.add_argument('--ffprobe', default='ffprobe')
    args = p.parse_args()
    candidates = [json.loads(l) for l in Path(args.manifest).read_text().splitlines() if l.strip()]
    validate_splits(candidates)
    ids = [safe_id(c['clip_id']) for c in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate clip IDs')
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / 'collection.json').exists():
        raise ValueError('Use a fresh output directory')
    report = {'created_at': datetime.now(timezone.utc).isoformat(), 'manifest_sha256': sha256(args.manifest),
              'mode': 'acquire' if args.acquire else 'dry_run', 'clips': [], 'model_calls': 0}
    for candidate in candidates:
        cid = candidate['clip_id']
        directory = out / cid
        directory.mkdir(exist_ok=True)
        record = {'clip_id': cid, 'status': 'discovered', 'media': {}}
        review = {'clip_id': cid, 'reviewer': None, 'reviewer_kind': None, 'watched_full_clip': False,
                  'native_platform_url': candidate.get('native_platform_url'), 'native_platform_verified': False,
                  'media_sha256': None, 'claims': []}
        if not candidate.get('rights', {}).get('download_allowed'):
            record['status'] = 'pending_rights_no_download_attempted'
        elif args.acquire:
            try:
                direct, caption = resolve_dvids(candidate, directory) if candidate.get('acquisition') == 'dvids_public_mp4' else (candidate['direct_media_url'], None)
                record['direct_media_url'] = direct
                record['original_sha256'] = download(direct, directory / 'original.mp4')
                media, raw = inspect(directory / 'original.mp4', args.ffprobe, args.ffmpeg)
                record['media'] = media
                save(directory / 'ffprobe.json', raw)
                review['media_sha256'] = media['sha256']
                record['status'] = 'technical_pass_review_pending' if media['technical_short_form_pass'] else 'excluded_media_shape_or_duration'
                if caption:
                    try:
                        record['captions_sha256'] = download(caption, directory / 'publisher_captions.vtt', max_bytes=2_000_000)
                        record['captions_url'] = caption
                        cues, issues = parse_vtt((directory / 'publisher_captions.vtt').read_text(), media['duration_seconds'])
                        record['captions_status'] = 'publisher_track_has_errors' if issues else 'publisher_track_unreviewed'
                        record['caption_issues'] = issues
                        save(directory / 'timeline.json', {'source': 'publisher_captions_not_verified_audio',
                             'media_sha256': media['sha256'], 'cues': cues, 'issues': issues})
                    except (OSError, ValueError):
                        record['captions_status'] = 'unavailable'
                # Preview frames at 1 fps preserve the original timeline. No crop or trimming.
                frames = directory / 'frames'
                frames.mkdir(exist_ok=True)
                subprocess.run([args.ffmpeg, '-v', 'error', '-i', str(directory / 'original.mp4'),
                                '-vf', 'fps=1,scale=360:-2', '-q:v', '3', str(frames / '%04d.jpg')],
                               check=True, capture_output=True, timeout=120)
                record['frame_sampling'] = {'fps': 1, 'purpose': 'review_preview_only_not_complete_visual_evidence'}
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                record['status'] = 'acquisition_or_validation_failed'
                record['error_type'] = type(exc).__name__
        record['admission_issues'] = admission_issues(candidate, record['media'], review)
        record['benchmark_admitted'] = not record['admission_issues']
        save(directory / 'review.template.json', review)
        report['clips'].append(record)
        save(out / 'collection.json', report)
        print(cid, record['status'], flush=True)
    cards = []
    for c, r in zip(candidates, report['clips']):
        cid = c['clip_id']
        video = f'<video controls preload="metadata" src="{cid}/original.mp4"></video>' if r['media'] else ''
        cards.append(f'<article><h2>{html.escape(c["title"])}</h2>{video}<p>{html.escape(r["status"])}</p>'
                     f'<a href="{html.escape(c["source_url"], quote=True)}">Original source</a> · '
                     f'<a href="{cid}/review.template.json">Review template</a></article>')
    (out / 'review.html').write_text('<!doctype html><meta charset="utf-8"><title>ReelCheck clip review</title>'
        '<style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:20px}article{border-top:1px solid #ccc;padding:20px 0}video{height:460px;max-width:100%}</style>'
        '<h1>Short-form pilot review</h1><p>Candidate queue, not a validated benchmark. Watch the entire original, verify native social publication, and record exact claim timestamps. No truth labels inferred from descriptions.</p>' + ''.join(cards))


if __name__ == '__main__':
    main()
