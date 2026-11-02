"""Read public YouTube player metadata, without media downloads or authentication."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import urllib.request


def inspect(candidate):
    url = candidate['source_url']
    match = re.fullmatch(r'https://www\.youtube\.com/shorts/([\w-]{11})', url)
    if not match:
        raise ValueError('Only canonical public YouTube Shorts leads supported')
    expected = match[1]
    row = {'clip_id': candidate['clip_id'], 'url': url,
           'checked_at': datetime.now(timezone.utc).isoformat(),
           'media_downloaded': False, 'rights_verified': False,
           'native_short_verified': False, 'metadata_short_form_pass': False}
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'ReelCheck-research/0.1'})
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read(4 * 1024 * 1024 + 1)
            if len(body) > 4 * 1024 * 1024:
                raise ValueError('page_size_limit')
        row['page_sha256'] = hashlib.sha256(body).hexdigest()
        text = body.decode('utf-8', 'replace')
        marker = re.search(r'(?:var\s+)?ytInitialPlayerResponse\s*=\s*', text)
        if not marker:
            raise ValueError('primary_player_response_not_found')
        player, _ = json.JSONDecoder().raw_decode(text[marker.end():])
        status = player.get('playabilityStatus', {})
        row['playability'] = {k: status[k] for k in ('status', 'reason') if k in status}
        details = player.get('videoDetails', {})
        if details.get('videoId') != expected:
            # Recommendations or error-page videos must never masquerade as this clip.
            row.update(status='primary_video_not_available', observed_video_id=details.get('videoId'))
            return row
        row['video_details'] = {k: details[k] for k in ('videoId', 'title', 'author', 'channelId', 'lengthSeconds', 'isLiveContent') if k in details}
        micro = player.get('microformat', {}).get('playerMicroformatRenderer', {})
        row['microformat'] = {k: micro[k] for k in ('publishDate', 'uploadDate', 'category', 'isShortsEligible') if k in micro}
        formats = player.get('streamingData', {})
        dimensions = {(f['width'], f['height']) for name in ('formats', 'adaptiveFormats') for f in formats.get(name, []) if f.get('width') and f.get('height')}
        row['video_format_dimensions'] = [list(d) for d in sorted(dimensions)]
        duration = int(details.get('lengthSeconds', '0'))
        row['metadata_short_form_pass'] = bool(15 <= duration <= 180 and dimensions and all(h >= w for w, h in dimensions))
        row['status'] = 'primary_metadata_verified'
        # Native UI publication and byte-based admission still require their own checks.
    except Exception as exc:
        row.update(status='metadata_unavailable', error_type=type(exc).__name__)
        if getattr(exc, 'code', None):
            row['http_status'] = exc.code
        elif isinstance(exc, ValueError):
            row['error'] = str(exc)
    return row


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', default='data/shortform_candidates.jsonl')
    p.add_argument('--out', required=True)
    args = p.parse_args()
    target = Path(args.out)
    if target.exists():
        raise ValueError('Fresh output required')
    candidates = [c for c in map(json.loads, Path(args.manifest).read_text().splitlines()) if c['acquisition'] == 'creator_permission_required']
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(inspect, candidates))
    target.write_text(json.dumps({'note': 'Primary player metadata must match requested video ID. No cookies, login, media download or access bypass. Metadata is not full-clip review or rights clearance.', 'candidates': rows}, indent=2, ensure_ascii=False) + '\n')
    for row in rows:
        print(row['clip_id'], row['status'], row.get('video_details', {}).get('lengthSeconds'), row['metadata_short_form_pass'])


if __name__ == '__main__':
    main()
