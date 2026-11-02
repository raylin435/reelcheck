"""Acquire explicitly permitted direct media and inspect the bytes, not URL labels."""
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def download(url, target, *, expected_sha256=None, max_bytes=200 * 1024 * 1024):
    """Bounded retries, atomic writes, verified cache; never bypass platform access."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('Media must have an HTTPS URL without credentials')
    target = Path(target)
    if target.exists():
        if expected_sha256 and sha256(target) == expected_sha256:
            return sha256(target)
        raise ValueError('Existing file needs a matching recorded SHA256; refusing overwrite')
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + '.part')
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'ReelCheck-research/0.1'})
            with urllib.request.urlopen(req, timeout=30) as response, partial.open('wb') as f:
                if urllib.parse.urlsplit(response.url).scheme != 'https':
                    raise ValueError('HTTPS downgrade refused')
                total = 0
                while chunk := response.read(1024 * 1024):
                    total += len(chunk)
                    if total > max_bytes:
                        raise ValueError('Download exceeds byte cap')
                    f.write(chunk)
            value = sha256(partial)
            if not total or (expected_sha256 and value != expected_sha256):
                raise ValueError('Empty file or SHA256 mismatch')
            partial.replace(target)
            return value
        except (OSError, ValueError) as exc:
            partial.unlink(missing_ok=True)
            if isinstance(exc, ValueError) or (isinstance(exc, urllib.error.HTTPError) and exc.code < 500 and exc.code != 429) or attempt == 2:
                raise
            time.sleep(attempt + 1)


def probe_fields(raw):
    videos = [s for s in raw.get('streams', []) if s.get('codec_type') == 'video' and not s.get('disposition', {}).get('attached_pic')]
    if len(videos) != 1:
        raise ValueError('Exactly one video stream required')
    v = videos[0]
    rotation = float(v.get('tags', {}).get('rotate', 0))
    for side in v.get('side_data_list', []):
        if 'rotation' in side:
            rotation = float(side['rotation'])
    rotation %= 360
    if rotation not in (0, 90, 180, 270):
        raise ValueError('Non-right-angle rotation needs manual review')
    width, height = int(v['width']), int(v['height'])
    sar = v.get('sample_aspect_ratio', '1:1')
    if sar not in ('N/A', '0:1'):
        a, b = map(int, sar.split(':'))
        width *= a / b
    if rotation in (90, 270):
        width, height = height, width
    duration = float(raw.get('format', {}).get('duration', v.get('duration', 0)))
    if not all(math.isfinite(x) and x > 0 for x in (duration, width, height)):
        raise ValueError('Invalid media dimensions/duration')
    return {'duration_seconds': duration, 'display_width': width, 'display_height': height,
            'rotation': rotation, 'has_audio': any(s.get('codec_type') == 'audio' for s in raw['streams']),
            'codec': v.get('codec_name'), 'format': raw.get('format', {}).get('format_name')}


def inspect(path, ffprobe, ffmpeg):
    result = subprocess.run([str(ffprobe), '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)],
                            check=True, capture_output=True, text=True, timeout=30)
    raw = json.loads(result.stdout)
    fields = probe_fields(raw)
    if fields['duration_seconds'] > 180:
        raise ValueError('Clip longer than 180 seconds')
    # Decode the full original, including audio; metadata alone cannot detect corruption.
    subprocess.run([str(ffmpeg), '-v', 'error', '-xerror', '-i', str(path), '-map', '0:v:0',
                    '-map', '0:a?', '-f', 'null', '-'], check=True, capture_output=True, timeout=120)
    fields.update(decode_ok=True, sha256=sha256(path), bytes=Path(path).stat().st_size)
    fields['technical_short_form_pass'] = 15 <= fields['duration_seconds'] <= 180 and fields['display_height'] >= fields['display_width']
    return fields, raw


def admission_issues(candidate, media, review):
    issues = []
    if not media.get('technical_short_form_pass') or not media.get('decode_ok'):
        issues.append('media_not_verified_short_form')
    if not candidate.get('rights', {}).get('redistribution_allowed') or not candidate.get('rights', {}).get('evidence_url'):
        issues.append('redistribution_rights_unverified')
    if not review.get('native_platform_url') or review.get('native_platform_verified') is not True:
        issues.append('native_short_publication_unverified')
    if not review.get('reviewer') or review.get('reviewer_kind') != 'human' or review.get('watched_full_clip') is not True:
        issues.append('full_clip_human_review_pending')
    if review.get('media_sha256') != media.get('sha256') or not media.get('sha256'):
        issues.append('review_not_bound_to_media')
    claims = review.get('claims')
    if not isinstance(claims, list) or not claims:
        issues.append('timestamped_claims_missing')
    else:
        for claim in claims:
            start, end = claim.get('start_seconds'), claim.get('end_seconds')
            if (type(start) not in (int, float) or type(end) not in (int, float)
                    or not 0 <= start < end <= media.get('duration_seconds', 0)
                    or not claim.get('text') or claim.get('origin') not in {'spoken', 'on_screen', 'combined'}):
                issues.append('invalid_claim_span')
                break
    return issues


def validate_splits(rows):
    """Do not let creators, events or original videos cross split boundaries."""
    seen = {}
    for row in rows:
        for key in ('creator_group', 'event_group', 'original_video_group'):
            value = row.get(key)
            if not value or not row.get('split'):
                raise ValueError('Every item needs explicit split and grouping fields')
            group = (key, value)
            if group in seen and seen[group] != row['split']:
                raise ValueError(f'Cross-split leakage: {key}={value}')
            seen[group] = row['split']


def safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,79}', value):
        raise ValueError('Unsafe clip_id')
    return value


def parse_vtt(text, duration):
    """Retain publisher timings; expose invalid cues rather than repairing silently."""
    if not text.lstrip('\ufeff').startswith('WEBVTT'):
        raise ValueError('Caption response is not WebVTT')
    cues, issues = [], []
    def seconds(value):
        parts = list(map(float, value.split(':')))
        if len(parts) not in (2, 3):
            raise ValueError('Invalid cue timestamp')
        return sum(v * 60 ** i for i, v in enumerate(reversed(parts)))
    for block in re.split(r'\n\s*\n', text.replace('\r\n', '\n')):
        lines = block.strip().splitlines()
        if not lines or lines[0].startswith(('NOTE', 'STYLE', 'REGION')):
            continue
        for i, line in enumerate(lines):
            if '-->' not in line:
                continue
            start, rest = line.split('-->', 1)
            a, b = seconds(start.strip()), seconds(rest.strip().split()[0])
            cue = {'start_seconds': a, 'end_seconds': b, 'text': '\n'.join(lines[i + 1:])}
            if not 0 <= a < b <= duration or not cue['text']:
                issues.append({'cue_index': len(cues), 'issue': 'invalid_timing_or_empty_text', 'cue': cue})
            cues.append(cue)
            break
    if not cues:
        issues.append({'issue': 'no_cues'})
    return cues, issues
