# Schema-matched follow-up: no observed accuracy advantage

Ordinary JSON-schema output matched citation-ID rendering: 6/6 valid outputs,
3/6 reference matches and 3/6 judge-accepted answers for both. All six paired
acceptance outcomes tie. The schema-only model copied every claim and quote
correctly, so this run found no additional validity benefit from rendering.

Both systems incorrectly supported sf_02 by treating a substance's ability to
cause a positive drug test as documentation that positive tests occurred. Both
abstained on sf_05/sf_06, the two disputed scope interpretations. On the four
less reference-sensitive cases, both score 3/4 by the same AI judge. These are
fixed-evidence development results, not independently reviewed accuracy.

The earlier citation-ID score of 5/6 did not repeat: it is 3/6 here. The two
insomnia verdicts changed across runs. Do not claim general factual improvement
or pitch deterministic citation rendering as the central innovation on this evidence.
It can remain an implementation reliability feature. Focus the next hypothesis on
semantic sufficiency, especially possibility versus occurrence, after human review
and fresh diverse cases.

Generation cost: $0.00478092; Kimi high-reasoning judging: $0.176394;
total: **$0.18117492**. Citation IDs used about 20% less generation cost and had
a lower observed median latency (2.43 vs 2.77 seconds), but six cases and one run
cannot establish reliable cost/latency advantages. The primary success metric tied.

See [the predeclared protocol](SHORTFORM_SCHEMA_PROTOCOL.md),
[configuration](config.shortform_schema.json), and
[review instructions](INDEPENDENT_REVIEW.md). Raw outputs, manifests and judge
responses are preserved under `results/shortform-schema-01/` and
`results/shortform-schema-judge-01/`. References and original inputs are unchanged.
This follow-up reuses previously inspected development cases and is not held out.

## Full audit

**AI-reviewed references and LLM assessments; not human-verified benchmark accuracy.**

6 original-claim paraphrases from 3 downloaded portrait clips. Fixed evidence, not end-to-end video or live retrieval. References predate this run; these development cases may have been tested in earlier runs. Consult the run protocol.

| System | Valid outputs | Reference verdict matches | Judge accepted | Unresolved | Wrong decisive vs reference | Median seconds | Generation cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| gptoss_schema_quotes | 6/6 | 3/6 | 3/6 | 0 | 1 | 2.77 | $0.002655 |
| gptoss_citation_ids | 6/6 | 3/6 | 3/6 | 0 | 1 | 2.43 | $0.002126 |

Generation: 12 calls, $0.00478092. Judge: 12 calls, $0.176394.

gptoss_citation_ids versus gptoss_schema_quotes: 0 paired acceptance wins, 0 losses, 6 ties, 0 unresolved.

## Case-level audit

### sf_01: Approximately 75% of service members self-report taking at least one dietary supplement at least once a week.

Frozen reference: supported. S1 reports 74% weekly use and S2 establishes the service-member population and self-report method. About 75% is a reasonable rounded paraphrase of this historical survey estimate. The clip is from 2022: do not interpret it as a newly measured 2026 rate or an exact census. Approximation is acceptable; retain survey limitations.
- gptoss_schema_quotes: completed; verdict=supported; judge acceptance=True; objective errors=[].
- gptoss_citation_ids: completed; verdict=supported; judge acceptance=True; objective errors=[].

### sf_02: Dietary supplement use has documented adverse events and positive drug tests.

Frozen reference: insufficient. A1 documents adverse-effect reports. F1 and O1 establish that hidden ingredients could produce positive tests, but give no observed positive-test case attributable to a supplement. Possibility is not documentation of occurrence. The packet is insufficient for the conjunction, not a refutation of the real-world claim.
- gptoss_schema_quotes: completed; verdict=supported; judge acceptance=False; objective errors=[].
  Candidate: Evidence A1 documents adverse effects among supplement users, and evidence F1 documents that undeclared drugs in supplements can cause a positive amphetamine urinalysis, supporting both parts of the claim.
  Judge: A1 establishes documented self-reported adverse effects among weekly supplement users, satisfying the adverse-events half. However F1 only says undeclared fenproporex "could produce" a positive amphetamine urinalysis and O1 says lab testing is needed to determine whether products contain undeclared drugs; both establish possibility/risk, not an observed positive drug test attributable to supplements. The claim asserts documented positive tests, so citing the modal "could produce" as proof misses the possibility qualifier and overclaims; the packet is insufficient rather than supportive. The candidate's confident supported verdict with null uncertainty is therefore not justified.
- gptoss_citation_ids: completed; verdict=supported; judge acceptance=False; objective errors=[].
  Candidate: A1 documents that supplement users reported adverse effects, establishing adverse events. F1 shows that testing found undeclared amphetamine-like drugs in weight‑loss supplements that can yield positive drug tests, establishing documented positive drug test results.
  Judge: A1 documents reported adverse events, but F1 only states fenproporex 'could produce a positive amphetamine urinalysis' and O1 only notes lab testing is needed — neither documents an actual positive drug test from supplement use. Possibility is not documented occurrence, so the conjunction is not established; the candidate's 'supported' verdict overclaims and lacks appropriate uncertainty. The cited quotes are relevant but insufficient for the asserted relationship.

### sf_03: If a weight-loss supplement works, it is probably a drug.

