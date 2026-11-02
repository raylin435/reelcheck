# Fresh-clip development comparison

**AI-reviewed references and LLM assessments; not human-verified benchmark accuracy.**

6 original-claim paraphrases from 3 downloaded portrait clips. Fixed evidence, not end-to-end video or live retrieval. No new candidate outputs were inspected before freezing references.

| System | Valid outputs | Reference verdict matches | Judge accepted | Unresolved | Wrong decisive vs reference | Median seconds | Generation cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| glm_direct | 6/6 | 4/6 | 4/6 | 0 | 0 | 4.05 | $0.003302 |
| deepseek_reference | 6/6 | 4/6 | 4/6 | 0 | 0 | 3.25 | $0.005461 |
| gptoss_reference | 2/6 | 1/6 | 1/6 | 0 | 1 | 2.20 | $0.002141 |
| gptoss_citation_ids | 6/6 | 5/6 | 5/6 | 0 | 1 | 2.34 | $0.002631 |

Generation: 24 calls, $0.013535275. Judge: 20 calls, $0.284703.

GPT-OSS treatment: 4 paired acceptance wins, 0 losses, 2 ties, 0 unresolved.

## Case-level audit

### sf_01: Approximately 75% of service members self-report taking at least one dietary supplement at least once a week.

Frozen reference: supported. S1 reports 74% weekly use and S2 establishes the service-member population and self-report method. About 75% is a reasonable rounded paraphrase of this historical survey estimate. The clip is from 2022: do not interpret it as a newly measured 2026 rate or an exact census. Approximation is acceptable; retain survey limitations.
- glm_direct: completed; verdict=supported; judge acceptance=True; objective errors=[].
- deepseek_reference: completed; verdict=supported; judge acceptance=True; objective errors=[].
- gptoss_reference: invalid_output; verdict=None; judge acceptance=False; objective errors=['candidate_execution_invalid_output'].
  Candidate: (no parsed answer)
  Judge: (not assessed)
- gptoss_citation_ids: completed; verdict=supported; judge acceptance=True; objective errors=[].

### sf_02: Dietary supplement use has documented adverse events and positive drug tests.

Frozen reference: insufficient. A1 documents adverse-effect reports. F1 and O1 establish that hidden ingredients could produce positive tests, but give no observed positive-test case attributable to a supplement. Possibility is not documentation of occurrence. The packet is insufficient for the conjunction, not a refutation of the real-world claim.
- glm_direct: completed; verdict=insufficient; judge acceptance=True; objective errors=[].
- deepseek_reference: completed; verdict=insufficient; judge acceptance=True; objective errors=[].
- gptoss_reference: invalid_output; verdict=supported; judge acceptance=False; objective errors=['candidate_execution_invalid_output'].
  Candidate: Evidence A1 documents that supplement users report adverse effects, and evidence F1 shows that some supplements contain undeclared drugs (e.g., fenproporex) that can cause positive drug tests.
  Judge: (not assessed)
- gptoss_citation_ids: completed; verdict=supported; judge acceptance=False; objective errors=[].
  Candidate: A1 documents that supplement users reported adverse effects, and F1 shows that some supplements contain undeclared drugs (e.g., fenproporex) that can produce a positive amphetamine urinalysis, supporting both parts of the claim.
  Judge: A1 supports only self-reported adverse effects among some supplement users, and F1/O1 establish that undeclared ingredients such as fenproporex could produce a positive amphetamine urinalysis or require lab testing; they do not document an actual positive drug test attributable to supplement use. The candidate preserves the claim but overclaims the conjunction as supported and gives no uncertainty despite the missing occurrence evidence.

### sf_03: If a weight-loss supplement works, it is probably a drug.

Frozen reference: insufficient. The FDA examples establish that some marketed weight-loss products contain undeclared drugs. They do not quantify the fraction among effective products. The probabilistic generalization is not established or contradicted by this packet. Score the factual interpretation only; rhetoric versus literal intent still needs human review.
- glm_direct: completed; verdict=insufficient; judge acceptance=True; objective errors=[].
- deepseek_reference: completed; verdict=insufficient; judge acceptance=True; objective errors=[].
- gptoss_reference: invalid_output; verdict=None; judge acceptance=False; objective errors=['candidate_execution_invalid_output'].
  Candidate: (no parsed answer)
  Judge: (not assessed)
- gptoss_citation_ids: completed; verdict=insufficient; judge acceptance=True; objective errors=[].

### sf_04: Half of body weight in pounds, expressed as fluid ounces of water per day, is generally a good starting point for hydration.

