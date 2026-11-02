# Model-led evidence search pilot

Declared before candidate generation on November 2, 2026.

The candidate receives only the original claim and its as-of date. It does not
receive curated evidence, source URLs, previous answers, expected labels, or video
metadata. The tested model writes queries, selects discovered URLs, reads pages,
can search again, and produces a verdict with exact quotes from pages it opened.
Search snippets are discovery aids, never citable evidence. Web content is untrusted
data, never instructions. No operator edits candidate queries or chooses its pages.

Pilot: the existing video_sea_02, sf_01 and sf_02 claims, in that order, with GLM
5.3 Flash and DeepSeek V4.1 Flash. These are familiar development cases, not a
held-out benchmark. Their original claim wording is unchanged. Three cases do not
establish general factual accuracy. Both systems use identical JSON-object action
instructions, up to 2 searches, 3 page reads, 5 results/search, 16,000 characters/read,
and 8 model calls/case including the final answer. No automatic model retries or
answer repair. The final allowed call must answer. Invalid actions end that case.
Alternate model order across cases. Retain failures and abstentions in denominators.
Candidate reservations are capped at $2 for the whole six-run pilot; judging at $2.
Model token rates are copied from the existing same-day verified configurations.

The search/read transport is a file bridge to Codex's web tool, with a documented
JSON worker contract. The model makes every research decision; the worker executes
its exact requests. There is no standalone search-provider credential configured.
This pilot therefore needs a Codex web worker, or another conforming external tool
worker. Search uses one query per call with a long response. Read uses the exact
model-selected URL with a long response. Normalization is deterministic; raw web
responses, timestamps, hashes and tool errors are saved locally. The web tool may
return only part of a page; bounded extracted text is not the original page bytes.

All candidate API calls and tool operations are logged. Record model-service time,
tool-service time, and wall time separately; operator/bridge idle time makes wall
time unsuitable for product-latency comparisons. Web-tool monetary cost is unknown,
not zero. API costs are usage-based estimates, not invoice reconciliation. Interrupted
API requests are never automatically repeated; their cost remains unknown.

Evaluation uses Kimi K3 identity-blind on each candidate's actual retrieved passages,
not the old fixed-packet labels. A new valid source can legitimately change a verdict.
The judge also assesses source suitability, date/scope matching and whether research
was sufficient for the decision. A separate judge does not establish truth or search
completeness. Exact quotes and opened-source IDs are checked deterministically;
semantic acceptance remains a fallible machine assessment. No human accuracy score.
Report paired outcomes descriptively, all failures, cited domains, search/read
counts, cost, and at least one complete query → page → verdict trace.
