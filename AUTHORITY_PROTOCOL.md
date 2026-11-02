# Dated authority experiment v1

Frozen before candidate inference, November 2, 2026. This is an authored claim-verification stress test, not medical advice, authentic video evaluation, or an official benchmark score.

## Data

40 claims from 20 FDA/CDC document families. Selection window: January 1, 2025–November 2, 2026. Only eight claims concern notices within the preceding 90 days; report them separately. The wider window provides earlier statements, scope traps, and changed guidance. All claims explicitly concern a named, dated notice. This tests retrieval of recent documents and interpretation of dated statements, not general clinical accuracy or proof that these facts are absent from model training.

20 development and 20 held-out cases; each has five cases in each of four categories, four cases within 90 days, and two missing-context cases. Related statements and updates stay within one family and split. The deterministic group selection rule and file hashes are in `data/authority_v1/manifest.json`. References are AI-authored drafts with exact source excerpts, source snapshot hashes, retrieval dates and explicit review status. No human has reviewed them. Do not describe label matching as verified accuracy.

Candidate initialization reads only the selected claim file, then whitelists claim text and as-of date. It never sends source URLs, references, categories, expected verdicts or excerpts to candidates. The models select every query and opened URL themselves. The runner has no candidate filesystem tool. Reference files are available only to review/report commands after inference.

## Comparison

1. GLM memory-only: one call, no evidence; diagnostic only.
2. GLM ordinary search/retry: strong source/date/scope instructions.
3. Same GLM shared draft plus enforced metadata and targeted gap recovery.
4. DeepSeek open-model reference: the same research allowances and instructions.
5. Development-only ablation: same GLM shared draft with metadata enforcement and ordinary retry, isolating targeted search routing from enforcement. Do not claim a causal component advantage without completed paired semantic improvements.

Research starts with at most one search, two reads and five model calls. Each recovery fork receives one additional search, two reads and five calls from the identical draft/history. Every arm returns the same answer and metadata schema. A metadata rejection consumes a call and uses the existing remaining budget; no hidden extra model or search is granted. The ordinary/reference arms record the same mechanical audit without enforcing it. No-search is not used to attribute harness gains.

Checks enforce FDA/CDC HTTPS issuer matching, exact metadata quotations, a rendered document date no later than the claim date, and coverage of cited passages. They do NOT verify semantic scope, that a date is the publication date, exhaustiveness, currentness, or the truth of an authority's statement. Unknown dates cannot silently become today's date. Effective dates and document dates are distinct. Supersession remains an explicit, unverified model assessment. Failed validation is an execution failure, not a correct abstention.

## Staging and measurement

Run a four-case development canary (first development case in each category, before observing outputs), including the metadata-only ablation. Preserve all attempts. Do not run or tune on held-out cases during canary development. A full evaluation follows independent reference review and canary inspection; a canary is not evidence of aggregate improvement. The held-out set stays unused in this implementation release.

Reference-label match, wrong decisive answers, operational abstentions, completion, metadata audit and source-grounding assessments are separate. A candidate that cannot retrieve an answerable fact does not receive credit for a correct insufficient verdict. Missing-context cases require that reason, not generic failed retrieval. Exact-quote validity and metadata checks do not establish entailment. Identity-blind machine grounding assessments remain provisional, including disagreement and failure; no human-verified accuracy is reported.

The two independent reference reviewers see the claim and frozen excerpt and can flag ambiguity, incorrect labels or inadequate source context. Neither review rewrites the reference or drops a case. Unreviewed/disputed cases remain explicitly provisional. Paid calls have persisted reservations and journals; no silent retries. Unknown provider/web cost remains unknown. Shared draft calls are counted once in experiment billing and attributed to each deployable arm separately.

## Promotion criterion

Before a final run, resolve disputed references independently and freeze a new reviewed manifest without using held-out candidate outputs. The intended evidence is semantic correction on completed matched pairs, with no increase in wrong confident answers and reported costs. Formatting recovery, a small canary, or beating a no-search model alone does not establish that the harness improves accuracy.
