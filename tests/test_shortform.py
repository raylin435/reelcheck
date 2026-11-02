import copy
import json
from pathlib import Path
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
import hashlib
import io
from scripts.judge_run import run_judge
from scripts.export_shortform import export

from reelcheck.media import admission_issues, download, parse_vtt, probe_fields, sha256, validate_splits
from reelcheck.references import enforce_reference, fingerprint, load_references, reference_case, reference_prompt
from reelcheck.judge import judge_messages


class MediaTests(unittest.TestCase):
    def test_display_rotation_and_sample_aspect_ratio(self):
        raw = {'format': {'duration': '32.7'}, 'streams': [
            {'codec_type': 'video', 'width': 1920, 'height': 1080, 'sample_aspect_ratio': '1:1',
             'side_data_list': [{'rotation': -90}]}, {'codec_type': 'audio'}]}
        result = probe_fields(raw)
        self.assertEqual((result['display_width'], result['display_height']), (1080, 1920))
        self.assertTrue(result['has_audio'])
        raw['streams'][0]['sample_aspect_ratio'] = '2:1'
        self.assertEqual(probe_fields(raw)['display_height'], 3840)

    def test_nan_duration_rejected(self):
        with self.assertRaises(ValueError):
            probe_fields({'format': {'duration': 'NaN'}, 'streams': [{'codec_type': 'video', 'width': 1, 'height': 1}]})

    def test_url_and_metadata_cannot_admit_an_unreviewed_clip(self):
        c = {'source_url': 'https://youtube.com/shorts/example', 'rights': {'redistribution_allowed': True, 'evidence_url': 'publisher'}}
        m = {'technical_short_form_pass': True, 'decode_ok': True, 'sha256': 'abc', 'duration_seconds': 30}
        self.assertIn('full_clip_human_review_pending', admission_issues(c, m, {}))
        r = {'reviewer': 'test human', 'reviewer_kind': 'human', 'watched_full_clip': True,
             'native_platform_url': c['source_url'], 'native_platform_verified': True, 'media_sha256': 'abc',
             'claims': [{'text': 'Claim', 'start_seconds': 1, 'end_seconds': 5, 'origin': 'spoken'}]}
        self.assertEqual(admission_issues(c, m, r), [])
        r['media_sha256'] = 'different'
        self.assertIn('review_not_bound_to_media', admission_issues(c, m, r))
        r['claims'][0]['end_seconds'] = 100
        self.assertIn('invalid_claim_span', admission_issues(c, m, r))

    def test_split_leakage_by_creator_event_and_original(self):
        a = {'creator_group': 'a', 'event_group': 'x', 'original_video_group': 'one', 'split': 'development'}
        for key in ('creator_group', 'event_group', 'original_video_group'):
            b = {'creator_group': 'b', 'event_group': 'y', 'original_video_group': 'two', 'split': 'test'}
            b[key] = a[key]
            with self.assertRaises(ValueError):
                validate_splits([a, b])

    def test_bad_publisher_caption_timing_remains_visible(self):
        cues, errors = parse_vtt('WEBVTT\n\n00:01.000 --> 00:02.000\nValid\n\n00:03.500 --> 00:03.200\nInvalid\n', 10)
        self.assertEqual(len(cues), 2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]['cue']['text'], 'Invalid')
        with self.assertRaises(ValueError):
            parse_vtt('<html>login</html>', 10)

    def test_cached_file_needs_a_matching_hash(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'clip.mp4'
            f.write_bytes(b'test')
            with self.assertRaises(ValueError):
                download('https://example.com/clip.mp4', f)
            self.assertEqual(download('https://example.com/clip.mp4', f, expected_sha256=sha256(f)), sha256(f))


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.case = {'case_id': 'one', 'claim_text': 'A is 10.', 'evidence': [{'id': 'p', 'text': 'A is 10.'}]}
        self.ref = {'case_id': 'one', 'case_sha256': fingerprint(reference_case(self.case)),
                    'acceptable_verdicts': ['supported'], 'rationale': 'p states the value.',
                    'evidence_ids': ['p'], 'review_status': 'ai_draft'}

    def test_reference_conflict_cannot_become_a_pass(self):
        assessment = {'model_assessed_acceptance': True, 'objective_errors': []}
        result = enforce_reference(assessment, {'expected_verdict': 'contradicted'}, self.ref)
        self.assertIsNone(result['model_assessed_acceptance'])
        self.assertTrue(result['requires_review'])
        assessment = {'model_assessed_acceptance': False, 'objective_errors': ['bad_quote']}
        self.assertFalse(enforce_reference(assessment, {'expected_verdict': 'contradicted'}, self.ref)['model_assessed_acceptance'])

    def test_reference_prompt_keeps_candidate_identity_blind(self):
        row = {'system': 'SECRET', 'requested_model': 'SECRET', 'output': {'claim_text': 'A is 10.'}}
        prompt = reference_prompt(self.case, self.ref, judge_messages(self.case, row))
        self.assertNotIn('SECRET', json.dumps(prompt))
        self.assertIn('frozen_reference', prompt[1]['content'])

    def test_frozen_reference_detects_changed_evidence_or_labels(self):
        bundle = {'schema_version': 1, 'frozen_at': '2026-11-02T00:00:00+00:00',
                  'references': [self.ref], 'references_sha256': fingerprint([self.ref]), 'human_reviewed': False}
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'refs.json'
            p.write_text(json.dumps(bundle))
            load_references(p, [self.case])
            changed = copy.deepcopy(self.case)
            changed['evidence'][0]['text'] = 'A is 20.'
            with self.assertRaises(ValueError):
                load_references(p, [changed])
            bundle['references'][0]['acceptable_verdicts'] = ['contradicted']
            p.write_text(json.dumps(bundle))
            with self.assertRaises(ValueError):
                load_references(p, [self.case])

    def test_judge_requires_prebound_reference_and_rejects_late_freeze(self):
        self.case['evidence'][0]['sha256'] = hashlib.sha256(b'A is 10.').hexdigest()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'inputs.jsonl').write_text(json.dumps(self.case) + '\n')
            (root / 'runs.jsonl').write_text(json.dumps({'case_id': 'one', 'system': 'B', 'execution_status': 'invalid_output'}) + '\n')
            bundle = {'schema_version': 1, 'frozen_at': '2026-11-02T00:00:00+00:00', 'references': [self.ref],
                      'references_sha256': fingerprint([self.ref]), 'human_reviewed': False}
            refs = root / 'refs.json'
            refs.write_text(json.dumps(bundle))
            (root / 'config.json').write_text(json.dumps({'judge': {'provider': 'fireworks', 'model': 'test', 'max_output_tokens': 100,
                'pricing': {'input_per_million': 1, 'output_per_million': 1}}}))
            args = Namespace(run=str(root), inputs=str(root / 'inputs.jsonl'), config=str(root / 'config.json'),
                references=str(refs), role=None, systems=None, out=str(root / 'out'), live=False,
                max_calls=1, max_cost_usd=1, interval=0)
            manifest = {'created_at': '2026-11-02T01:00:00+00:00'}
            (root / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'not bound'):
                run_judge(args)
            manifest['frozen_reference_file_sha256'] = sha256(refs)
            manifest['created_at'] = '2026-11-01T00:00:00+00:00'
            (root / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'after candidate'):
                run_judge(args)
            manifest['created_at'] = '2026-11-02T01:00:00+00:00'
            (root / 'manifest.json').write_text(json.dumps(manifest))
            with redirect_stdout(io.StringIO()):
                run_judge(args)
            self.assertIn('frozen_reference', (root / 'out/request_preview.jsonl').read_text())


