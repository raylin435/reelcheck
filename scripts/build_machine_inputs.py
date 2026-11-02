"""Versioned fixed-evidence inputs: six old development cases and nine new-clip claims."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reelcheck.__main__ import check_data, save_jsonl
from reelcheck.media import sha256


def passage(pid, url, text, date, retrieval):
    return {'id': pid, 'url': url, 'text': text, 'published_date': date,
            'retrieved_date': '2026-11-02', 'evidence_kind': 'editorial_source_summary_machine_reviewed_track',
            'retrieval_method': retrieval, 'sha256': hashlib.sha256(text.encode()).hexdigest()}


def main():
    target = ROOT/'data/machine_semantic_inputs.jsonl'
    if target.exists():
        raise ValueError('Refusing input overwrite')
    dcsa = 'https://media-cdn.dvidshub.net/pubs/pdf_55292.pdf'
    marine = 'https://www.manpower.marines.mil/COVID-19-Reinstatement/'
    navy26 = 'https://www.niwcatlantic.navy.mil/Media/News-Stories/Article/4456008/sharpening-the-spear-navy-experiment-advances-sensor-to-shooter-connectivity/'
    navy25 = 'https://www.dvidshub.net/news/493793/niwc-atlantic-conducts-wartime-readiness-experiment'
    evidence = {
        'D1': passage('D1', dcsa, 'Source summary, DCSA ACCESS July 2020, page 33: During 2012–2018, DoD CAF performed about 2.3 million adjudicative actions, including grants, denials and jurisdiction decisions. The chart gives 2,361,717 total actions and 46,985 cases with psychological issues. These are adjudicative actions and cases, not necessarily distinct individuals.', '2020-07-01', 'downloaded_pdf_page_visually_checked'),
        'D2': passage('D2', dcsa, 'Source summary, page 33: Twelve individuals had eligibility denied or revoked solely because of security concerns presented by a psychological condition. Another 380 individuals had psychological concerns together with other concerns and were denied or revoked. None of the denials or revocations were solely for seeking mental health care.', '2020-07-01', 'downloaded_pdf_page_visually_checked'),
        'M1': passage('M1', marine, 'Source summary: Executive Order 14184 was signed January 27, 2025. Subsequent guidance established return-to-service and records-correction processes for people affected by the vaccine mandate. The Marine Corps implemented a program involving recruiters and the COVID Reinstatement Cell. Applicants submit information so staff can assess their circumstances and explain a pathway.', None, 'primary_page_retrieved_via_web_search_index_direct_fetch_403'),
        'M2': passage('M2', marine, 'Source summary: The return-to-service process includes review of individual circumstances, required medical and administrative screening, and eligibility and outcome decisions made case by case under governing policy. Submitting an application does not oblige an applicant to return to service.', None, 'primary_page_retrieved_via_web_search_index_direct_fetch_403'),
        'N1': passage('N1', navy26, 'Source summary of the April 8, 2026 article and March 18 photo captions: NIWC Atlantic describes the 2026 SoSNIE as the seventh annual experiment. Joint forces and engineers tested end-to-end mission threads and emerging technologies. The experiment involved more than 40 communications technologies and more than 150 participants from military services, government and industry.', '2026-04-08', 'primary_page_retrieved_via_web_search_index_direct_fetch_403'),
        'N2': passage('N2', navy26, 'Source summary: The event facilitated direct warfighter feedback on command-and-control prototypes. Its stated goals include finding opportunities for greater interoperability and strengthening digital architecture. Activities took place at NIWC Atlantic and off South Carolina, using manned and unmanned systems on land, at sea and in the air.', '2026-04-08', 'primary_page_retrieved_via_web_search_index_direct_fetch_403'),
        'N3': passage('N3', navy25, 'Source summary of the March 26, 2025 article: The annual SoSNIE held in 2025 is described as the seventh year the command hosted the event. The article reports approximately 45 systems and approximately 240 active participants and attendees. It says the team hoped to continue its growth into 2026.', '2025-03-26', 'downloaded_primary_publisher_article'),
    }
    specs = [
        ('new_01', 'clearance_new', 19.224, 27.43, 'During 2012–2018, about 2.3 million security-clearance adjudicative actions were performed.', ['D1'], 'publisher_captions_and_on_screen_chart'),
        ('new_02', 'clearance_new', 31.239, 43.729, 'During 2012–2018, only 12 individuals had clearance eligibility denied or revoked solely for psychological issues.', ['D1', 'D2'], 'spoken_claim_qualified_by_visible_chart_ONLY'),
        ('new_03', 'clearance_new', 35., 43., 'The 12 denials and revocations solely for psychological issues represent 0.00507% of the 2,361,717 total adjudicative actions in 2012–2018.', ['D1', 'D2'], 'on_screen_chart_percentage_and_denominator_at_39_seconds'),
        ('new_04', 'reinstatement_new', 16.889, 29.656, 'Following the executive order, the Marine Corps established a COVID-19 reinstatement cell and a pathway for eligible Marines to return to service.', ['M1', 'M2'], 'publisher_captions_and_embedded_captions'),
        ('new_05', 'reinstatement_new', 45.139, 56.139, 'The Marine Corps team personally contacted 100% of the 3,748 eligible veteran Marines about returning to service.', ['M1', 'M2'], 'publisher_captions_and_embedded_captions'),
        ('new_06', 'reinstatement_new', 58.529, 64.835, 'Since the executive order was signed, 53 Marines had returned to the Marine Corps by the time of this announcement.', ['M1', 'M2'], 'publisher_captions_and_embedded_captions'),
        ('new_07', 'science_new', 44., 52., 'The 2026 SoSNIE was the seventh iteration of the annual experiment.', ['N1', 'N3'], 'on_screen_text'),
        ('new_08', 'science_new', 24., 32., 'Teaming warfighters with engineers at SoSNIE 2026 provided an opportunity for direct user feedback.', ['N1', 'N2'], 'on_screen_text'),
        ('new_09', 'science_new', 44., 52., 'SoSNIE 2026 showed a significant shift in the depth and breadth of the experiment’s scope and participation.', ['N1', 'N2', 'N3'], 'on_screen_text'),
    ]
    collections = {}
    for root in (ROOT/'data/media/machine-pilot-01', ROOT/'data/media/machine-pilot-02'):
        collection = json.loads((root/'collection.json').read_text())
        for record in collection['clips']:
            collections[record['clip_id']] = (root, record)
    old = [json.loads(s) for s in (ROOT/'data/shortform_dev_inputs.jsonl').read_text().splitlines()]
    for c in old:
        c['evaluation_partition'] = 'previously_tested_development'
        c['topic'] = 'nutrition' if c['case_id'] in ('sf_01', 'sf_02', 'sf_03', 'sf_04') else 'health_fitness'
    cases = list(old)
    for cid, clip, start, end, claim, ids, origin in specs:
        root, record = collections[clip]
        if not record['media'].get('technical_short_form_pass') or not 0 <= start < end <= record['media']['duration_seconds']:
            raise ValueError('Failed media or timestamp check')
        if sha256(root/clip/'original.mp4') != record['media']['sha256']:
            raise ValueError('Media hash mismatch')
        cases.append({'case_id': cid, 'group_id': clip, 'as_of': '2026-11-02', 'claim_text': claim,
            'evidence': [evidence[i] for i in ids], 'evaluation_partition': 'new_clip_validation',
            'topic': 'science_technology' if clip == 'science_new' else 'politics_policy',
            'provenance': {'clip_id': clip, 'media_sha256': record['media']['sha256'],
                'media_root': str(root.relative_to(ROOT)), 'start_seconds': start, 'end_seconds': end,
                'claim_origin': origin, 'review_status': 'machine_track_draft', 'benchmark_admitted': False,
                'native_social_publication_verified': False,
                'creator_overlap_with_development': clip == 'clearance_new',
                'audio_review': 'publisher_captions_only_no_independent_listening',
                'visual_review': 'Codex contact sheets at 5-second intervals; clearance chart at 39 seconds',
                'caption_issues': record.get('caption_issues', [])}})
    check_data(cases)
    save_jsonl(target, cases)
    print(f'Prepared {len(old)} old development cases and {len(specs)} new claims from 3 clips; no truth labels.')


if __name__ == '__main__':
    main()
