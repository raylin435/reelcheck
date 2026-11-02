# Automated short-video claim evaluation

Machine-reviewed references were frozen before candidate generation. These are model assessments of fixed evidence, not verified real-world accuracy or end-to-end video scores.

The baseline is GPT-OSS 120B with JSON schema and verbatim citations. The treatment reuses its exact draft and adds one GPT-OSS pass that checks each material requirement. Both stages use the same per-call token ceiling. Treatment cost and latency include both calls.

## All

| System | Valid | Matches / resolved | Accepted / all | Accepted / resolved | Unresolved grading | Wrong decisive emitted | Median seconds | Deployment cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gptoss_schema_quotes | 15/15 | 12/13 | 12/15 | 12/13 | 2 | 1 | 2.15 | $0.006574 |
| gptoss_semantic_check | 15/15 | 11/13 | 11/15 | 11/13 | 2 | 1 | 6.07 | $0.018630 |

References resolved: 13/15; 2 unresolved. 6 clip groups. Treatment acceptance: 0 paired wins, 1 losses, 12 ties, 2 unresolved pairs.

## New clip validation

| System | Valid | Matches / resolved | Accepted / all | Accepted / resolved | Unresolved grading | Wrong decisive emitted | Median seconds | Deployment cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gptoss_schema_quotes | 9/9 | 8/8 | 8/9 | 8/8 | 1 | 0 | 1.99 | $0.003876 |
| gptoss_semantic_check | 9/9 | 7/8 | 7/9 | 7/8 | 1 | 0 | 4.94 | $0.010918 |

References resolved: 8/9; 1 unresolved. 3 clip groups. Treatment acceptance: 0 paired wins, 1 losses, 7 ties, 1 unresolved pairs.

## Previously tested development

| System | Valid | Matches / resolved | Accepted / all | Accepted / resolved | Unresolved grading | Wrong decisive emitted | Median seconds | Deployment cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gptoss_schema_quotes | 6/6 | 4/5 | 4/6 | 4/5 | 1 | 1 | 2.27 | $0.002699 |
| gptoss_semantic_check | 6/6 | 4/5 | 4/6 | 4/5 | 1 | 1 | 6.26 | $0.007712 |

References resolved: 5/6; 1 unresolved. 3 clip groups. Treatment acceptance: 0 paired wins, 0 losses, 5 ties, 1 unresolved pairs.

## Costs

{
  "generation_physical": 0.018630044999999998,
  "grading": 0.279948,
  "references": 0.191685514,
  "clip_fidelity": 0.00383185,
  "total": 0.494095409
}

Physical generation billing counts the shared baseline once. Per-system deployment costs above overlap; do not sum them. Estimates use returned usage and recorded prices, not a reconciled provider invoice.

## Case audit

### sf_01 (previously_tested_development): Approximately 75% of service members self-report taking at least one dietary supplement at least once a week.

Reference: supported. Independent machine agreement. Assessment 1: S1 directly reports 74% using ≥1 dietary supplement per week, which rounds to approximately 75%. S2 confirms DS means dietary supplements, use was self-reported, and the respondents were US service members, matching the claim's material scope without asserting a census. Assessment 2: S1 directly reports 74% using at least one dietary supplement per week, which approximates the claimed 75%. S2 confirms the measure is self-reported among surveyed US service members from four military branches and clarifies it is a survey estimate, not a census; this supports the claim as a survey-based prevalence statement, with some population/representativeness caveats.

- gptoss_schema_quotes: supported; completed; accepted=True; objective errors=[].
  Explanation: S1 reports that 74% of respondents used at least one dietary supplement per week, which is approximately 75%, and S2 confirms the respondents were service members.
- gptoss_semantic_check: supported; completed; accepted=True; objective errors=[].
  Explanation: S1 provides a 74% weekly supplement use estimate, which is approximately 75%. S2 confirms the respondents were U.S. service members and that the data were self‑reported, satisfying all parts of the claim.

### sf_02 (previously_tested_development): Dietary supplement use has documented adverse events and positive drug tests.

