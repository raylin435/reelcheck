# Recommended next experiment: recent, authoritative evidence

Research checked November 2, 2026. The proposal below is preserved as design history. The staged implementation, dataset and canary are documented in [AUTHORITY.md](AUTHORITY.md); this research note itself is not a measured result.

## Immediate integration work

At planning time, the recovery work was local and had not been pushed. The checked GitHub default branch was at `a25b9df`, which merged a teammate's 50-case development dataset. `scripts/run_recovery.py` is absent there. The local working tree belongs to a parent repository with no commits; do not overwrite the remote with an unrelated initial commit. Start a clean branch from current remote main, reconcile the local implementation, preserve the teammate's files, and include portable result summaries. Exclude credentials, raw full-page caches and large media. Publication is a separate action from the status check performed here.

The teammate's [benchmark50 README](https://github.com/raylin435/reelcheck/blob/a25b9dff6e51323de69c3e01315f6236e11f8f22/video_collection/benchmark50/README.md) describes 50 development cases from 29 videos and 26 creators, with 35 supported, 11 insufficient and four contradicted AI-drafted references. They are pending independent review. Reuse suitable cases as development material, not a fresh final test. Their fixed-packet insufficiency labels cannot be reused as global truth labels when candidates can find new evidence.

## Research findings

| Resource | Use for this project | Important limit |
| --- | --- | --- |
| [FreshQA / FreshLLMs](https://github.com/freshllms/freshqa) | Changing facts and false-premise questions; dated evaluation versions | The displayed latest version is April 21, 2026 despite a stated weekly update policy. Revalidate answers rather than assume freshness. |
| [SealQA, revised paper](https://arxiv.org/html/2506.01062v4) | Search results that conflict, mislead or fail to answer; temporal reasoning and source selection | Table 1 reports GPT-5-high with search at 43.2% on Seal-0. This is that paper's historical setup, not a measurement of today's best model. Pin dataset revision and answer date. |
| [FRAMES](https://aclanthology.org/2025.naacl-long.243/) | Questions requiring evidence from multiple documents and reasoning across constraints | Useful for retrieval/reasoning; not specifically a fresh government-health benchmark. |
| [HealthBench](https://openai.com/index/healthbench/) | Physician-written answer requirements and omissions for realistic health conversations | Broader clinical communication task, not a direct replacement for our claim-verification dataset or a freshness test. |
| [FDA safety communications](https://www.fda.gov/drugs/drug-safety-and-availability/drug-safety-communications), [CDC HAN](https://www.cdc.gov/han/index.html) | Dated primary notices and guidance for constructing a narrow current-information test | These are source collections, not pre-labeled benchmark datasets. Verify the actual notice, scope and effective date. |

Benchmarks identify failures; selecting a harder dataset does not itself improve a model. Freshness alone can show that retrieval beats memory. It does not isolate our harness's contribution when an ordinary search-enabled baseline can retrieve the same information.

Useful implementation precedents: [CRAG](https://arxiv.org/abs/2401.15884) evaluates retrieved-document quality and triggers corrective retrieval. [i-MedRAG](https://arxiv.org/abs/2408.00727) asks iterative follow-up questions and reports improvements on medical QA tasks. These motivate testable changes, not guaranteed improvements for our models. More searches or more reasoning are not automatically beneficial.

## Narrow task

Check what a named authority currently says about a specific public-health or regulatory claim, with an explicit date and jurisdiction. Begin with FDA labeling changes, approvals and recalls, plus CDC advisories. This supports a more auditable answer than broad personalized treatment advice.

Distinguish an authority's published position from universal scientific truth. A .gov domain alone does not establish applicability or currentness. Where competent authorities disagree, retain their names, dates and populations rather than force a consensus.

Examples of source-based development prompts, not measured model failures:

- A January 13, 2026 [FDA communication](https://www.fda.gov/drugs/drug-safety-communications/fda-requests-removal-suicidal-behavior-and-ideation-warning-glucagon-peptide-1-receptor-agonist-glp) requests removal of a warning from the labeling of named GLP-1 products. Test whether the model distinguishes the new request from older warnings, and a request from completed implementation.
- A September 1, 2026 [FDA notice](https://www.fda.gov/drugs/drug-safety-communications/fda-adds-boxed-warning-labeling-ferric-carboxymaltose-injection-injectafer-describe-risk-low) concerns Injectafer labeling. Test exact product identity and warning scope, not a blanket claim about all iron products.
- A recall question can require matching the product, lot code and date. FDA explains that [public warnings can precede enforcement classification](https://www.fda.gov/safety/enforcement-reports/enforcement-report-information-and-definitions); do not infer no recall from a missing classification or confuse classification date with announcement date.

## Proposed implementation change

Add source and date checks to the existing bounded recovery workflow:

1. Identify the factual requirements: product/entity, date, country, affected population, and exact action or recommendation.
2. Prefer applicable primary notices or guidance; record document date, effective date when available, publisher and supersession links from the actual page. Retrieval time is not publication time.
3. Assess whether each retrieved passage supplies the missing requirement. A keyword match, old official page or repeated headline is insufficient by itself.
4. Spend the remaining search allowance on the specific missing or conflicting requirement. If sources conflict, seek the relevant update and preserve unresolved differences.
5. Return a short answer with citations for each material assertion. Avoid extra uncited explanatory claims, which caused unresolved grades in the last run.

Test metadata checks and recovery separately. Do not add an uncontrolled extra judge, extra search budget and different evidence source pool only to the treatment. Ordinary retry should receive strong source/date instructions and access to the same tools; the experiment then tests whether executable enforcement and routing add value.

## Proposed data and comparison

Start with 40 cases across four equally sized categories: recent changes, exact population/product scope, outdated or conflicting sources, and false-premise or genuinely under-specified questions. Select recent notices using a predeclared date window (for example the preceding 90 days), not by checking which examples our method wins. Keep 20 development and 20 untouched evaluation cases, grouped by event, document family and source video so related versions cannot cross splits. Preserve authentic video wording when available; label authored/adapted claims separately. Converting benchmark QA into claims changes the task and cannot be reported as the original benchmark score.

For every case, record the as-of date, jurisdiction, authoritative source snapshot, exact supporting/refuting passage, answer and essential qualifiers. Freeze references before evaluation and obtain independent review of ambiguous or medical interpretations. Keep these reference materials hidden from candidates; tested models still choose their own queries and pages.

Use four arms: cheap model without search (diagnostic only), cheap model with strong ordinary search/retry, the same cheap model with source/date-aware recovery, and the selected stronger open-model reference with the same tools. Attribute harness gains to treatment versus ordinary search, not versus no-search. A future claim of beating a proprietary frontier model requires an actual contemporary comparison under matched access and budgets; existing papers do not establish that result for us.

Measure answer correctness against the frozen reference separately from citation entailment, source/date/scope correctness, decisive coverage, unsafe or wrong confident answers, and cost. Retrieval failure is an operational abstention, not a correct answer to an otherwise answerable question. Handle truly missing-context cases separately. Split core-verdict errors from unsupported extra explanation, calibrate the grader on separate examples, and keep unresolved assessments explicit.

The first useful success would be several independently checked semantic corrections on untouched cases where ordinary search completed but relied on stale, inapplicable or insufficient evidence. Fewer formatting failures alone would not establish the intended accuracy improvement.
