"""Report a frozen-reference development run without implying human accuracy."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.__main__ import digest
from reelcheck.evaluation import read_jsonl
from reelcheck.references import load_references


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', required=True)
    p.add_argument('--judge', required=True)
    p.add_argument('--inputs', required=True)
    p.add_argument('--references', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--baseline', default='gptoss_reference')
    p.add_argument('--treatment', default='gptoss_citation_ids')
    args = p.parse_args()
    run, judge, out = Path(args.run), Path(args.judge), Path(args.out)
    if out.exists():
        raise ValueError('Fresh output directory required')
    cases = read_jsonl(args.inputs)
    bundle, refs = load_references(args.references, cases)
    rows, judgments = read_jsonl(run / 'runs.jsonl'), read_jsonl(judge / 'judgments.jsonl')
    rm, jm = [json.loads((d / 'manifest.json').read_text()) for d in (run, judge)]
    ref_hash = hashlib.sha256(Path(args.references).read_bytes()).hexdigest()
    if any(m.get('frozen_reference_file_sha256') != ref_hash or m['inputs_sha256'] != digest(cases) for m in (rm, jm)):
        raise ValueError('Reference/input hashes differ')
    if jm['candidate_rows_sha256'] != digest(rows):
        raise ValueError('Judge assessed different answers')
    planned = {(c['case_id'], s) for c in cases for s in rm['systems']}
    if len(rows) != len(planned) or len(judgments) != len(planned) or {(r['case_id'], r['system']) for r in rows} != planned or {(r['case_id'], r['system']) for r in judgments} != planned:
        raise ValueError('Incomplete or duplicate comparison rows')
    rs, js = [json.loads((d / 'summary.json').read_text()) for d in (run, judge)]
    by_judge = {(r['case_id'], r['system']): r for r in judgments}
    case_map = {c['case_id']: c for c in cases}
    systems, details = {}, []
    for system in rm['systems']:
        part = [r for r in rows if r['system'] == system]
        metrics = dict(rs['systems'][system])
        metrics.update(js['systems'][system])
        metrics['reference_verdict_matches'] = sum((r.get('output') or {}).get('verdict') in refs[r['case_id']]['acceptable_verdicts'] for r in part)
        metrics['wrong_decisive_vs_reference'] = sum((r.get('output') or {}).get('verdict') in {'supported', 'contradicted'} and (r.get('output') or {}).get('verdict') not in refs[r['case_id']]['acceptable_verdicts'] for r in part)
        metrics['reference_conflicts'] = sum(bool(by_judge[r['case_id'], system].get('reference_conflict')) for r in part)
        metrics['verdict_counts'] = dict(Counter((r.get('output') or {}).get('verdict', 'missing') for r in part))
        groups = {c['group_id'] for c in cases}
        metrics['all_claims_judge_accepted_clips'] = sum(all(by_judge[c['case_id'], system]['model_assessed_acceptance'] is True for c in cases if c['group_id'] == group) for group in groups)
        systems[system] = metrics
        for row in part:
            j = by_judge[row['case_id'], system]
            details.append({'case_id': row['case_id'], 'clip_id': case_map[row['case_id']]['group_id'], 'system': system,
                'reference_verdicts': refs[row['case_id']]['acceptable_verdicts'], 'execution_status': row['execution_status'],
                'candidate': row.get('output'), 'accepted_by_judge': j.get('model_assessed_acceptance'),
                'objective_errors': j.get('objective_errors', []), 'reference_conflict': j.get('reference_conflict', False),
                'judge': (j.get('judge_response') or {}).get('output')})
    if args.baseline == args.treatment or any(s not in rm['systems'] for s in (args.baseline, args.treatment)):
        raise ValueError('Baseline and treatment must be distinct systems in this run')
    pair = {'baseline': args.baseline, 'treatment': args.treatment, 'acceptance_wins': [], 'acceptance_losses': [], 'ties': [], 'unresolved': []}
    for c in cases:
        a, b = [by_judge[c['case_id'], pair[k]]['model_assessed_acceptance'] for k in ('baseline', 'treatment')]
        category = 'unresolved' if a is None or b is None else 'ties' if a == b else 'acceptance_wins' if b else 'acceptance_losses'
        pair[category].append(c['case_id'])
    result = {'status': 'AI-reviewed development only; no human-verified accuracy', 'cases': len(cases),
        'clips': len({c['group_id'] for c in cases}), 'references_human_reviewed': bundle['human_reviewed'],
        'frozen_reference_file_sha256': ref_hash, 'systems': systems, 'pairwise': pair, 'details': details,
        'generation_cost_usd': rs['estimated_actual_run_cost_usd'], 'judge_cost_usd': js['estimated_actual_judge_cost_usd'],
        'generation_calls': rs['paid_calls_attempted'], 'judge_calls': js['paid_judge_calls']}
    lines = ['# Frozen-reference development comparison', '',
        '**AI-reviewed references and LLM assessments; not human-verified benchmark accuracy.**', '',
        f"{result['cases']} original-claim paraphrases from {result['clips']} downloaded portrait clips. Fixed evidence, not end-to-end video or live retrieval. References predate this run; these development cases may have been tested in earlier runs. Consult the run protocol.", '',
        '| System | Valid outputs | Reference verdict matches | Judge accepted | Unresolved | Wrong decisive vs reference | Median seconds | Generation cost |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name, m in systems.items():
        cost = 'unknown' if m['estimated_total_cost_usd'] is None else f"${m['estimated_total_cost_usd']:.6f}"
        lines.append(f"| {name} | {m['schema_valid_completed']}/{len(cases)} | {m['reference_verdict_matches']}/{len(cases)} | {m['accepted_by_model_assessment']}/{len(cases)} | {m['unresolved']} | {m['wrong_decisive_vs_reference']} | {m['p50_latency_s']:.2f} | {cost} |")
    lines += ['', f"Generation: {result['generation_calls']} calls, ${result['generation_cost_usd']}. Judge: {result['judge_calls']} calls, ${result['judge_cost_usd']}.", '',
        f"{args.treatment} versus {args.baseline}: {len(pair['acceptance_wins'])} paired acceptance wins, {len(pair['acceptance_losses'])} losses, {len(pair['ties'])} ties, {len(pair['unresolved'])} unresolved.", '',
        '## Case-level audit', '']
    for c in cases:
        lines += [f"### {c['case_id']}: {c['claim_text']}", '', 'Frozen reference: ' + ', '.join(refs[c['case_id']]['acceptable_verdicts']) + '. ' + refs[c['case_id']]['rationale']]
        for d in [d for d in details if d['case_id'] == c['case_id']]:
            output = d['candidate'] or {}
            lines.append(f"- {d['system']}: {d['execution_status']}; verdict={output.get('verdict')}; judge acceptance={d['accepted_by_judge']}; objective errors={d['objective_errors']}.")
            if d['accepted_by_judge'] is not True:
                lines.append('  Candidate: ' + output.get('explanation', '(no parsed answer)'))
                lines.append('  Judge: ' + (d['judge'] or {}).get('rationale', '(not assessed)'))
        lines.append('')
    lines += ['## Limits', '',
        'Three correlated clips from one publisher and two topic areas; three supported and three insufficient reference judgments, no contradicted cases. AI-authored evidence summaries and reference interpretations need independent human review. Caption-derived claims were checked against selected visual frames, not independently transcribed from audio. Native social publication remains unverified.', '',
        'Quote validity in citation-ID mode is guaranteed by rendering and is not semantic evidence. A single run cannot establish robust speed gains or general model superiority. Keep the unchanged protocol and all failures visible.']
    for v in rm['config']['variants']:
        lines.append(f"- {v['id']}: output_mode={v.get('output_mode', 'verbatim_quotes')}; " + rm.get('output_mode_notes', {}).get(v['id'], 'See recorded request parameters.'))
    out.mkdir(parents=True)
    (out / 'summary.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    (out / 'REPORT.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps({k: result[k] for k in ('cases', 'clips', 'systems', 'pairwise', 'generation_cost_usd', 'judge_cost_usd')}, indent=2))


if __name__ == '__main__':
    main()