Frozen reference: insufficient. W1 and W2 describe variable needs and sources of total water intake. They neither validate this specific plain-water starting-point formula nor explicitly refute it. Variation does not logically disprove a qualified heuristic. Missing support warrants insufficient rather than contradicted. The video graphic resolves the example as 160 lb and 80 oz.
- glm_direct: completed; verdict=insufficient; judge acceptance=True; objective errors=[].
- deepseek_reference: completed; verdict=insufficient; judge acceptance=True; objective errors=[].
- gptoss_reference: invalid_output; verdict=None; judge acceptance=False; objective errors=['candidate_execution_invalid_output'].
  Candidate: (no parsed answer)
  Judge: (not assessed)
- gptoss_citation_ids: completed; verdict=insufficient; judge acceptance=True; objective errors=[].

### sf_05: Behavioral health consultants can provide brief behavioral treatment for insomnia.

Frozen reference: supported. B1 describes trained behavioral-health clinicians providing BBT-I, and B2 explains the treatment. Interpret can as availability through appropriately trained clinicians, not permission for every consultant regardless of training. No universal cure or guarantee is claimed.
- glm_direct: completed; verdict=insufficient; judge acceptance=False; objective errors=[].
  Candidate: The evidence confirms that brief behavioral therapy for insomnia (BBT-I) exists and is delivered by 'specially trained clinical psychologists or social workers' in settings including 'behavioral health' clinics, but no passage states that the specific role of 'behavioral health consultants' can provide this treatment. The named provider type in the claim is not addressed by the supplied evidence, so the claim is neither supported nor contradicted.
  Judge: Per the frozen reference, B1 establishes that BBT-I is available in behavioral health settings through specially trained clinicians (clinical psychologists/social workers), and B2 characterizes BBT-I as the brief behavioral treatment; reading 'can' as capability via appropriately trained clinicians makes the claim supported. The candidate preserved the claim and cited real, relevant quotes, but required the literal job title 'behavioral health consultants' and therefore abstained as 'insufficient' despite B1/B2 meeting the reference's supported reading. That is unnecessary abstention rather than genuine missing evidence.
- deepseek_reference: completed; verdict=insufficient; judge acceptance=False; objective errors=[].
  Candidate: The evidence identifies BBT-I as a specialized behavioral treatment and says trained clinical psychologists or social workers may provide such treatments, but it does not state that behavioral health consultants can provide BBT-I.
  Judge: The frozen reference reads B1's placement of CBT-I/BBT-I in behavioral health clinics and delivery by specially trained clinical psychologists or social workers, together with B2's description of BBT-I, as establishing that appropriately trained behavioral-health clinicians can provide brief behavioral treatment for insomnia; it interprets 'can' as availability through trained clinicians rather than a guarantee or permission for every untrained consultant. The candidate preserved the exact claim and quoted B1 accurately, but it abstained as insufficient by demanding the exact job title 'behavioral health consultants,' an overly narrow reading under the reference. Thus its insufficient verdict and missing-evidence uncertainty are not justified, and the cited B1 lines do not support insufficiency since, on the reference reading, they point toward support.
- gptoss_reference: completed; verdict=insufficient; judge acceptance=False; objective errors=[].
  Candidate: The evidence describes brief behavioral therapy for insomnia (BBT-I) and notes it is available in behavioral health settings, provided by specially trained clinical psychologists or social workers. However, it does not specifically state that behavioral health consultants can provide this treatment, so the claim lacks direct supporting evidence.
  Judge: Against the frozen reference, B1 establishes that BBT-I is available in behavioral health settings and delivered by specially trained behavioral-health clinicians (clinical psychologists or social workers), and B2 describes the brief behavioral treatment itself; read as capability/availability rather than a guarantee for every untrained consultant, this supports the claim. The candidate preserved the claim but abstained as 'insufficient' solely because the exact phrase 'behavioral health consultants' is absent, which is unnecessarily strict given B1/B2, gave no citations to the supporting passages, and asserted missing evidence that the packet actually supplies.
- gptoss_citation_ids: completed; verdict=supported; judge acceptance=True; objective errors=[].

### sf_06: Irregular work schedules during deployment can contribute to insomnia.

Frozen reference: supported. R1 and R2 support changing schedules and shift work as contributors to insomnia. Deployment supplies context, not a unique risk multiplier. Can does not imply certainty. The on-screen list says IRREGULAR WORK SCHEDULE DURING DEPLOYMENT; the publisher caption incorrectly says regular.
- glm_direct: completed; verdict=insufficient; judge acceptance=False; objective errors=[].
  Candidate: The evidence supports the general mechanism that irregular or shift work schedules can raise insomnia risk, but no supplied passage addresses the deployment (military/operational) context specified in the claim, so the deployment-scoped assertion cannot be fully verified.
  Judge: R1 states schedule/environment changes can cause or raise insomnia risk, and R2 links shift/night work and frequently changing sleep schedules to sleep problems; the frozen reference also notes the source list expressly names irregular work schedule during deployment. The claim's weak modal 'can' is satisfied and deployment functions as context rather than an unverified unique multiplier, so the packet supports the claim. The candidate preserved the claim and cited genuine relevant quotes, but its 'insufficient' verdict and missing_context uncertainty abstain despite sufficient evidence, making the uncertainty invalid.
