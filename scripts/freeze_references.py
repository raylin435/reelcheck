"""Prepare blank candidate-free assessments, or freeze completed references before a new run."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.evaluation import read_jsonl
from reelcheck.__main__ import check_data
from reelcheck.references import fingerprint, reference_case, validate_reference


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs', required=True)
    p.add_argument('--drafts', help='Completed JSONL assessments; omit to generate templates')
    p.add_argument('--out', required=True)
    p.add_argument('--allow-ai-drafts', action='store_true', help='Development only; not human ground truth')
    args = p.parse_args()
    cases = read_jsonl(args.inputs)
    check_data(cases)
    out = Path(args.out)
    if out.exists():
        raise ValueError('Refusing to overwrite a reference artifact')
    if not args.drafts:
        refs = [{'case_id': c['case_id'], 'case_sha256': fingerprint(reference_case(c)),
                 'acceptable_verdicts': [], 'rationale': '', 'evidence_ids': [],
                 'review_status': 'ai_draft', 'reviewer': None} for c in cases]
        out.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in refs))
        print('Blank references only. Complete against inputs, without viewing candidate answers.')
        return
    refs = read_jsonl(args.drafts)
    mapping = {r['case_id']: r for r in refs}
    if len(mapping) != len(refs) or set(mapping) != {c['case_id'] for c in cases}:
        raise ValueError('Reference cases must match inputs')
    for c in cases:
        ref = mapping[c['case_id']]
        validate_reference(ref, c)
        if ref['review_status'] != 'human_reviewed' and not args.allow_ai_drafts:
            raise ValueError('Human review required, or explicitly allow AI drafts for development')
    bundle = {'schema_version': 1, 'frozen_at': datetime.now(timezone.utc).isoformat(),
              'references_sha256': fingerprint(refs), 'references': refs,
              'human_reviewed': all(r['review_status'] == 'human_reviewed' for r in refs),
              'note': 'Freeze precedes candidate generation; timestamp/hash are reproducibility checks, not tamper-proof attestation.'}
    out.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + '\n')
    print('Frozen references:', len(refs))


if __name__ == '__main__':
    main()
