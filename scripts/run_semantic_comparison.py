"""Paired baseline versus baseline plus semantic check, with complete two-pass cost."""
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
from reelcheck.contract import validate
from reelcheck.evaluation import read_jsonl
from reelcheck.prompts import messages
from reelcheck.providers import call, load_shell_exports
from reelcheck.references import load_references
from reelcheck.semantic import semantic_config, semantic_messages
from reelcheck.structured import request_config
from scripts.run_model_matrix import _execute, operational_summary, validate_config


def run(args):
    if args.max_calls < 1 or not math.isfinite(args.max_cost_usd) or args.max_cost_usd <= 0:
        raise ValueError('Positive finite budgets required')
    config = json.loads(Path(args.config).read_text())
    variants = config['variants']
    validate_config(config)
    if len(variants) != 2 or variants[0]['model'] != variants[1]['model'] or any(v.get('output_mode') != 'schema_quotes' for v in variants):
        raise ValueError('Two schema-quote variants of the same model required')
    base, treatment = variants
    for key in ('model', 'provider', 'parameters', 'max_output_tokens', 'pricing'):
        if base.get(key) != treatment.get(key):
            raise ValueError('Candidate stage settings must match')
    cases = read_jsonl(args.inputs)
    if not cases:
        raise ValueError('Nonempty cases required')
    check_data(cases)
    bundle, _ = load_references(args.references, cases)
    out = Path(args.out)
    if out.exists():
        raise ValueError('Fresh output required')
    out.mkdir(parents=True)
    created = datetime.now(timezone.utc).isoformat()
    if datetime.fromisoformat(bundle['frozen_at']) > datetime.fromisoformat(created):
        raise ValueError('Reference freeze must precede generation')
    snapshot = out/'source_snapshot'
    snapshot.mkdir()
    hashes = {}
    for path in [*sorted((ROOT/'reelcheck').glob('*.py')), ROOT/'scripts/run_model_matrix.py', Path(__file__).resolve()]:
        rel = path.relative_to(ROOT)
        target = snapshot/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
        hashes[str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
    save_json(snapshot/'config.json', config)
    save_jsonl(snapshot/'inputs.jsonl', cases)
    manifest = {'mode': 'live' if args.live else 'dry_run', 'created_at': created, 'config': config,
        'inputs_sha256': digest(cases), 'frozen_reference_file_sha256': hashlib.sha256(Path(args.references).read_bytes()).hexdigest(),
        'source_files_sha256': hashes, 'case_count': len(cases), 'systems': [v['id'] for v in variants],
        'planned_calls': 2*len(cases), 'max_calls': args.max_calls, 'max_cost_usd': args.max_cost_usd,
        'protocol': 'Generate one baseline per case, reuse that exact draft as semantic-check input. Baseline then dependent check, sequential. No reference labels in candidate prompts. No retry or repair. Treatment deployment cost and latency include both stages; physical billing counts shared baseline once.'}
    save_json(out/'manifest.json', manifest)
    if not args.live:
        save_jsonl(out/'request_preview.jsonl', [{'case_id': c['case_id'], 'baseline': messages(c, 'B'), 'semantic_check_with_empty_draft': semantic_messages(c, None), 'semantic_parameters': semantic_config(treatment, c)['parameters']} for c in cases])
        print(f'Dry run: {len(cases)} pairs; no model results.')
        return
    if args.shell_keys:
        load_shell_exports(args.shell_keys)
    if not os.environ.get('FIREWORKS_API_KEY'):
        raise ValueError('Missing FIREWORKS_API_KEY')
    rows, stages, reserved, calls, halted = [], [], 0., 0, None
    for case in cases:
        prompt = messages(case, 'B')
        bconfig = request_config(base, case)
        # Reserve the known base request; second pass is reserved after its draft exists.
        budget_prompt = prompt + [{'role': 'system', 'content': json.dumps(bconfig['parameters']['response_format'])}]
        bound = upper_cost(bconfig, budget_prompt)
        if calls >= args.max_calls or reserved + bound > args.max_cost_usd:
            halted = halted or 'call_or_cost_budget_reached'
        if halted:
            break
        reserved += bound
        calls += 1
        baseline = _execute(case, base, prompt, calls)
        rows.append(baseline)
        stages.append({'case_id': case['case_id'], 'stage': 'baseline', 'physical_call_index': calls, **baseline})
        if baseline.get('http_status') in {401, 403, 404, 429} or baseline['execution_status'] in {'transport_error', 'runner_error'}:
            halted = 'provider_access_rate_or_transport_error'
        sprompt = semantic_messages(case, baseline.get('output'))
        effective = semantic_config(treatment, case)
        budget_prompt = sprompt + [{'role': 'system', 'content': json.dumps(effective['parameters']['response_format'])}]
        bound = upper_cost(effective, budget_prompt)
        if calls >= args.max_calls or reserved + bound > args.max_cost_usd:
            halted = halted or 'call_or_cost_budget_reached'
        if halted:
            result = {'execution_status': 'not_attempted', 'output': None, 'cost_usd': 0., 'latency_s': 0.}
        else:
            reserved += bound
            calls += 1
            started = time.monotonic()
            try:
                result = call(effective, sprompt)
            except Exception:
                result = {'execution_status': 'runner_error', 'output': None, 'cost_usd': None, 'latency_s': time.monotonic()-started}
            if result['execution_status'] == 'completed':
                errors = validate(result.get('output'), case, require_map=True)
                if errors:
                    result.update(execution_status='invalid_output', validation_errors=errors)
            if result.get('http_status') in {401, 403, 404, 429} or result['execution_status'] in {'transport_error', 'runner_error'}:
                halted = 'provider_access_rate_or_transport_error'
        stage = {'case_id': case['case_id'], 'stage': 'semantic_check', 'physical_call_index': calls if result['execution_status'] != 'not_attempted' else None, 'prompt_sha256': digest(sprompt), 'request_parameters': effective['parameters'], **result}
        stages.append(stage)
        costs = [baseline.get('cost_usd'), result.get('cost_usd')]
        combined = {'case_id': case['case_id'], 'group_id': case.get('group_id', case['case_id']), 'system': treatment['id'],
                   'provider': treatment['provider'], 'requested_model': treatment['model'], 'prompt_system': 'semantic_check',
                   'prompt_sha256': digest(sprompt), 'call_index': calls, **result,
                   'cost_usd': sum(costs) if all(c is not None for c in costs) else None,
                   'latency_s': baseline['latency_s'] + result['latency_s'],
                   'baseline_call_index': baseline['call_index'], 'stage_cost_usd': result.get('cost_usd'),
                   'stage_latency_s': result['latency_s'], 'two_stage_cost_included': True}
        rows.append(combined)
        save_jsonl(out/'runs.jsonl', rows)
        save_jsonl(out/'stages.jsonl', stages)
        print(case['case_id'], baseline['execution_status'], combined['execution_status'], flush=True)
    # A stopped run stays explicitly incomplete; downstream reports reject missing rows.
    save_jsonl(out/'runs.jsonl', rows)
    save_jsonl(out/'stages.jsonl', stages)
    summary = operational_summary(rows, variants, len(cases))
    paid = [r for r in stages if r.get('physical_call_index') is not None]
    costs = [r.get('cost_usd') for r in paid]
    summary.update(paid_calls_attempted=len(paid), estimated_actual_run_cost_usd=sum(costs) if all(c is not None for c in costs) else None,
                   known_cost_subtotal_usd=sum(c for c in costs if c is not None), unknown_cost_calls=sum(c is None for c in costs),
                   physical_billing_note='Baseline shared once; treatment system totals include baseline plus check.',
                   completion={'stop_reason': halted or 'completed', 'planned_calls': 2*len(cases), 'paid_calls_attempted': len(paid), 'saved_records': len(rows), 'reserved_cost_upper_estimate': reserved})
    save_json(out/'summary.json', summary)
    save_json(out/'completion.json', summary['completion'])
    print(json.dumps(summary, indent=2), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'inputs', 'references', 'out'):
        p.add_argument('--'+name, required=True)
    p.add_argument('--live', action='store_true')
    p.add_argument('--shell-keys')
    p.add_argument('--max-calls', type=int, default=40)
    p.add_argument('--max-cost-usd', type=float, default=1.)
    run(p.parse_args())


if __name__ == '__main__':
    main()