- deepseek_reference: completed; verdict=insufficient; judge acceptance=False; objective errors=[].
  Candidate: The evidence supports that schedule changes and irregular routines can raise insomnia or sleep-problem risk, but it does not address deployment work schedules specifically.
  Judge: R1 states schedule changes can cause or raise insomnia risk, and R2 confirms shift/night work and frequently changing sleep schedules are listed risk factors for sleep problems. Together they establish that irregular work schedules can contribute to insomnia; 'can contribute' is a weak modal claim and deployment merely supplies context (the source itself lists irregular work schedule during deployment, per the reference). The candidate's demand for deployment-specific evidence is an unnecessary abstention, so its 'insufficient' verdict is not justified, and its quoted passages actually support the claim rather than the asserted insufficiency.
- gptoss_reference: completed; verdict=supported; judge acceptance=True; objective errors=[].
- gptoss_citation_ids: completed; verdict=supported; judge acceptance=True; objective errors=[].

## Limits

Three correlated clips from one publisher and two topic areas; three supported and three insufficient reference judgments, no contradicted cases. AI-authored evidence summaries and reference interpretations need independent human review. Caption-derived claims were checked against selected visual frames, not independently transcribed from audio. Native social publication remains unverified.

The treatment changes schema generation as well as deterministic quotation rendering; reasoning-output behavior can differ. Quote validity is partly guaranteed by rendering and is not semantic evidence. A single run cannot establish robust speed gains or general model superiority. Keep the unchanged protocol and all failures visible.

## What this result supports

The previously developed citation-ID configuration generalized its output-validity
benefit to these six fresh-to-the-candidate development claims: 2/6 baseline outputs
passed the structural and exact-quote contract, compared with 6/6 treatment outputs.
The baseline made three object-shape/wrapper errors and one abbreviated non-verbatim
quotation. This is an operational reliability result on a small development set.

This is a combined schema-generation and rendering treatment. A schema-matched
full-quotation baseline has not been run on these clips, so the experiment does not
isolate which part of the treatment caused the benefit. It does not show that the
underlying GPT-OSS model acquired better factual knowledge.

The frozen-reference judge accepted 1/6 baseline outputs and 5/6 treatment outputs.
The treatment still overclaimed sf_02: possible positive drug tests were treated as
documented positive tests. Direct GLM and DeepSeek correctly abstained on that case.

The baseline's raw nested sf_04 answer also made a substantive mistake: it called
the hydration rule contradicted because a CDC page does not state the rule. The
treatment answered insufficient, matching the reference distinction between lack
of support and contradiction. The baseline answer additionally failed the output
contract; this example is not an independently scored repaired baseline.

## Reference sensitivity: post-run diagnostic, no rescoring

The two insomnia references need independent adjudication before a quality-ranking
claim. sf_05 maps specially trained psychologists/social workers to behavioral health
consultants; sf_06 applies general schedule-risk evidence to deployment. Those
interpretations were written into the frozen references before inference, but are
not human-validated. The judge accepted the reference interpretations while other
models abstained. Reference anchoring can therefore influence the apparent ranking.

As a descriptive post-run check, the first four cases yielded acceptance of 4/4 for
GLM, 4/4 for DeepSeek, 3/4 for citation-ID GPT-OSS, and 0/4 for baseline GPT-OSS. This
subset was selected after results to examine the disputed references, is not a new
benchmark, and does not replace the full six-case table. It shows why we cannot
claim factual superiority over the other models from the aggregate 5/6 score.

The treatment cost $0.002631 versus $0.002141 for baseline GPT-OSS (about 23% more),
and median service time was 2.34 versus 2.20 seconds. This run supports neither
a cost reduction nor a speed improvement over that baseline. Latency is one noisy
run under two-worker concurrency.

## Provenance and review handoff

References were frozen at 2026-11-02T20:56:41.222847+00:00; generation began at
2026-11-02T20:56:53.529774+00:00. Frozen reference and input hashes were checked
against generation and judge manifests. No inputs or references changed after
viewing answers. Six of seven evidence pages were also snapshotted locally; the
CDC page was readable through the web tool but direct snapshot acquisition returned
HTTP 403. The snapshot manifest retains that failure.

All original media and candidate/judge traces remain local. Independent reviewer
templates, without candidate answers or the AI reference labels, are in
`data/shortform_dev_human_review.template.jsonl`. All six references remain AI drafts
and all three clips remain unadmitted to the independently reviewed benchmark.

Total measured estimate: $0.298238275 for 24 generation calls and 20 paid judge
calls; four invalid outputs were rejected without a judge call. No transcription
API calls or new hosted deployments were used.