Frozen reference: insufficient. The FDA examples establish that some marketed weight-loss products contain undeclared drugs. They do not quantify the fraction among effective products. The probabilistic generalization is not established or contradicted by this packet. Score the factual interpretation only; rhetoric versus literal intent still needs human review.
- gptoss_schema_quotes: completed; verdict=insufficient; judge acceptance=True; objective errors=[].
- gptoss_citation_ids: completed; verdict=insufficient; judge acceptance=True; objective errors=[].

### sf_04: Half of body weight in pounds, expressed as fluid ounces of water per day, is generally a good starting point for hydration.

Frozen reference: insufficient. W1 and W2 describe variable needs and sources of total water intake. They neither validate this specific plain-water starting-point formula nor explicitly refute it. Variation does not logically disprove a qualified heuristic. Missing support warrants insufficient rather than contradicted. The video graphic resolves the example as 160 lb and 80 oz.
- gptoss_schema_quotes: completed; verdict=insufficient; judge acceptance=True; objective errors=[].
- gptoss_citation_ids: completed; verdict=insufficient; judge acceptance=True; objective errors=[].

### sf_05: Behavioral health consultants can provide brief behavioral treatment for insomnia.

Frozen reference: supported. B1 describes trained behavioral-health clinicians providing BBT-I, and B2 explains the treatment. Interpret can as availability through appropriately trained clinicians, not permission for every consultant regardless of training. No universal cure or guarantee is claimed.
- gptoss_schema_quotes: completed; verdict=insufficient; judge acceptance=False; objective errors=[].
  Candidate: The evidence confirms that brief behavioral therapy for insomnia (BBT‑I) exists and is offered in behavioral health settings, but it does not state that behavioral health consultants specifically are authorized or capable of providing this treatment.
  Judge: B1 says BBT-I/CBT-I are available in behavioral health clinics and may be delivered by specially trained clinicians; B2 describes BBT-I. Under the frozen reference, this supports the modal claim as availability through appropriately trained behavioral-health clinicians, not a guarantee for every consultant. The candidate preserved the claim but demanded explicit authorization for the exact title 'behavioral health consultants,' so insufficient/missing_evidence is an unnecessary abstention and the cited quotes do not semantically support that abstention.
- gptoss_citation_ids: completed; verdict=insufficient; judge acceptance=False; objective errors=[].
  Candidate: The sources describe brief behavioral therapy for insomnia (BBT‑I) and note it can be delivered by specially trained clinical psychologists or social workers in behavioral health settings, but they do not specifically state that behavioral health consultants are able to provide this treatment.
  Judge: Under the frozen reference, B1 establishes that BBT-I is a brief behavioral treatment available in behavioral health settings from specially trained clinicians, and B2 describes the treatment; the claim's 'can' is read as availability through appropriately trained clinicians rather than a guarantee for every consultant. The candidate preserves the claim but wrongly abstains for lack of the exact job-title phrase and gives no citations to B1/B2.

### sf_06: Irregular work schedules during deployment can contribute to insomnia.

Frozen reference: supported. R1 and R2 support changing schedules and shift work as contributors to insomnia. Deployment supplies context, not a unique risk multiplier. Can does not imply certainty. The on-screen list says IRREGULAR WORK SCHEDULE DURING DEPLOYMENT; the publisher caption incorrectly says regular.
- gptoss_schema_quotes: completed; verdict=insufficient; judge acceptance=False; objective errors=[].
  Candidate: The evidence shows that irregular or shift work schedules can cause insomnia, but it does not address the specific context of deployment, so the claim lacks supporting evidence for that condition.
  Judge: R1 states that schedule or environment changes can cause or raise insomnia risk, and R2 adds shift/night work and frequently changing sleep routine as risk factors. The claim uses the weak modal 'can contribute,' and 'during deployment' is context rather than an extra required causal multiplier, so R1-R2 are sufficient. The candidate preserved the claim and cited relevant quotes, but abstained on a missing-deployment-context rationale that the evidence and modal wording do not require.
- gptoss_citation_ids: completed; verdict=insufficient; judge acceptance=False; objective errors=[].
  Candidate: The sources indicate that changes in schedule or shift work can raise the risk of insomnia, but they do not specifically address work schedules during deployment, so the claim lacks direct supporting evidence for that context.
  Judge: R1 explicitly states changes in schedule can cause or raise risk of insomnia, and R2 identifies shift/night work and frequently changing sleep schedules as risk factors. The claim uses the weak modal 'can contribute,' and deployment is merely context, so R1+R2 establish it. The candidate's own citations actually support the claim, yet it concluded 'insufficient' on the grounds that deployment is not specifically named — an overly strict demand for context-specific evidence. Verdict unjustified, citations do not support the asserted insufficiency relationship, and the missing-context abstention was unnecessary.

## Limits

Three correlated clips from one publisher and two topic areas; three supported and three insufficient reference judgments, no contradicted cases. AI-authored evidence summaries and reference interpretations need independent human review. Caption-derived claims were checked against selected visual frames, not independently transcribed from audio. Native social publication remains unverified.

Quote validity in citation-ID mode is guaranteed by rendering and is not semantic evidence. A single run cannot establish robust speed gains or general model superiority. Keep the unchanged protocol and all failures visible.
- gptoss_schema_quotes: output_mode=schema_quotes; JSON-schema generation with model-authored claim and quotations; no rendering or repair. Fireworks schema mode disables reasoning output. Quote fidelity and claim preservation are checked after generation, not schema-enforced.
- gptoss_citation_ids: output_mode=citation_ids; JSON-schema generation with deterministic claim/quote rendering; Fireworks schema mode disables reasoning output. Quote validity is renderer-enforced, not evidence of semantic entailment.
