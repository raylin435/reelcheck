# Evidence recovery: completed comparison

**Targeted recovery works as an executable research workflow, but this experiment does not establish better factual quality than ordinary retry.** On 20 fresh transcript-derived claims, all three approaches received two-judge acceptance on 15/20 cases. Targeted recovery produced fewer invalid final attempts and used slightly less estimated model spend, but had more unresolved assessments. These are descriptive pilot results, not accuracy or statistical-equivalence claims.

Open the [20-claim recorded replay](data/releases/recovery-fresh-01/demo.html) to inspect all 60 attempts, or the [development replay](data/releases/recovery-dev-01/demo.html) for the supplement example. Both run locally and are explicitly labeled recorded; neither is a deployed live checker.

## What was implemented

The tested model supplies the evidence itself: it writes search queries, chooses discovered URLs, reads pages, and cites exact text from opened pages. The controller supplies the claim and date, tool access and limits. It does not supply the correct answer or a curated evidence packet.

GLM 5.3 Flash makes one initial research draft. The exact same draft and history fork into ordinary retry and targeted recovery. Both get one additional search, two reads and five model calls. The targeted branch must name a specific missing fact when it searches. DeepSeek V4.1 Flash with high reasoning researches separately using the same two-phase allowances. This is an open-model reference, not an organizer-certified proprietary frontier baseline.

The revised two-judge rubric passed all 16 predeclared synthetic checks (eight cases × Kimi/DeepSeek). Both judges also rejected the previously disputed answer that treated a contamination warning as proof of an observed positive drug test. Historical scores remain unchanged. Calibration tests specific logical distinctions; it does not certify evaluator accuracy on arbitrary claims.

## Frozen fresh evaluation

| Approach | Both judges accept | Unresolved | Execution failures | Decisive answers | Model estimate, 20 cases | Model estimate / accepted answer |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM ordinary retry | 15/20 | 2 | 3 | 17 | $0.08478 | $0.00565 |
| GLM targeted recovery | 15/20 | 4 | 1 | 19 | $0.07836 | $0.00522 |
| DeepSeek reference | 15/20 | 4 | 1 | 18 | $0.14860 | $0.00991 |

Failures and unresolved cases stay in the 20-case denominator. All 55 structurally valid answers received two assessment attempts. No valid answer was rejected by both judges; this is not evidence that none was wrong. There were 54 supported answers, one insufficient answer and no contradicted answers. The reference's single abstention remained unresolved, so the experiment does not establish justified-abstention performance or false-claim detection.

Targeted versus ordinary retry: **2 wins, 0 losses, 13 ties, 5 unresolved pairs** under the frozen consensus rule. Both wins were against invalid ordinary-retry executions: an undiscovered read URL on `fresh_08`, and an invalid finish action on `fresh_17`. Both cheap arms truncated on `fresh_09`. Among the 17 pairs where both completed, there were **12 ties and 5 unresolved pairs, with no resolved semantic win**. The same accepted total despite two wins reflects cases where one arm is accepted and the other unresolved; unresolved is not counted as a loss.

Targeted recovery used 22 searches and 30 reads, versus 23 and 37 for ordinary retry, including each arm's initial history. Its estimated model spend was 7.6% lower than ordinary retry and 47.3% lower than the DeepSeek reference. These are observed token-cost differences, not proven total-cost savings or quality equivalence. Only **2/20 targeted branches actually issued a follow-up search**, so this fresh set provides little coverage of the proposed search mechanism. One searched for the exact juniper/pine species; the other searched for bighorn-sheep habitat and still truncated.

## What remains uncertain

The fresh set contains 20 AI-paraphrased claims from seven public NPS/NOAA video transcript pages, grouped into four creator/series groups and two publisher institutions. These are new claims and clips for this experiment, but institutional/source overlap remains. The set was chosen for readable factual transcripts, not randomly sampled or balanced by truth label. It is not 20 independent videos and is not a broad creator-held-out benchmark.

