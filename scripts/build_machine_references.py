"""Collect two independent assessments, a third only if needed, then freeze all cases."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.__main__ import check_data, digest, save_json, save_jsonl, upper_cost
from reelcheck.evaluation import read_jsonl
from reelcheck.providers import call, load_shell_exports
from reelcheck.machine_jury import jury_messages, vote_errors, initial_agreement, resolve
from reelcheck.references import fingerprint, validate_reference


def run(args):
    if args.max_calls < 1 or not math.isfinite(args.max_cost_usd) or args.max_cost_usd <= 0:
        raise ValueError('Positive finite budgets required')
    config = json.loads(Path(args.config).read_text())
    jury = config['reference_panel']
    if len(jury) != 3 or len({v['model'] for v in jury}) != 3 or len({v['family'] for v in jury}) != 3:
        raise ValueError('Three distinct model families required')
    for v in jury:
        if v['provider'] != 'fireworks' or not 1 <= v['max_output_tokens'] <= 16384 or not 1 <= v.get('timeout_s', 60) <= 60:
            raise ValueError('Invalid reference model configuration')
        if v.get('parameters', {}).get('response_format', {}).get('type') == 'json_schema':
            raise ValueError('Do not disable jury reasoning with JSON-schema mode')
    cases = read_jsonl(args.inputs)
    if not cases:
        raise ValueError('Nonempty cases required')
    check_data(cases)
    out = Path(args.out)
    if out.exists():
        raise ValueError('Fresh output required')
    out.mkdir(parents=True)
    snapshot = out/'source_snapshot'
    snapshot.mkdir()
    hashes = {}
    for path in [*sorted((ROOT/'reelcheck').glob('*.py')), Path(__file__).resolve()]:
        rel = path.relative_to(ROOT)
        target = snapshot/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        hashes[str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
    save_json(snapshot/'config.json', config)
    save_jsonl(snapshot/'inputs.jsonl', cases)
    manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'mode': 'live' if args.live else 'dry_run',
        'inputs_sha256': digest(cases), 'config': config, 'case_count': len(cases), 'source_files_sha256': hashes,
        'max_calls': args.max_calls, 'max_cost_usd': args.max_cost_usd,
        'protocol': 'Two independent votes; third only without initial agreement, blind to other votes. Any explicit scope ambiguity stays unresolved. No candidates or prior labels. All cases retained. No retries.'}
    save_json(out/'manifest.json', manifest)
    if not args.live:
        save_jsonl(out/'request_preview.jsonl', [{'case_id': c['case_id'], 'messages': jury_messages(c)} for c in cases])
        print(f'Dry run: {len(cases)} cases; no reference labels or API calls.')
        return
    if args.shell_keys:
        load_shell_exports(args.shell_keys)
    if not os.environ.get('FIREWORKS_API_KEY'):
        raise ValueError('Missing FIREWORKS_API_KEY')
    records, refs, reserved, calls, halted = [], [], 0., 0, None
    for case in cases:
        votes = []
        prompt = jury_messages(case)
        for index, model in enumerate(jury):
            if index == 2 and initial_agreement(votes):
                break
            bound = upper_cost(model, prompt)
            if calls >= args.max_calls or reserved + bound > args.max_cost_usd:
                halted = halted or 'call_or_cost_budget_reached'
            if halted:
                result = {'execution_status': 'not_attempted', 'output': None, 'cost_usd': 0., 'latency_s': 0.}
            else:
                reserved += bound
                calls += 1
                started = time.monotonic()
                try:
                    result = call(model, prompt)
                except Exception:
                    result = {'execution_status': 'runner_error', 'output': None, 'cost_usd': None, 'latency_s': time.monotonic()-started}
                if result.get('http_status') in {401, 403, 404, 429} or result['execution_status'] in {'transport_error', 'runner_error'}:
                    halted = 'provider_access_rate_or_transport_error'
            row = {'case_id': case['case_id'], 'assessor_index': index+1, 'model': model['model'],
                   'model_family': model['family'], 'prompt_sha256': digest(prompt),
                   'paid_call': result['execution_status'] != 'not_attempted', **result}
            if row['execution_status'] == 'completed':
                row['validation_errors'] = vote_errors(row['output'], case)
                if row['validation_errors']:
                    row['execution_status'] = 'invalid_output'
            records.append(row)
            votes.append(row)
            save_jsonl(out/'votes.jsonl', records)
            print(case['case_id'], 'assessor', index+1, row['execution_status'], flush=True)
        reference = resolve(case, votes)
        validate_reference(reference, case, allow_machine=True)
        refs.append(reference)
    frozen = {'schema_version': 2, 'review_track': 'machine_reviewed', 'human_reviewed': False,
              'frozen_at': datetime.now(timezone.utc).isoformat(), 'references_sha256': fingerprint(refs),
              'references': refs, 'inputs_sha256': digest(cases), 'vote_rows_sha256': digest(records),
              'note': 'Machine agreement is not ground truth. Explicit ambiguities and failed consensus remain in coverage denominators.'}
    save_json(out/'references.frozen.json', frozen)
    costs = [r.get('cost_usd') for r in records if r['paid_call']]
    resolved = sum(bool(r['acceptable_verdicts']) for r in refs)
    summary = {'cases': len(cases), 'resolved': resolved, 'unresolved': len(cases)-resolved, 'coverage': resolved/len(cases),
               'paid_calls': calls, 'estimated_cost_usd': sum(costs) if all(c is not None for c in costs) else None,
               'known_cost_subtotal_usd': sum(c for c in costs if c is not None), 'reserved_cost_upper_estimate': reserved,
               'stop_reason': halted or 'completed', 'references_human_reviewed': False}
    save_json(out/'summary.json', summary)
    print(json.dumps(summary, indent=2), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'inputs', 'out'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--live', action='store_true')
    p.add_argument('--shell-keys')
    p.add_argument('--max-calls', type=int, default=60)
    p.add_argument('--max-cost-usd', type=float, default=5.)
    run(p.parse_args())


if __name__ == '__main__':
    main()