Reference: insufficient. Independent machine agreement. Assessment 1: Adverse events are documented: A1 reports 18% of weekly supplement users self-reporting adverse effects (though cross-sectional and non-causal, 'documented' does not require causation). However, for positive drug tests, F1 only states fenproporex 'could produce' a positive amphetamine urinalysis and O1 only discusses the possibility that supplements could lead to positive tests—neither documents an actual positive drug test attributed to supplement use. Since one material part of the conjunctive claim is supported only as potential rather than documented, the claim as a whole is insufficient. Assessment 2: A1 documents self-reported adverse effects associated with supplement use, but not causation. F1 says an undeclared amphetamine derivative in selected weight-loss products could produce a positive urine test, not that positive drug tests were documented. O1 only notes questions and that laboratory testing is needed. Thus the adverse-event component has support, but the documented-positive-drug-test component is not established.

- gptoss_schema_quotes: supported; completed; accepted=False; objective errors=[].
  Explanation: Evidence A1 documents adverse effects among supplement users, and evidence F1 reports that testing found undeclared drugs that can cause a positive amphetamine urinalysis, confirming both adverse events and positive drug tests.
  Grade: The claim is conjunctive. A1 supports documented (self-reported, non-causal) adverse effects among weekly supplement users, satisfying the first part. But for positive drug tests, F1 only says fenproporex 'could produce' a positive amphetamine urinalysis and O1 only frames positive tests as a possibility requiring laboratory confirmation; neither documents an actual positive drug test from supplement use. The candidate's 'supported' verdict treats F1's conditional 'could produce' as documented confirmation, which is an overclaim; the F1 quote is real but semantically insufficient for documented positives, and the candidate gave no uncertainty despite the second conjunct being unestablished. Per the frozen reference the packet cannot decide the full claim, so the justified verdict is insufficient.
- gptoss_semantic_check: supported; completed; accepted=False; objective errors=[].
  Explanation: Evidence A1 documents adverse effects among supplement users, and evidence F1 shows that some supplements contain undeclared drugs that can cause a positive amphetamine urinalysis, thereby supporting both parts of the claim.
  Grade: The conjunctive claim requires documented adverse events AND documented positive drug tests. A1 supports the adverse-event part (18% self-reported adverse effects; documentation does not require causation). But F1 only says fenproporex 'could produce' a positive amphetamine urinalysis and O1 only frames positive tests as a possibility requiring lab confirmation; neither documents an actual positive drug test from supplement use. The candidate's F1 quote establishes potential, not documented occurrence, so 'supported' overclaims and ignores the 'could' qualifier; the justified verdict is insufficient.

### sf_03 (previously_tested_development): If a weight-loss supplement works, it is probably a drug.

Reference: insufficient. Independent machine agreement. Assessment 1: The packet shows only that FDA testing of selected weight-loss products found undeclared drugs/chemicals such as fenproporex and warns of stimulant risks (F1). It does not measure efficacy, estimate the proportion of effective supplements that are drugs, or provide base rates; F2 expressly says the listed products are an enforcement fraction and not a random sample of effective weight-loss supplements, so selection bias prevents generalizing to 'probably a drug.' There is also no explicit counterevidence, so the claim is unproven rather than refuted. Assessment 2: The evidence shows some selected weight-loss products contained undeclared drugs, but it explicitly says the listed products are not a random sample of all effective weight-loss supplements and that FDA enforcement covers only a fraction of potentially hazardous products. It therefore does not establish that a working weight-loss supplement is probably a drug.

- gptoss_schema_quotes: insufficient; completed; accepted=True; objective errors=[].
  Explanation: The provided evidence only notes that some weight‑loss supplements contain undeclared drugs and that FDA testing is limited; it does not address whether effective supplements are likely to be drugs, so the claim lacks supporting evidence.
- gptoss_semantic_check: insufficient; completed; accepted=True; objective errors=[].
  Explanation: The evidence only notes that some weight‑loss products contain undeclared drugs and that FDA testing is limited; it does not provide any information about whether supplements that actually work are drugs or are likely to be drugs.

### sf_04 (previously_tested_development): Half of body weight in pounds, expressed as fluid ounces of water per day, is generally a good starting point for hydration.

Reference: insufficient. Independent machine agreement. Assessment 1: The supplied evidence does not endorse the half-body-weight formula: W1 only states intake needs vary by individual factors, and W2 explicitly notes the source does not give that formula. Absence of the recommendation is not explicit counterevidence that the heuristic is poor, so the claim is unproven rather than refuted. Assessment 2: The packet says water intake recommendations vary and that water comes from beverages and foods, but it neither endorses nor explicitly refutes the half-body-weight-in-pounds as fluid ounces formula. Thus the claim is unproven by the supplied evidence.

