# Authority development canary

The source/date checks work as an executable, bounded workflow. This four-case canary does **not** demonstrate a factual-accuracy improvement from targeted recovery. It exposed output-format failures and another unnecessary explanatory overclaim. The 20-case holdout remains unused.

## What ran

Four development cases selected before inference: the first case in each category under the frozen input order. They concern three FDA notices (two alli claims, one Tavneos claim, one opioid-labeling claim). None is within 90 days of the evaluation date, and no CDC case entered this small canary. It is an integration test, not the full freshness or authority benchmark.

Two independent model reviewers accepted all four reference labels (8/8 assessments). They reviewed the frozen excerpts and metadata, not a new live verification of every source. No human review took place. The other 36 draft references remain independently unreviewed in this release.

The cheap model's research draft and evidence history were cloned into ordinary retry, enforced metadata with targeted recovery, and enforced metadata with ordinary retry. Each had the same additional search, read and model-call limits. The separate DeepSeek reference had equivalent research allowances. Memory-only GLM is a diagnostic, not a harness comparator.

## Observed results

All denominators retain four cases. Label matching uses provisional references; grounding uses the model's actual retrieved pages and two identity-blind model assessments.

| Arm | Structurally completed | Reference-label matches | Both grounding judges accept | Completed but grounding unresolved | Execution failures |
| --- | ---: | ---: | ---: | ---: | ---: |
| GLM memory only | 4 | 1 | Not assessed | Not assessed | 0 |
| GLM ordinary retry | 2 | 2 | 2 | 0 | 2 |
| GLM authority recovery | 3 | 3 | 2 | 1 | 1 |
| GLM metadata enforcement + ordinary retry | 4 | 4 | 4 | 0 | 0 |
| DeepSeek reference | 3 | 3 | 3 | 0 | 1 |

The memory-only model abstained on three answerable claims. All four initial cheap research drafts were structurally valid and matched the reference label before review. Final structural failures involved exact quotation or original-claim reproduction. The treatment's two gains over ordinary retry were against those structural failures; its failure on the Tavneos case was an unchanged-claim contract error. These are not demonstrated semantic corrections. The metadata-only result is four development observations, not proof of superiority.

On the opioid claim, both graders agreed that the treatment's contradicted verdict was supported. One rejected its extra statement that the page showed no later reversal; the other accepted the whole answer. That assessment stays unresolved. Passing metadata checks does not establish the correctness of additional explanation.

**Zero of four targeted branches issued a follow-up search.** They already had useful FDA evidence. This canary validates mechanical enforcement and repair, but it does not exercise a successful live targeted-search correction. The stronger reference is an open-model comparison, not evidence about today's best proprietary frontier model.

## Integrity and cost

The read-only audit passed: frozen source snapshots, no active or pending candidates, no in-flight request, equal shared histories and remaining budgets, exact-quote validation for completed researched answers, and reconciliation of all 51 unique candidate calls. Each of 12 valid researched final answers received both grounding assessments. All provider costs were known for this run; web cost is unavailable.

- 51 candidate calls: estimated $0.069320346.
- Eight independent reference-review calls: $0.035212800.
- 24 grounding-assessment calls: $0.218686272.
- Total: **83 calls, estimated $0.323219418**, plus unknown web billing. Eight searches and ten page reads.

[Portable results and traces](data/releases/authority-canary-01/README.md) retain failures, judgments, metadata checks, source hashes and selected queries/URLs. [Machine-readable summary](data/releases/authority-canary-01/summary.json). The summary's `metadata_pass` counts the last metadata audit even when another output-contract check failed; it is not a count of valid final answers. Likewise, raw `grounding_unresolved` includes unassessed failures and the no-search diagnostic; the table above separates those from disagreement on completed answers.

All 122 Python tests and the mocked web-worker persistence/resume check passed. The live worker successfully persisted and ingested the candidate-selected searches and reads. The original recovery experiments were preserved unchanged; publication includes their small summaries and recorded demos.

## Next decision

Do not spend the holdout yet. First remove avoidable claim-copy/reader-markup failures with a deterministic output boundary applied identically to all research arms; preserve this run rather than relabeling it after a change. Independently review the remaining reference drafts, and run the full development set with scope, stale-source and missing-context cases. Use those results to decide whether targeted search is exercised and useful before freezing the final comparison. This is the next validation stage, not a claim that the current harness has already improved accuracy.
