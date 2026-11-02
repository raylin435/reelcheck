"""Build an explicitly AI-reviewed development packet, not admitted benchmark data.

Claims and reference drafts are prepared before any candidate generation. Sources
were inspected on 2026-11-02. No automatic claim mutation or human review is claimed.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.references import fingerprint, reference_case
from reelcheck.__main__ import check_data


def passage(pid, url, text, date=None, kind='editorial_summary_pending_human_review'):
    return {'id': pid, 'url': url, 'text': text, 'published_date': date,
            'retrieved_date': '2026-11-02', 'evidence_kind': kind,
            'sha256': hashlib.sha256(text.encode()).hexdigest()}


def main():
    survey = 'https://pubmed.ncbi.nlm.nih.gov/34293133/'
    adverse = 'https://pubmed.ncbi.nlm.nih.gov/35123127/'
    fda = 'https://www.fda.gov/drugs/frequently-asked-questions-popular-topics/questions-and-answers-about-fdas-initiative-against-contaminated-weight-loss-products'
    opss = 'https://www.opss.org/article/drug-testing-and-dietary-supplements'
    water = 'https://www.cdc.gov/healthy-weight-growth/water-healthy-drinks/'
    sleep = 'https://www.health.mil/Reference-Center/Publications/2021/05/21/PHCoE_Treating_Insomnia_PatientsGuide_5_20_21_508'
    risk = 'https://www.nhlbi.nih.gov/health/insomnia/causes'
    evidence = {
        'S1': passage('S1', survey, 'Overall, 74% reported using ≥1 DS/wk.', '2021-11-02', 'verbatim_short_excerpt'),
        'S2': passage('S2', survey, 'Editorial summary of the study abstract: DS means dietary supplements. This cross-sectional study surveyed personnel from the US Air Force, Army, Marine Corps and Navy. Between December 2018 and August 2019, 26,681 service members completed questionnaires, about 18% of those successfully contacted. Supplement use was self-reported; the reported 74% is a survey estimate, not a census of every service member.', '2021-11-02'),
        'A1': passage('A1', adverse, 'Editorial summary of the study abstract: In a questionnaire study of US military personnel conducted in 2018–2019, 18% of supplement users taking products at least weekly reported one or more associated adverse effects. These were self-reports in a cross-sectional study rather than proof that each supplement caused the reported event.', '2022-10-01'),
        'F1': passage('F1', fda, 'Editorial summary of FDA questions 1 and 5: Laboratory testing found undeclared drugs and chemicals in selected products marketed for weight loss. Identified ingredients included fenproporex. FDA describes fenproporex as an amphetamine derivative that could produce a positive amphetamine urinalysis. The page also describes serious potential adverse effects of stimulants.'),
        'F2': passage('F2', fda, 'Editorial summary of the FDA introduction and product list: FDA cannot test and identify every potentially contaminated weight-loss product. Its enforcement actions and advisories cover only a fraction of potentially hazardous products. The page lists tainted products identified in an enforcement initiative; it does not describe a random sample of all effective weight-loss supplements.'),
        'O1': passage('O1', opss, 'Editorial summary: OPSS receives questions about whether bodybuilding, testosterone-boosting and weight-loss supplements could lead to a positive military drug test. It explains that laboratory testing is needed to determine whether a product contains undeclared drugs or controlled substances.', '2022-01-12'),
        'W1': passage('W1', water, 'Daily water intake recommendations vary by age, sex, pregnancy status, activity level, and breastfeeding status.', '2026-03-05', 'verbatim_short_excerpt'),
        'W2': passage('W2', water, 'Editorial summary: CDC explains that water intake comes from plain water, other beverages and foods. More water may be needed in hot climates, during greater physical activity, fever, diarrhea or vomiting. This page does not give a formula of half body weight in pounds as fluid ounces of plain water per day.', '2026-03-05'),
        'B1': passage('B1', sleep, 'Editorial summary of the 2020 patient guide: Cognitive behavioral therapy for insomnia (CBT-I) and brief behavioral therapy for insomnia (BBT-I) are specialized behavioral treatments for chronic insomnia. Treatment is available in primary care, behavioral health and sleep clinics. Patients may receive these treatments from specially trained clinical psychologists or social workers, depending on the facility.', '2021-05-21'),
        'B2': passage('B2', sleep, 'Editorial summary: BBT-I treats insomnia by addressing sleep-specific behaviors through multiple sessions. Its components include sleep restriction, stimulus control and some sleep hygiene. Certain coexisting conditions can require tailoring or delaying treatment.', '2021-05-21'),
        'R1': passage('R1', risk, 'Changes in your schedule or environment can cause or raise your risk of insomnia.', None, 'verbatim_short_excerpt'),
        'R2': passage('R2', risk, 'Editorial summary: NHLBI lists shift or night work as factors that can disturb the sleep-wake cycle. Frequently changing the normal routine, including sleep schedule, is also listed as a lifestyle risk factor for sleep problems.')}
    specs = [
        ('sf_01', 'nutrition_supplements', .14, 11.12,
         'Approximately 75% of service members self-report taking at least one dietary supplement at least once a week.',
         ['S1', 'S2'], 'supported',
         'S1 reports 74% weekly use and S2 establishes the service-member population and self-report method. About 75% is a reasonable rounded paraphrase of this historical survey estimate. The clip is from 2022: do not interpret it as a newly measured 2026 rate or an exact census. Approximation is acceptable; retain survey limitations.', 'publisher_captions_and_visual_context'),
        ('sf_02', 'nutrition_supplements', 8.68, 22.75,
         'Dietary supplement use has documented adverse events and positive drug tests.',
         ['A1', 'F1', 'O1'], 'insufficient',
         'A1 documents adverse-effect reports. F1 and O1 establish that hidden ingredients could produce positive tests, but give no observed positive-test case attributable to a supplement. Possibility is not documentation of occurrence. The packet is insufficient for the conjunction, not a refutation of the real-world claim.', 'publisher_captions_and_visual_context'),
        ('sf_03', 'nutrition_supplements', 22.75, 27.84,
         'If a weight-loss supplement works, it is probably a drug.',
         ['F1', 'F2'], 'insufficient',
         'The FDA examples establish that some marketed weight-loss products contain undeclared drugs. They do not quantify the fraction among effective products. The probabilistic generalization is not established or contradicted by this packet. Score the factual interpretation only; rhetoric versus literal intent still needs human review.', 'publisher_captions_and_visual_context'),
        ('sf_04', 'nutrition_eating', 26.03, 40.06,
         'Half of body weight in pounds, expressed as fluid ounces of water per day, is generally a good starting point for hydration.',
         ['W1', 'W2'], 'insufficient',
         'W1 and W2 describe variable needs and sources of total water intake. They neither validate this specific plain-water starting-point formula nor explicitly refute it. Variation does not logically disprove a qualified heuristic. Missing support warrants insufficient rather than contradicted. The video graphic resolves the example as 160 lb and 80 oz.', 'publisher_captions_plus_on_screen_units'),
        ('sf_05', 'health_insomnia', 14.79, 22.72,
         'Behavioral health consultants can provide brief behavioral treatment for insomnia.',
         ['B1', 'B2'], 'supported',
         'B1 describes trained behavioral-health clinicians providing BBT-I, and B2 explains the treatment. Interpret can as availability through appropriately trained clinicians, not permission for every consultant regardless of training. No universal cure or guarantee is claimed.', 'publisher_captions_and_visual_context'),
        ('sf_06', 'health_insomnia', 6.6, 10.917,
         'Irregular work schedules during deployment can contribute to insomnia.',
         ['R1', 'R2'], 'supported',
         'R1 and R2 support changing schedules and shift work as contributors to insomnia. Deployment supplies context, not a unique risk multiplier. Can does not imply certainty. The on-screen list says IRREGULAR WORK SCHEDULE DURING DEPLOYMENT; the publisher caption incorrectly says regular.', 'on_screen_text_with_caption_error_flag')]
    acquisition = json.loads((ROOT / 'data/shortform_acquisition.json').read_text())
    clips = {c['clip_id']: c for c in acquisition['clips']}
    cases, refs = [], []
    for cid, clip, start, end, text, ids, verdict, rationale, origin in specs:
        case = {'case_id': cid, 'group_id': clip, 'as_of': '2026-11-02', 'claim_text': text,
                'evidence': [evidence[i] for i in ids], 'provenance': {
                    'clip_id': clip, 'media_sha256': clips[clip]['media']['sha256'], 'start_seconds': start,
                    'end_seconds': end, 'claim_origin': origin, 'review_status': 'ai_reviewed_development_only',
                    'audio_review': 'publisher_captions_only_no_independent_listening',
                    'visual_review': 'Codex inspected 4-second contact sheets; selected unit and schedule overlays verified',
                    'benchmark_admitted': False, 'native_social_publication_verified': False}}
        cases.append(case)
        refs.append({'case_id': cid, 'case_sha256': fingerprint(reference_case(case)),
                     'acceptable_verdicts': [verdict], 'rationale': rationale, 'evidence_ids': ids,
                     'review_status': 'ai_draft', 'reviewer': 'Codex; not independent human review'})
    check_data(cases)
    for name, rows in [('shortform_dev_inputs.jsonl', cases), ('shortform_dev_reference_drafts.jsonl', refs)]:
        path = ROOT / 'data' / name
        if path.exists():
            raise ValueError('Refusing overwrite of prepared development packet: ' + name)
        path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    print('Prepared 6 development claims from 3 clips; not admitted benchmark data.')


if __name__ == '__main__':
    main()