- gptoss_schema_quotes: insufficient; completed; accepted=True; objective errors=[].
  Explanation: The supplied evidence only notes that the CDC page does not provide the claimed half‑body‑weight formula and gives no recommendation supporting it; thus there is no evidence confirming the claim.
- gptoss_semantic_check: insufficient; completed; accepted=True; objective errors=[].
  Explanation: The supplied CDC evidence only notes that daily water intake recommendations vary and explicitly states that the page does not give a formula of half body weight in pounds as fluid ounces of water per day; therefore there is no evidence confirming the claimed recommendation.

### sf_05 (previously_tested_development): Behavioral health consultants can provide brief behavioral treatment for insomnia.

Reference: unresolved. Unresolved: at least one assessor flagged material scope ambiguity.

- gptoss_schema_quotes: insufficient; completed; accepted=None; objective errors=[].
  Explanation: The evidence confirms that brief behavioral therapy for insomnia (BBT-I) exists and is offered in behavioral health settings, but it only identifies clinical psychologists or social workers as providers, not "behavioral health consultants". Therefore there is no evidence that behavioral health consultants can provide this treatment.
  Grade: unresolved_machine_reference
- gptoss_semantic_check: insufficient; completed; accepted=None; objective errors=[].
  Explanation: The evidence confirms that brief behavioral therapy for insomnia (BBT‑I) exists and is offered in behavioral health settings, but it only identifies clinical psychologists or social workers as providers and does not mention behavioral health consultants as capable providers. Therefore there is missing evidence that behavioral health consultants can provide this treatment.
  Grade: unresolved_machine_reference

### sf_06 (previously_tested_development): Irregular work schedules during deployment can contribute to insomnia.

Reference: insufficient. Independent machine agreement. Assessment 1: The passages support that schedule changes, shift/night work, and changing sleep routines can cause or raise risk of insomnia, but they do not address deployment or military deployment settings specifically. Since the claim is scoped to irregular work schedules during deployment, that contextual condition is not established by the supplied evidence. Assessment 2: R1 and R2 support that schedule changes, shift/night work, and irregular routines can contribute to insomnia or sleep problems generally, but neither addresses deployment or military populations. The specific 'during deployment' component is unsupported by the packet.

- gptoss_schema_quotes: insufficient; completed; accepted=True; objective errors=[].
  Explanation: The evidence confirms that changes in schedule or shift work can increase insomnia risk, but it does not specifically address deployment contexts, so the claim’s condition "during deployment" lacks supporting evidence.
- gptoss_semantic_check: insufficient; completed; accepted=True; objective errors=[].
  Explanation: The evidence confirms that irregular or shift work schedules can increase the risk of insomnia, but it provides no information about such schedules occurring during deployment, so the claim’s deployment condition lacks support.

### new_01 (new_clip_validation): During 2012–2018, about 2.3 million security-clearance adjudicative actions were performed.

Reference: supported. Independent machine agreement. Assessment 1: D1 states that during 2012–2018 DoD CAF performed about 2.3 million adjudicative actions and gives a precise total of 2,361,717, matching the claim’s date range, rounded magnitude, and action-count framing; the DCSA/DoD CAF context supplies the security-clearance setting. Assessment 2: D1 directly states that during 2012–2018 the DoD CAF performed about 2.3 million adjudicative actions, with a chart total of 2,361,717. The claim’s approximate figure and period match; the evidence also clarifies these are actions, not necessarily distinct individuals.

- gptoss_schema_quotes: supported; completed; accepted=True; objective errors=[].
  Explanation: The evidence explicitly states that during 2012–2018 the DoD CAF performed about 2.3 million adjudicative actions, matching the claim.
- gptoss_semantic_check: supported; completed; accepted=True; objective errors=[].
  Explanation: The evidence states that during 2012–2018 the DoD CAF performed about 2.3 million adjudicative actions, matching the claim’s period and quantity.

### new_02 (new_clip_validation): During 2012–2018, only 12 individuals had clearance eligibility denied or revoked solely for psychological issues.

