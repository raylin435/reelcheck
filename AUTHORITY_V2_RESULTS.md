# Authority v2.1: larger comparison

The held-out test does **not establish a factual-accuracy improvement** from the authority harness. Ordinary GLM retry and targeted GLM recovery each match 18 of 19 settled reference keys, with one failed execution and one additional unresolved key among all 20 cases. There are no paired semantic wins. The harness improves compliance with the declared source/date rules, but that is a different measurement.

## What changed

Every arm now selects numbered evidence spans; the controller copies the original claim and renders exactly the selected passages. The model still finds its own evidence, chooses its citations and decides its answer. This removes copying as a reasoning burden equally for every arm. It does not guarantee schema compliance or factual correctness: missing metadata fields, wrong citation structure and truncation remain recorded failures.

All 40 answer keys received two blind reviews using freshly opened FDA/CDC pages. All 80 reviews completed and agreed with the original verdict labels. Twenty-one reviewer quotations were not verbatim; their original reviews are preserved alongside separate exact-span anchoring attempts. No verdict labels changed. One key (`authority_06_2`, an unnamed manufacturer's completed label change) remains unresolved because the missing-context versus missing-evidence distinction is not uniquely established. The other 39 keys have machine consensus, not human clinical validation. References were frozen before candidate inference and never supplied to tested models.

## Final answers

Counts below retain every planned case. A match requires the reference verdict and, for an insufficient answer, its required reason. Failures are not dropped. Each held-out arm also has one unresolved reference, which is neither correct nor incorrect.

| System | Development matches / 20 | Development completed / 20 | Held-out matches / 20 | Held-out completed / 20 |
|---|---:|---:|---:|---:|
| GLM without search | 6 | 16 | 8 + 1 unresolved | 17 |
| GLM ordinary retry | 18 | 19 | 18 + 1 unresolved | 19 |
| GLM authority recovery | 19 | 20 | 18 + 1 unresolved | 19 |
| DeepSeek reference | 20 | 20 | 18 + 1 unresolved | 19 |
| GLM metadata-only control | 19 | 19 | Not run | Not run |

Development has one treatment win caused by ordinary retry omitting `evidence_checks`; the 19 pairs where both completed are all reference-score ties. Both cheap arms make the same substantive mistake on `authority_11_2`: they assume an unnamed child's patch is Transderm Scop. The authority answer passes metadata checks but both grounding judges reject that assumption. DeepSeek correctly asks for the missing product context.

Held-out comparison has 19 reference-score ties and one unresolved pair. Among both-completed pairs, 18 are ties and one is unresolved. Both cheap arms fail `authority_18_1` by returning citations in the wrong structure; DeepSeek fails `authority_01_1` by omitting the metadata list. These failures remain in the released record; no selective reruns or post-hoc repairs were scored. There are **zero targeted follow-up searches** in either partition: this experiment has not demonstrated that the targeted search mechanism improves answers.

Only four cases in each partition concern notices from the previous 90 days. Ordinary retry and authority recovery both match all four in each partition; DeepSeek matches 4/4 development and 3/4 held-out (one format failure). This small subset does not establish frontier-model weakness on very recent knowledge.

## Independent grounding and metadata checks

Every completed researched answer received two grading attempts: 156 development and 114 held-out calls. No failed judge was silently rerun. These assessments evaluate evidence support separately from reference-label matching.

| System | Development accepted / rejected / unresolved | Held-out accepted / rejected / unresolved | Held-out metadata passes / completed |
|---|---:|---:|---:|
| Ordinary retry | 18 / 0 / 1 | 18 / 0 / 1 | 17 / 19 |
| Authority recovery | 19 / 1 / 0 | 17 / 0 / 2 | 19 / 19 |
| DeepSeek reference | 19 / 0 / 1 | 19 / 0 / 0 | 17 / 19 |
| Metadata-only | 19 / 0 / 0 | Not run | Not run |

Grounding counts above cover completed answers only; execution failures are listed in the first table. The three unresolved held-out assessments are two truncated DeepSeek judge responses and one Kimi response containing an extra `_note` field rejected by the frozen strict rubric. They are not demonstrated semantic losses. The unresolved reference (`authority_06_2`) remains unresolved even when grounding judges accept a candidate's answer; the two metrics answer different questions. Passing a metadata gate alone does not establish truth, and the harness shows no accepted-grounding advantage here either.

## Estimated model cost

| Component | Estimated USD |
|---|---:|
| Blind reference reviews | $0.678129 |
| Reviewer citation anchoring | $0.214613 |
| Aborted development, including original initial drafts | $0.254476 |
| Corrected development, newly paid candidate calls | $0.094265 |
| Held-out candidate calls | $0.249348 |
| Development grounding | $1.422048 |
| Held-out grounding | $1.197675 |
| Total for this review and larger comparison | **$4.110554** |

These are token-based estimates using the recorded configuration, not invoice reconciliation; web-tool costs are unknown. The corrected development workflow includes $0.115519 of inherited initial calls already counted in the aborted attempt, so only its new calls are added above. Each arm's deployment-attributed cost includes its own initial draft, while actual experiment billing deduplicates shared drafts. Earlier v1 canary and historical experiments are excluded from this total.

## Integrity and execution

The first full development attempt revealed a controller date-parser bug: it rejected CDC's `Sept.` abbreviation. That experiment was stopped before grading and preserved as an invalid controller run. The correction affects date recognition only. All original memory and initial-research attempts, including failures, were reused unchanged; every recovery branch was rerun under v2.1. The corrected prompts, models, reference files and inference runtime were frozen identically across development and held-out evaluation.

At the user's request during held-out execution, a separate executor increased scheduling concurrency to 12 independent candidate calls. It journals requests and reserves their budgets before dispatch, serializes state updates, preserves per-task ordering, and records its own immutable hash and per-shard scheduling addenda. The prompts, scoring and allowances stayed fixed. Grading runs four shards in parallel, two requests per shard. Elapsed experiment latency is not a controlled comparison across this scheduling change.

The 40 cases come from 20 document families, split by family into 20 development and 20 held-out cases. There are 180 final arm attempts (100 development, 80 held-out). Shared initial drafts, tool observations, output rendering, original claim preservation, budget limits and complete call journals are audited. All eight shard audits pass. All 131 Python tests and the JavaScript web-worker persistence test pass.

## Interpretation and next experiment

The harness enforces source/date checks; it still needs evidence that these checks improve decisions. For example, its issuer rule excludes FDA-distributed GovDelivery pages because their host is not fda.gov, and its date rule excludes later documents even when they describe earlier events. A metadata failure therefore is not automatically a factual mistake. Conversely, a well-dated official source does not establish an unnamed person's product or an unspecified manufacturer's actions.

The next experiment should target these observed gaps: use independently reviewed cases requiring identification of missing context, resolving genuinely conflicting official updates, and finding a second source. Freeze the expected evidence requirements before testing; then compare ordinary retry against an explicit evidence-sufficiency check with equal tools and budgets. Keep this completed held-out result unchanged and use new document families for the next test.

This is a small AI-authored FDA/CDC claim benchmark, not a clinical-advice evaluation, an end-to-end video benchmark, or a comparison against proprietary frontier models. Two machine judges can share errors; the DeepSeek judge shares a family with the reference model. Neither reference matching nor judge acceptance establishes human-verified accuracy.

## Records

- [Frozen protocol](AUTHORITY_V2_PROTOCOL.md), [implementation and reproduction](AUTHORITY_V2.md), [reviewed dataset manifest](data/authority_v2/manifest.json).
- [Development summary](data/releases/authority-v21-development/summary.json) and [all traces](data/releases/authority-v21-development/traces.json).
- [Held-out summary](data/releases/authority-v21-heldout/summary.json) and [all traces](data/releases/authority-v21-heldout/traces.json).
- [Blind reference reviews and anchoring](data/releases/authority-reference-review-v2), [aborted controller attempt](data/releases/authority-v2-controller-abort).

The earlier four-case authority canary and older recovery experiments remain separate historical results.
