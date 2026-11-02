# Automated review and semantic-check results

The automated pilot completed without human review. **The extra verification pass
did not improve results:** it had zero paired acceptance wins and one regression.
Keep the schema baseline for now. This run does not support an improvement claim.

| Partition | Reference coverage | Baseline accepted / resolved | Extra pass accepted / resolved | Accepted / all, baseline → extra pass |
| --- | ---: | ---: | ---: | ---: |
| New clips: 9 claims, 3 videos | 8/9 | 8/8 | 7/8 | 8/9 → 7/9 |
| Previously tested development: 6 claims, 3 videos | 5/6 | 4/5 | 4/5 | 4/6 → 4/6 |
| Combined | 13/15 | 12/13 | 11/13 | 12/15 → 11/15 |

These are LLM assessments against frozen machine references, not human-verified
accuracy. Both systems produced 15/15 valid outputs. Reference-verdict agreement
matches the acceptance counts above. `sf_05` and `new_07` remain unresolved and are
included in all-case denominators. Neither system emitted a wrong decisive answer
on the resolved new cases; both retained one on the old development cases.

## What failed

- **Persistent overclaim (`sf_02`).** Both systems inferred documented positive
  drug tests from evidence that undeclared substances could cause a positive test.
  The second pass repeated the possibility-versus-observation error despite its
  explicit checklist and requirement mapping. Quote validity did not prevent it.
- **New regression (`new_02`).** The baseline correctly combined a report page's
  date context with its count of 12 individuals. The extra pass treated the date
  as missing because the count's sentence did not repeat it. The judge rejected
  this unnecessary abstention against the pre-frozen reference.
- **Arithmetic check passed (`new_03`).** Both systems detected that the displayed
  percentage did not follow from the chart's numerator and denominator. This is
  a real clip error, but it did not distinguish the two systems.

The baseline passed every resolved claim from the three new clips. That set is
therefore not yet difficult enough to demonstrate a stronger verification method.
The next experiment should expand creators and topics, with authentic temporal,
scope and conflicting-source cases. Reserve untouched clip/creator groups before
tuning. Keep failure discovery and final evaluation separate.

## Cost and latency

| Component | Calls | Estimated USD |
| --- | ---: | ---: |
| Claim fidelity, captions + sampled frames | 3 | 0.003832 |
| Reference panel, including superseded votes | 35 | 0.191686 |
| Candidate generation, shared baseline counted once | 30 | 0.018630 |
| Kimi high-reasoning grading | 26 | 0.279948 |
| Total | 94 | **0.494095** |

Across 15 cases, baseline deployment cost was $0.006574 with median latency 2.15 s;
the two-pass workflow cost $0.018630 with median latency 6.07 s. The extra pass cost
about 2.8 times as much and did not improve acceptance. Its cost and latency include
both calls. Do not add baseline deployment cost again to the experiment total.
Prices and usage are recorded estimates, not reconciled billing.

## Reproducibility and limits

Kimi K3 and DeepSeek assessed references independently with high reasoning effort;
GLM supplied a third vote only when needed. Any explicit material scope ambiguity
stayed unresolved. Kimi also graded answers against those references, so its grades
are not independent validation of the panel. Candidate identities were hidden.
No favorable model retries or post-generation label changes were used.

One source-summary omission was corrected before candidate generation. Only that
case was reassessed; unchanged exact-case votes were reused. The merged references
were frozen before all 30 generation calls. Superseded inputs, votes and costs are
retained. Old cases received fresh machine references, so their scores should not
be compared directly with historical reports using different reference labels.

The new data contains nine claims from three 54–127-second portrait videos. All
passed downloaded-byte checks and automated claim-fidelity review. The broader
15-claim export contains six clips. All come from the DVIDS government publishing
ecosystem, and one new creator overlaps development. Native social publication is
unverified. This evaluates supplied claims and evidence summaries, not end-to-end
video understanding, independent audio transcription or live retrieval. Two source
pages were retrieved through indexed primary-page text after direct HTTP 403 errors;
source provenance distinguishes those records from original PDF/HTML snapshots.

Validation: **86 tests passed**, including unresolved-reference handling, exact
evidence-only reuse, blinded prompts and two-stage cost accounting. All 30 archived
media/caption/metadata files and the exported artifact hashes were verified.

The [portable dataset and audit trail](data/releases/machine-pilot-01/README.md)
contains inputs, references, results, raw votes, candidate responses, judgments,
source records, rights and checksums. The [detailed report](data/releases/machine-pilot-01/REPORT.md)
preserves every case. See [dataset methods](MACHINE_DATASET.md) and the unchanged
[pre-run protocol](MACHINE_EVAL_PROTOCOL.md). The media archive is local at
`results/machine-pilot-01-media.zip` (265.8 MB); nothing has been uploaded or published.