Reference: supported. Independent machine agreement. Assessment 1: D1 establishes the 2012–2018 DoD CAF context and distinguishes actions/cases from individuals; D2 directly states that twelve individuals had eligibility denied or revoked solely due to security concerns from a psychological condition, with 380 others involving additional concerns. This matches the claim's sole-cause psychological denial/revocation count. Assessment 2: D2 states that twelve individuals had eligibility denied or revoked solely because of security concerns presented by a psychological condition, with another 380 having additional concerns. D1 places the page 33 figures in the 2012–2018 period.

- gptoss_schema_quotes: supported; completed; accepted=True; objective errors=[].
  Explanation: D1 confirms the data period is 2012–2018, and D2 states that exactly twelve individuals had eligibility denied or revoked solely for a psychological condition, matching the claim.
- gptoss_semantic_check: insufficient; completed; accepted=False; objective errors=[].
  Explanation: D2 confirms that exactly twelve individuals were denied or revoked solely for a psychological condition, but it does not specify that this occurred during the 2012–2018 period. D1 establishes the 2012–2018 timeframe for overall adjudicative actions, yet it does not link the twelve‑person count to that period. Therefore the claim lacks explicit evidence tying the number to the stated timeframe.
  Grade: D1 explicitly frames the page 33 DCSA ACCESS figures as DoD CAF adjudications during 2012–2018, and D2 is the same page 33 source summary stating that twelve individuals had eligibility denied or revoked solely because of security concerns from a psychological condition (with 380 others having additional concerns). Jointly D1+D2 establish both the timeframe and the sole-cause individual count, so the reference verdict supported stands. The candidate preserved the claim and quoted D2 accurately, but its missing_context rationale is wrong: the 2012–2018 linkage is supplied by the shared page-33 context in D1, making the insufficient verdict an unnecessary abstention with invalid uncertainty.

### new_03 (new_clip_validation): The 12 denials and revocations solely for psychological issues represent 0.00507% of the 2,361,717 total adjudicative actions in 2012–2018.

Reference: contradicted. Independent machine agreement. Assessment 1: The supplied figures (12 sole-psychological denials/revocations from D2; 2,361,717 total actions from D1) give 12/2,361,717 = 0.000508%, not 0.00507%. The stated percentage is off by a factor of 10 (0.00507% of 2,361,717 ≈ 120, not 12), so the explicit quantitative claim is arithmetically inconsistent with the packet. A secondary individuals-vs-actions unit mismatch exists but is immaterial to the failed percentage. Assessment 2: D1 supplies the 2,361,717 total adjudicative actions and D2 supplies 12 denials/revocations solely for psychological concerns. But 12 ÷ 2,361,717 × 100 = approximately 0.000508%, not 0.00507%; the stated percentage is wrong by roughly a factor of 10.

- gptoss_schema_quotes: contradicted; completed; accepted=True; objective errors=[].
  Explanation: Evidence shows there were 12 such denials/revocations (D2) and 2,361,717 total adjudicative actions (D1). The percentage calculated from these numbers is (12/2,361,717)*100 ≈ 0.000508%, which differs from the claimed 0.00507%.
- gptoss_semantic_check: contradicted; completed; accepted=True; objective errors=[].
  Explanation: Evidence D1 confirms there were 2,361,717 total adjudicative actions, and D2 confirms there were twelve denials/revocations solely for psychological issues. Computing the percentage (12 ÷ 2,361,717 × 100) yields about 0.000508%, which does not match the claimed 0.00507%; therefore the claim’s percentage is incorrect.

### new_04 (new_clip_validation): Following the executive order, the Marine Corps established a COVID-19 reinstatement cell and a pathway for eligible Marines to return to service.

Reference: supported. Independent machine agreement. Assessment 1: M1 states EO 14184 was signed Jan 27, 2025, that subsequent guidance created return-to-service processes for those affected by the vaccine mandate, and that the Marine Corps implemented a program involving recruiters and the COVID Reinstatement Cell, with staff assessing applicants and explaining a pathway. M2 corroborates a case-by-case return-to-service eligibility process. All material parts of the claim—post-order timing, the reinstatement cell, and a pathway for eligible Marines—are directly supported, with no counterevidence. Assessment 2: M1 states that after Executive Order 14184, subsequent guidance established return-to-service processes and the Marine Corps implemented a program involving the COVID Reinstatement Cell, with applicants assessed and given an explained pathway. M2 confirms case-by-case eligibility and return-to-service review, supporting the pathway for eligible Marines.

