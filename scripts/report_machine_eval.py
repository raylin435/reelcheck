"""Coverage-aware report for the fixed, machine-reviewed two-pass comparison."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.__main__ import digest, save_json
from reelcheck.evaluation import read_jsonl
from reelcheck.judge import objective_errors
from reelcheck.references import load_references


def verify_audit_binding(manifest, cases, audited_inputs=None):
    """Evidence-only revisions can reuse fidelity checks; claim/media edits cannot."""
    original = read_jsonl(audited_inputs) if audited_inputs else cases
    if manifest.get('inputs_sha256') != digest(original) or manifest.get('mode') != 'live':
        raise ValueError('Fidelity audit inputs differ')
    def projection(items):
        return [{k:c.get(k) for k in ('case_id','group_id','claim_text','provenance','evaluation_partition')}
                for c in items]
    if projection(original) != projection(cases):
        raise ValueError('Claim text, timing or media changed since fidelity audit')


def metrics(cases, rows, judgments, refs):
    """Unresolved references never become errors or correct abstentions."""
    ids = {c['case_id'] for c in cases}
    part = [r for r in rows if r['case_id'] in ids]
    js = {j['case_id']: j for j in judgments if j['case_id'] in ids}
    cm = {c['case_id']: c for c in cases}
    resolved = {i for i in ids if refs[i]['acceptable_verdicts']}
    valid = {r['case_id'] for r in part if not objective_errors(r, cm[r['case_id']])}
    matches = [r['case_id'] for r in part if r['case_id'] in resolved & valid
               and (r.get('output') or {}).get('verdict') in refs[r['case_id']]['acceptable_verdicts']]
    wrong = [r['case_id'] for r in part if r['case_id'] in resolved
             and (r.get('output') or {}).get('verdict') in ('supported', 'contradicted')
             and r['output']['verdict'] not in refs[r['case_id']]['acceptable_verdicts']]
    accepted = [i for i in ids if js[i]['model_assessed_acceptance'] is True]
    costs = [r.get('cost_usd') for r in part]
    groups = {c['group_id'] for c in cases}
    return {'cases': len(ids), 'clips': len(groups), 'resolved_reference_cases': len(resolved),
            'unresolved_reference_cases': len(ids-resolved), 'reference_coverage': len(resolved)/len(ids),
            'valid_outputs': len(valid), 'valid_reference_matches': len(matches),
            'valid_reference_matches_over_all': len(matches)/len(ids),
            'valid_reference_matches_over_resolved': len(matches)/len(resolved) if resolved else None,
            'judge_accepted': len(accepted), 'judge_accepted_over_all': len(accepted)/len(ids),
            'judge_accepted_over_resolved': sum(i in resolved for i in accepted)/len(resolved) if resolved else None,
            'judge_rejected': sum(js[i]['model_assessed_acceptance'] is False for i in ids),
            'judge_unresolved': sum(js[i]['model_assessed_acceptance'] is None for i in ids),
            'judge_reference_conflicts': sum(bool(js[i].get('reference_conflict')) for i in ids),
            'wrong_decisive_emitted': len(wrong), 'wrong_decisive_case_ids': wrong,
            'wrong_decisive_valid': len(set(wrong) & valid),
            'verdict_counts': dict(Counter((r.get('output') or {}).get('verdict', 'missing') for r in part)),
            'all_claims_accepted_clips': sum(all(c['case_id'] in accepted for c in cases if c['group_id']==g) for g in groups),
            'deployment_cost_usd': sum(costs) if all(c is not None for c in costs) else None,
            'median_deployment_latency_s': statistics.median(r['latency_s'] for r in part)}


def paired(cases, judgments, systems):
    js = {(j['case_id'], j['system']): j for j in judgments}
    result = {'baseline': systems[0], 'treatment': systems[1], 'wins': [], 'losses': [], 'ties': [], 'unresolved': []}
    for c in cases:
        a,b = [js[c['case_id'],s]['model_assessed_acceptance'] for s in systems]
        key = 'unresolved' if a is None or b is None else 'ties' if a==b else 'wins' if b else 'losses'
        result[key].append(c['case_id'])
    return result


def run(args):
    out = Path(args.out)
    if out.exists():
        raise ValueError('Fresh report directory required')
    cases = read_jsonl(args.inputs)
    bundle, refs = load_references(args.references, cases)
    run, judge, jury, audit = map(Path, (args.run,args.judge,args.jury,args.audit))
    rows, judgments = read_jsonl(run/'runs.jsonl'), read_jsonl(judge/'judgments.jsonl')
    rm,jm,pm,am = [json.loads((d/'manifest.json').read_text()) for d in (run,judge,jury,audit)]
    reference_hash = hashlib.sha256(Path(args.references).read_bytes()).hexdigest()
    if any(m.get('inputs_sha256') != digest(cases) or m.get('mode') != 'live' for m in (rm,jm,pm)):
        raise ValueError('All stages must be live and use identical inputs')
    verify_audit_binding(am,cases,args.audit_inputs)
    if any(m.get('frozen_reference_file_sha256') != reference_hash for m in (rm,jm)) or jm['candidate_rows_sha256'] != digest(rows):
        raise ValueError('Reference/candidate binding differs')
    if hashlib.sha256((jury/'references.frozen.json').read_bytes()).hexdigest() != reference_hash:
        raise ValueError('Reference panel artifact differs')
    systems = rm['systems']
    expected = {(c['case_id'],s) for c in cases for s in systems}
    if len(systems)!=2 or any(len(part)!=len(expected) or {(r['case_id'],r['system']) for r in part}!=expected for part in (rows,judgments)):
        raise ValueError('Incomplete or duplicate paired records')
    subsets = {'all':cases}
    subsets.update({p:[c for c in cases if c['evaluation_partition']==p] for p in sorted({c['evaluation_partition'] for c in cases})})
    results = {}
    for name, subset in subsets.items():
        results[name] = {'systems': {s:metrics(subset,[r for r in rows if r['system']==s],[j for j in judgments if j['system']==s],refs) for s in systems},
                         'paired_acceptance':paired(subset,judgments,systems)}
    summaries = [json.loads((d/'summary.json').read_text()) for d in (run,judge,jury,audit)]
    costs = dict(zip(('generation_physical','grading','references','clip_fidelity'),
                    (summaries[0]['estimated_actual_run_cost_usd'], summaries[1]['estimated_actual_judge_cost_usd'],
                     summaries[2]['estimated_cost_usd'], summaries[3]['estimated_cost_usd'])))
    costs['total'] = sum(costs.values()) if all(v is not None for v in costs.values()) else None
    by_judge = {(j['case_id'],j['system']):j for j in judgments}
    by_run = {(r['case_id'],r['system']):r for r in rows}
    details = []
    for c in cases:
        details.append({'case_id':c['case_id'], 'clip_id':c['group_id'], 'partition':c['evaluation_partition'],
            'claim_text':c['claim_text'], 'reference':refs[c['case_id']],
            'answers':{s:{'candidate':by_run[c['case_id'],s].get('output'),
                         'execution_status':by_run[c['case_id'],s]['execution_status'],
                         'objective_errors':by_judge[c['case_id'],s]['objective_errors'],
                         'accepted':by_judge[c['case_id'],s]['model_assessed_acceptance'],
                         'judge_status':by_judge[c['case_id'],s]['judge_status'],
                         'judgment':(by_judge[c['case_id'],s].get('judge_response') or {}).get('output')}
                       for s in systems}})
    result = {'status':'Machine-reviewed fixed-evidence pilot; no human-verified accuracy',
              'references_human_reviewed':bundle['human_reviewed'], 'inputs_sha256':digest(cases),
              'frozen_reference_file_sha256':reference_hash,'partitions':results, 'cost_usd':costs,
              'calls':{'generation':summaries[0]['paid_calls_attempted'],'grading':summaries[1]['paid_judge_calls'],
                       'references':summaries[2]['paid_calls'],'clip_fidelity':summaries[3]['paid_calls']},'details':details}
    lines = ['# Automated short-video claim evaluation', '',
             'Machine-reviewed references were frozen before candidate generation. These are model assessments of fixed evidence, not verified real-world accuracy or end-to-end video scores.', '',
             'The baseline is GPT-OSS 120B with JSON schema and verbatim citations. The treatment reuses its exact draft and adds one GPT-OSS pass that checks each material requirement. Both stages use the same per-call token ceiling. Treatment cost and latency include both calls.', '']
    for name, values in results.items():
        lines += ['## '+name.replace('_',' ').capitalize(), '',
                  '| System | Valid | Matches / resolved | Accepted / all | Accepted / resolved | Unresolved grading | Wrong decisive emitted | Median seconds | Deployment cost |',
                  '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for s,m in values['systems'].items():
            cost = 'unknown' if m['deployment_cost_usd'] is None else f"${m['deployment_cost_usd']:.6f}"
            lines.append(f"| {s} | {m['valid_outputs']}/{m['cases']} | {m['valid_reference_matches']}/{m['resolved_reference_cases']} | {m['judge_accepted']}/{m['cases']} | {m['judge_accepted']}/{m['resolved_reference_cases']} | {m['judge_unresolved']} | {m['wrong_decisive_emitted']} | {m['median_deployment_latency_s']:.2f} | {cost} |")
        m = values['systems'][systems[0]]
        pair = values['paired_acceptance']
        lines += ['',f"References resolved: {m['resolved_reference_cases']}/{m['cases']}; {m['unresolved_reference_cases']} unresolved. {m['clips']} clip groups. Treatment acceptance: {len(pair['wins'])} paired wins, {len(pair['losses'])} losses, {len(pair['ties'])} ties, {len(pair['unresolved'])} unresolved pairs.",'']
    lines += ['## Costs', '',json.dumps(costs,indent=2),'',
              'Physical generation billing counts the shared baseline once. Per-system deployment costs above overlap; do not sum them. Estimates use returned usage and recorded prices, not a reconciled provider invoice.', '',
              '## Case audit', '']
    for d in details:
        ref=d['reference']
        lines += [f"### {d['case_id']} ({d['partition']}): {d['claim_text']}", '',
                  'Reference: '+(', '.join(ref['acceptable_verdicts']) or 'unresolved')+'. '+ref['rationale'], '']
        for s,a in d['answers'].items():
            candidate=a['candidate'] or {}
            lines += [f"- {s}: {candidate.get('verdict')}; {a['execution_status']}; accepted={a['accepted']}; objective errors={a['objective_errors']}.",
                      '  Explanation: '+candidate.get('explanation','No parsed response.')]
            if a['accepted'] is not True:
                lines.append('  Grade: '+(a['judgment'] or {}).get('rationale',a['judge_status']))
        lines.append('')
    lines += ['## Interpretation limits', '',
        'Six previously tested development claims and nine claims from three new clips are reported separately. The new clips are public-domain DVIDS exports from the same government publisher ecosystem; one creator overlaps development. This is a small correlated pilot, not a representative or statistically conclusive benchmark.', '',
        'Technical checks establish duration (15–180 seconds), portrait/square display dimensions, hashes and complete decoding. Native social-platform publication remains unverified. New claim fidelity was assessed from publisher captions and sampled frames by GLM; no independent audio transcription was performed. Four malformed publisher-caption cues in the reinstatement clip lie outside the selected claim intervals.', '',
        'Evidence packets contain AI-authored source summaries. Two source pages were accessible through indexed primary-page text but returned HTTP 403 to direct downloads; the saved retrieval record distinguishes these from original PDF/HTML snapshots. Missing support in a packet is not proof that a real-world claim is false.', '',
        'Kimi K3 (high reasoning) and DeepSeek (high reasoning) supplied independent reference votes; GLM supplied a third vote only when needed. Explicit scope ambiguity stays unresolved even with a majority. Kimi also graded candidate answers, so its grades are not independent validation of the reference panel. Candidate identities and requirement maps are hidden from the grader.', '',
        'The old six cases received fresh machine references under this protocol. Their scores cannot be compared directly with historical reports that used different AI-draft labels. One new evidence summary was corrected before candidate generation; unchanged references were reused by exact case hash, and all superseded reference-call costs are retained.', '',
        'Unresolved references stay in all-case denominators and are excluded from verdict-error denominators. Wrong decisive emitted counts include parsed answers rejected by the executable gate, preventing a gate-only rejection from appearing to fix reasoning. No outcome-conditioned retry or correction was used. The treatment has an extra call, so this compares workflows, not equal-compute models.', '',
        'Human review is optional for this machine-reviewed track. Human-verified accuracy remains unavailable. Raw votes, candidate outputs, grading disagreements, usage, prompt hashes and source snapshots are retained.']
    out.mkdir(parents=True)
    save_json(out/'summary.json', result)
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'partitions':results,'cost_usd':costs,'calls':result['calls']},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('inputs','references','run','judge','jury','audit','out'):
        p.add_argument('--'+name,required=True)
    p.add_argument('--audit-inputs',help='Original audited inputs when only evidence was revised')
    run(p.parse_args())


if __name__ == '__main__':
    main()