This evaluates the retrieval/verdict component. Audio, frames, caption alignment and portrait/native short-form admission were not verified. Two NOAA video durations remain unverified; publisher download formats are landscape. No video assets were copied into a distributable dataset. [Claim provenance](data/recovery_fresh_claims.jsonl) records each source and transcript location. The [fresh protocol](RECOVERY_FRESH_PROTOCOL.md) disclosed these limits before inference.

Ten arm/case assessments stayed unresolved: five DeepSeek judge truncations, one malformed Kimi assessment, and four judge disagreements. Disagreements concern extra explanatory assertions or bounded-search wording even when the central verdict has support. For example, one judge rejected the unbounded phrase “no conflicting evidence exists,” while the other tolerated it; another treated the bounded phrase “No conflicting evidence was found” as an exhaustiveness claim. The calibrated judges still apply some rules inconsistently. Their frozen scores were not overwritten. One judge also shares the reference model's family.

The two targeted disagreements on `fresh_06` and `fresh_13` flag unnecessary assertions beyond the opened evidence. Those remain useful failure examples. Passing exact-quote checks does not guarantee that the whole explanation is grounded.

## Development result and concrete recovery

On the three familiar development claims, ordinary retry had 1 accepted answer and 2 execution failures; targeted recovery had 2 accepted and 1 unresolved; the reference had 3 accepted. The target's two wins were against a truncated response and an API transport timeout, not resolved semantic baseline errors.

The useful development example is `sf_02`: the model identified that contamination risk did not establish an actual positive test, searched for a documented athlete case, and read an article carrying USADA's Jessica Hardy announcement and the arbitration finding. It cited the observed test and disclosed the manufacturer's dispute of the contamination finding. Both judges accepted it. This demonstrates the intended recovery behavior; the selected example alone does not prove aggregate improvement.

## Accounting and integrity

Fresh evaluation: **230 unique candidate API calls, estimated $0.27220; 110 judge calls, $1.34078; combined $1.61298**, excluding unknown web charges. There were 47 distinct search actions and 83 distinct read actions. Per-arm estimates in the table include a starting draft for each deployed workflow; actual billing counts the shared GLM draft only once. Do not sum per-arm costs as the experiment bill.

Calibration cost $0.07099 and the disputed-answer audit $0.05341. Development candidate calls have a known subtotal of $0.06877 plus one timeout with unknown cost; development judging cost $0.30127. Across these new experiments, the known API estimate is **$2.10743 plus the unknown timeout and web charges**. Estimates use response usage and same-day configured token rates, not reconciled invoices.

The development web handoff had a lock collision: one saved response was reused and two unsaved page responses were reacquired. No model attempt was rerun. Its unknown web/latency overhead is documented in [the incident record](data/releases/recovery-dev-01/worker-incident.json). The replacement worker persists every response before ingestion and checks the runner lock; fresh evaluation used that worker throughout. Model-service durations exclude operator/bridge idle time and are not product latency.

Read-only integrity audits passed for all five runs: frozen sources, no pending/in-flight requests, identical forked drafts/history, matched remaining allowances, call-journal reconciliation, exact quote validation and two assessment attempts for every valid answer. All **108 Python tests** passed; the web worker's mocked persistence/resume check also passed. [Fresh audit](data/releases/recovery-fresh-01/integrity-audit.json), [machine-readable results](data/releases/recovery-fresh-01/summary.json), and per-shard `REPORT.md` files retain all outcomes.

## Decision

Keep targeted recovery as an inspectable experimental option. Keep ordinary research/retry as the quality baseline. The defensible hackathon claim is a working, model-led evidence checker with bounded recovery and transparent evaluation, with fewer execution failures and slightly lower model spend observed in this pilot. Do not claim improved factual accuracy or frontier equivalence.

The next quality experiment should start with independent review of the unresolved cases and a new set that actually requires evidence recovery, including unsupported or conflicting authentic claims. Define the scoring decisions before running it. Do not tune or rerun this frozen set until it produces a favorable result.

Reproduction and local worker instructions: [RECOVERY.md](RECOVERY.md). Original pre-run design: [RECOVERY_PROTOCOL.md](RECOVERY_PROTOCOL.md). No deployment, public publication, submission or external messages were performed.