class AdmissionExportTests(unittest.TestCase):
    def test_unreviewed_dataset_cannot_be_exported(self):
        candidate = {'clip_id': 'one', 'creator_group': 'a', 'event_group': 'e', 'original_video_group': 'o', 'split': 'development'}
        with self.assertRaisesRegex(ValueError, 'not admitted'):
            export([candidate], {'clips': [{'clip_id': 'one', 'media': {}}]}, [{'clip_id': 'one'}], Path('/tmp'))

    def test_reviewed_export_binds_media_and_does_not_leak_gold(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'one').mkdir()
            file = root / 'one/original.mp4'
            file.write_bytes(b'fixture media bytes')
            h = sha256(file)
            candidate = {'clip_id': 'one', 'creator_group': 'a', 'event_group': 'e', 'original_video_group': 'o',
                         'split': 'development', 'rights': {'redistribution_allowed': True, 'evidence_url': 'publisher'}}
            media = {'technical_short_form_pass': True, 'decode_ok': True, 'sha256': h, 'duration_seconds': 30}
            review = {'clip_id': 'one', 'reviewer': 'reviewer', 'reviewer_kind': 'human', 'watched_full_clip': True,
                      'native_platform_url': 'https://example.com/reel', 'native_platform_verified': True, 'media_sha256': h,
                      'claims': [{'text': 'A is 10.', 'start_seconds': 1, 'end_seconds': 5, 'origin': 'spoken',
                                  'as_of': '2026-11-02', 'gold': 'SECRET', 'evidence': [{'id': 'p', 'text': 'A is 10.',
                                  'sha256': hashlib.sha256(b'A is 10.').hexdigest(), 'url': 'https://example.com/evidence',
                                  'retrieved_date': '2026-11-02', 'evidence_kind': 'verbatim_excerpt'}]}]}
            collection = {'clips': [{'clip_id': 'one', 'media': media}]}
            result = export([candidate], collection, [review], root)
            self.assertEqual(len(result), 1)
            self.assertNotIn('SECRET', json.dumps(result))
            file.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'changed after inspection'):
                export([candidate], collection, [review], root)


if __name__ == '__main__':
    unittest.main()
