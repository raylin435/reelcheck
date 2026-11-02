# Model-led search and verification: live development trial

The new search → read → answer loop ran against real web results and Fireworks
models. Candidates received only claim text and date. They chose every search query
and page themselves; the worker executed those choices without supplying curated
evidence or expected answers. This establishes working retrieval integration, not
better factual accuracy or a model ranking.

## Original six-attempt pilot

Three familiar development claims were tested with GLM 5.3 Flash and DeepSeek V4.1
Flash, under identical limits. Kimi K3 judged the five structurally valid answers
against their actual opened pages without candidate identity.

| System | Structurally valid answers | Accepted by machine judge | Other outcomes |
| --- | --- | --- | --- |
| GLM | 3/3 | 2/3 | One judge rejection |
| DeepSeek | 2/3 | 0/3 | Two judge rejections; one request beyond the read budget |

These fractions are not accuracy estimates. The dataset is tiny, familiar, and
correlated; retrieval order and failures vary. One PDF extraction bug affected
DeepSeek's sf_01 path. Do not use this run to claim GLM superiority.

The pilot made **29 candidate calls** (estimated **$0.02211431**) and **5 judge
calls** (**$0.220845**), for **$0.24295931** in usage-based model API estimates.
Web-tool cost is unavailable and is not treated as zero. There were 8 searches,
15 page-read attempts, and 8 reads returning some extracted text. Two of those
returned only a PubMed footer; successful transport is not usable evidence.

## What happened

- **Independent evidence discovery worked.** For sf_01, GLM searched for weekly
  military supplement use, chose the primary study on PMC, and cited its 74% result
  as support for approximately 75%. The primary-study URL was not in its initial
  input. DeepSeek later found that study in the separate follow-up as well.
- **Both climate paths recovered from a blocked PDF.** Both first selected an IPCC
  PDF, encountered a 403, and chose a NASA page. They then searched again for more
  precise evidence. Their additional IPCC reads failed. Both still answered
  supported, while the judge rejected their use of NASA's approximate 90% wording
  to establish the stricter more-than-90% claim. This is a packet-specific semantic
  assessment, not evidence that the underlying real-world claim is false.
- **The read budget is enforced.** DeepSeek requested a fourth page on sf_02 after
  using its three reads. The runner rejected it and retained the failed attempt.
- **The judge can make mistakes too.** The judge accepted GLM's sf_02 answer, but a
  subsequent Codex audit flags that acceptance: the cited USADA passages document
  contamination and a risk of positive tests, not an observed positive test caused
  by supplement use. The judge's rationale bridges that same possibility/occurrence
  gap. Preserve its recorded acceptance, but treat this case as disputed, not a
  verified success. No human or independent adjudication has resolved it.

The full local trace is `results/research-pilot-01/REPORT.md`, with raw requests,
web results, model responses, prompts, source snapshots and hashes beside it.

## Reader correction and follow-up

The first reader recognized HTML lines such as `L12:` but not PDF lines such as
`L12@P0:` or an empty PDF title. The NIH ODS PDF was actually returned by the web
tool and was incorrectly classified as unreadable. The parser now supports both
formats. Replaying that exact saved response produces 7,523 characters of extracted
text. This is a parser regression check, not a new model result, and does not alter
any original answer or score.

A fresh, separately reported two-model run on sf_01 tests the updated implementation.
It was selected after observing the bug and is a development follow-up, not held-out
evidence. Both models chose the primary PMC study this time, so live HTML reading
was exercised; the PDF-specific correction is verified by the captured-response
replay and unit test. Follow-up details are recorded in
`results/research-reader-check-01/REPORT.md`.

In that follow-up, DeepSeek returned a valid answer accepted by the judge. GLM's
answer failed exact-quote validation; it also used search-snippet information in
its explanation without opening those additional sources. The runner retained the
failure and did not repair or retry it. The two runs must not be pooled into a
model-ranking claim.

The follow-up used 7 candidate calls (**$0.005331658**) and one judge call
(**$0.024432**). Across the original pilot and follow-up there were **8 research
attempts**, **36 candidate API calls**, **6 judge API calls**, and **$0.272722968**
in estimated model charges. Web-tool charges remain unknown. Six answers passed
structural checks and two failed; the judge accepted three of the six valid answers,
including the disputed sf_02 acceptance described above. These are operational and
machine-assessment counts, not verified accuracy.

## Scope

The Python runner uses a file bridge to Codex's web tool. A configured web worker is
required; it is not yet a standalone web-search service. Search snippets are never
citable passages. Pages may be partial or blocked; no pagination or link-following
tool is implemented. Search/read limits, exact quotes, source IDs, preservation of
the original claim, spend reservations, identity-blind judging, interrupted-call
tracking and input isolation are tested. The full local suite passes 100 tests.

The existing fixed-packet labels were not used to score this experiment: new
retrieved sources can legitimately change the answer. Candidate API time and web
tool time are recorded separately; bridge idle time prevents production-latency
claims. No live video transcription, deployment, or general reliability claim is
included.
