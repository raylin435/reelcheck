# Research a claim using model-selected evidence

`run_research.py` adds search → read → optional further search/read → verdict.
The tested Fireworks model decides the queries, pages and answer. It receives only
`claim_text` and `as_of`; a strict whitelist excludes evidence, source URLs, gold
labels and prior answers even if the input file contains them. The unchanged
fixed-packet runners remain useful controls.

## Run the pilot

From the repository root:

```sh
python3 scripts/run_research.py init --config config.research.json \
  --inputs data/research_pilot_claims.jsonl --out results/my-research
python3 scripts/run_research.py advance --out results/my-research --live
```

Initialization makes no API calls. `advance` makes at most one model call per active
case/model pair, reading the Fireworks key using the existing safe credential loader.
The initial pilot has six tasks, two searches and three reads per task, eight model
calls per task, and $2 candidate / $2 judge reservation caps. These conservative
reservations are not provider-enforced billing limits. See RESEARCH_PROTOCOL.md.

After `advance`, the web worker services `pending.json`. Repeat worker → advance
until every task is terminal, then:

```sh
python3 scripts/run_research.py judge --out results/my-research --live
python3 scripts/run_research.py report --out results/my-research
```

The judge sees the actual opened pages and answer, without model identity. It checks
meaning, source suitability, date/scope and whether the research supports the decision.
It does not use old fixed-packet verdicts: new evidence can change the right answer.
Results are model assessments, not human-reviewed factual accuracy.

## Web transport

This version uses Codex's connected web tool. No standalone search API key is
configured, so the Python runner needs a Codex tool worker (or an implementation of
the same bridge contract). It does not independently scrape a search engine.

`scripts/research_web_worker.js` supplies the worker. Run its `researchWebWorker`
function in the Codex functions execution environment, passing `tools`, `text`, the
absolute repository path and output directory. It runs independent requests in
parallel, then ingests responses sequentially. It uses exactly the model's query
or selected URL, without assistant rewriting, source selection or summaries.

Example in `functions.exec` after reading the local worker source:

```js
const worker = eval(source + '\nresearchWebWorker');
await worker(tools, text, repoPath, 'results/my-research');
```

Each pending request includes a generated `request_id`, `action`, and either `query`
with `max_results`, or `url` with `max_chars`. The worker executes one web search
query or opens the exact URL with `response_length: "long"`. Save a JSON response:

```json
{"request_id":"t000-s01","latency_s":1.2,"raw":"VERBATIM WEB TOOL RESPONSE"}
```

Then `run_research.py ingest --out RUN --response FILE` binds it to exactly one
pending request. Duplicate or mismatched responses fail. The normalizer takes the
first five search-result headings in order and bounded line-numbered read text.
Search snippets cannot be cited. Only successfully read passages receive R1/R2/etc.
Exact quotation matching and claim preservation use the existing contract validator.
Partial or empty page extraction remains visible; a successful read is not a source
quality guarantee. Read requests are limited to public HTTP(S) URLs discovered in
that candidate's search results. The web provider must also enforce network safety.

## Auditing and limits

The run saves all prompts, API responses, raw web responses, exact model-visible
extracted text, hashes, timestamps, tool failures, budget reservations and final
answers. File writes replace atomic snapshots. A local lock prevents overlapping
runner mutations. A persisted `in_flight` marker blocks automatic replay after a
crash; inspect the saved API response before manual recovery to avoid duplicate
billing. Read-only `report` does not make API calls.

Search/read prices are unavailable from this tool and remain **unknown**, not free.
Model service time and tool service time are reported separately. Bridge idle time
prevents interpreting this pilot's wall time as production latency. The reader can
return a partial page; HTML and PDF line formats are supported. There is no page pagination,
follow-link action, live transcript extraction, or deployed web interface.

Raw copyrighted pages stay in ignored `results/`; public code can include source
links and short result summaries. Never publish credentials or private run inputs.