- gptoss_schema_quotes: supported; completed; accepted=True; objective errors=[].
  Explanation: M1 confirms that after Executive Order 14184, the Marine Corps created a COVID Reinstatement Cell and provided a process (pathway) for eligible Marines to return to service.
- gptoss_semantic_check: supported; completed; accepted=True; objective errors=[].
  Explanation: M1 confirms that after Executive Order 14184 the Marine Corps created a COVID Reinstatement Cell and provides a pathway for eligible Marines to return to service.

### new_05 (new_clip_validation): The Marine Corps team personally contacted 100% of the 3,748 eligible veteran Marines about returning to service.

Reference: insufficient. Independent machine agreement. Assessment 1: The evidence describes a reinstatement program and case-by-case application process, but provides no basis for the specific figures '3,748 eligible veteran Marines,' '100%,' or that the team 'personally contacted' them; it emphasizes applicants submitting information rather than universal proactive outreach. Assessment 2: The evidence describes a Marine Corps return-to-service program and case-by-case application review, but it does not mention 3,748 eligible veteran Marines, personal contact, or 100% outreach. The claim's key quantitative and contact assertions therefore remain unproven.

- gptoss_schema_quotes: insufficient; completed; accepted=True; objective errors=[].
  Explanation: The supplied evidence (M1 and M2) describes the reinstatement program and the return-to-service process but does not mention any personal contact of eligible veteran Marines, nor does it provide the number of eligible veterans (3,748) or a claim of contacting 100% of them. Therefore, there is insufficient evidence to support or contradict the claim.
- gptoss_semantic_check: insufficient; completed; accepted=True; objective errors=[].
  Explanation: The provided evidence (M1 and M2) does not contain any information about a personal contact effort, the number of eligible veteran Marines, or that 100% were contacted, nor that the contact was about returning to service.

### new_06 (new_clip_validation): Since the executive order was signed, 53 Marines had returned to the Marine Corps by the time of this announcement.

Reference: insufficient. Independent machine agreement. Assessment 1: The evidence describes the existence and mechanics of the COVID Reinstatement/return-to-service program following Executive Order 14184, but neither passage provides any count of Marines who returned to service. The specific figure of 53, and the reference to 'this announcement,' are not established or contradicted by the supplied evidence. Assessment 2: The evidence confirms Executive Order 14184 and describes reinstatement processes, but it provides no count of Marines who had returned and no relevant announcement establishing that 53 had returned.

- gptoss_schema_quotes: insufficient; completed; accepted=True; objective errors=[].
  Explanation: The supplied evidence (M1 and M2) describes the executive order and the reinstatement process but does not provide any information about the number of Marines who returned, specifically mentioning 53 Marines.
- gptoss_semantic_check: insufficient; completed; accepted=True; objective errors=[].
  Explanation: The evidence confirms that Executive Order 14184 was signed, but provides no information about any Marines returning, let alone the specific number of 53.

### new_07 (new_clip_validation): The 2026 SoSNIE was the seventh iteration of the annual experiment.

Reference: unresolved. Unresolved: at least one assessor flagged material scope ambiguity.

- gptoss_schema_quotes: insufficient; completed; accepted=None; objective errors=[].
  Explanation: One source (N1) states the 2026 SoSNIE was the seventh annual experiment, while another source (N3) describes the 2025 SoSNIE as the seventh year, creating contradictory evidence about the iteration number for 2026.
  Grade: unresolved_machine_reference
- gptoss_semantic_check: insufficient; completed; accepted=None; objective errors=[].
  Explanation: One source (N1) states the 2026 SoSNIE was the seventh annual experiment, while another source (N3) states the 2025 SoSNIE was the seventh year, providing conflicting evidence about which iteration 2026 represents.
  Grade: unresolved_machine_reference

### new_08 (new_clip_validation): Teaming warfighters with engineers at SoSNIE 2026 provided an opportunity for direct user feedback.

Reference: supported. Independent machine agreement. Assessment 1: N1 states joint forces (warfighters) and engineers tested technologies together at the 2026 SoSNIE, and N2 explicitly states the event facilitated direct warfighter feedback on prototypes; together these cover both the teaming and the direct user feedback elements. Assessment 2: N1 states that at the 2026 SoSNIE, joint forces and engineers tested technologies together, and N2 states the event facilitated direct warfighter feedback on C2 prototypes, supporting the claim that teaming warfighters with engineers provided an opportunity for direct user feedback.

- gptoss_schema_quotes: supported; completed; accepted=True; objective errors=[].
  Explanation: Evidence N1 shows warfighters (joint forces) teamed with engineers, and N2 shows the event enabled direct warfighter feedback, together confirming the claim.
- gptoss_semantic_check: supported; completed; accepted=True; objective errors=[].
  Explanation: Evidence N1 shows warfighters (joint forces) teamed with engineers at SoSNIE 2026, and N2 shows the event facilitated direct warfighter feedback, together confirming the claim.

### new_09 (new_clip_validation): SoSNIE 2026 showed a significant shift in the depth and breadth of the experiment’s scope and participation.

Reference: supported. Independent machine agreement. Assessment 1: N2 explicitly states that the NIWC Atlantic article describes the 2026 iteration as 'a significant shift in the depth and breadth of the experiment’s scope and participation,' directly matching the claim. Supporting context in N1 (40+ technologies, 150+ participants, joint testing) is consistent. Note this is an attributed characterization from a single source, but the claim itself only asserts that SoSNIE 2026 showed this shift, and N2 provides that direct evidence. Assessment 2: N2 explicitly states that the 2026 iteration was described as a significant shift in the depth and breadth of the experiment’s scope and participation. N1 supplies corroborating details about the 2026 experiment’s expanded joint, government, and industry participation and technology testing. N3’s prior-year figures do not directly refute the claim because the metrics differ and a “shift” need not mean an increase.

- gptoss_schema_quotes: supported; completed; accepted=True; objective errors=[].
  Explanation: Evidence N2 explicitly characterizes the 2026 SoSNIE as a significant shift in scope and participation, directly supporting the claim.
- gptoss_semantic_check: supported; completed; accepted=True; objective errors=[].
  Explanation: Evidence N2 explicitly characterizes the 2026 SoSNIE as a significant shift in both depth and breadth of its scope and participation, directly supporting the claim.

## Interpretation limits

Six previously tested development claims and nine claims from three new clips are reported separately. The new clips are public-domain DVIDS exports from the same government publisher ecosystem; one creator overlaps development. This is a small correlated pilot, not a representative or statistically conclusive benchmark.

Technical checks establish duration (15–180 seconds), portrait/square display dimensions, hashes and complete decoding. Native social-platform publication remains unverified. New claim fidelity was assessed from publisher captions and sampled frames by GLM; no independent audio transcription was performed. Four malformed publisher-caption cues in the reinstatement clip lie outside the selected claim intervals.

Evidence packets contain AI-authored source summaries. Two source pages were accessible through indexed primary-page text but returned HTTP 403 to direct downloads; the saved retrieval record distinguishes these from original PDF/HTML snapshots. Missing support in a packet is not proof that a real-world claim is false.

Kimi K3 (high reasoning) and DeepSeek (high reasoning) supplied independent reference votes; GLM supplied a third vote only when needed. Explicit scope ambiguity stays unresolved even with a majority. Kimi also graded candidate answers, so its grades are not independent validation of the reference panel. Candidate identities and requirement maps are hidden from the grader.

The old six cases received fresh machine references under this protocol. Their scores cannot be compared directly with historical reports that used different AI-draft labels. One new evidence summary was corrected before candidate generation; unchanged references were reused by exact case hash, and all superseded reference-call costs are retained.

Unresolved references stay in all-case denominators and are excluded from verdict-error denominators. Wrong decisive emitted counts include parsed answers rejected by the executable gate, preventing a gate-only rejection from appearing to fix reasoning. No outcome-conditioned retry or correction was used. The treatment has an extra call, so this compares workflows, not equal-compute models.

Human review is optional for this machine-reviewed track. Human-verified accuracy remains unavailable. Raw votes, candidate outputs, grading disagreements, usage, prompt hashes and source snapshots are retained.
