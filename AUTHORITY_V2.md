# Larger authority comparison with equal output rendering

The [completed comparison and limitations](AUTHORITY_V2_RESULTS.md) report all 40 cases, including failures and one unresolved reference. Portable records: [development](data/releases/authority-v21-development), [held-out](data/releases/authority-v21-heldout), [blind reference review](data/releases/authority-reference-review-v2), and [aborted controller experiment](data/releases/authority-v2-controller-abort).

V2 removes claim-copy and quotation-copy tasks from every model arm. Models select numbered passages from pages they found themselves; the controller renders the selected text and preserves the input claim. It does not pick the evidence, decide the verdict, invent a date, or add facts. Unknown spans remain errors. This fixes avoidable serialization failures without awarding the treatment an exclusive formatting advantage.

The [frozen protocol](AUTHORITY_V2_PROTOCOL.md) defines a 20-case development comparison and then a 20-case held-out comparison with unchanged prompts, model settings, code and references. The [reviewed manifest](data/authority_v2/manifest.json) records 39 machine-consensus keys and one explicitly unresolved key. Neither model reviewers nor tested candidates receive proposed labels during their respective blind tasks. Candidates never receive reference materials at all.

The initial four-case trial and historical recovery experiments remain unchanged. V2 is a new experiment; old failures are not relabeled as successful after the code fix. Reference review uses full official pages and preserves separately recorded repairs for reviewer quotations that were not verbatim. All source acquisition and model requests remain journaled locally; the release carries summaries and relevant traces rather than full raw web caches.

Reproduction uses the existing Fireworks configuration/key-loading conventions and the Codex web bridge:

```sh
python3 -m unittest discover -s tests -q
python3 scripts/run_authority_v2.py init --partition development --shards 4 --shard 0 --out results/new-development/shard-0
python3 scripts/run_authority_v2.py advance --out results/new-development/shard-0 --live
```

Run `authorityV2WebWorker(tools, report, cwd, out)` from `scripts/authority_v2_web_worker.js` between completed advance passes. The worker executes the exact candidate-chosen query or URL; it does not provide reference pages or compose queries. Repeat independently for shards 0–3. Never run a worker during an advance command, and never silently repeat a failed provider call.

```sh
python3 scripts/audit_authority_v2.py --out results/new-development/shard-0
python3 scripts/run_authority_v2.py judge --out results/new-development/shard-0 --live
python3 scripts/aggregate_authority_v2.py --run results/new-development
```

The held-out partition uses the same commands with `--partition heldout`, after development integrity checks pass. No `metadata_only` arm runs on held-out data. Candidate and grading reservations are separate per shard; model invoice reconciliation and web charges are unavailable. Reference-label matching is a provisional metric, not human-verified factual or clinical accuracy. Report operational failures, unresolved keys and judge disagreements explicitly.

At the user's request during held-out execution, the execution-only helper below schedules up to 12 independent candidate calls concurrently across shards. It uses the frozen prompts, actions and budgets, writes each request and reservation before dispatch, and records its own immutable code hash plus a scheduling addendum in each shard. It stops launching new calls on rate-limit/authentication/transport failures without silently retrying. Do not compare elapsed experiment latency across the scheduling change.

```sh
python3 scripts/advance_authority_concurrent.py --run results/new-heldout --workers 12 --live
```

Run web workers only after the advance process exits. Four completed shard grading commands may run concurrently (two grading requests per shard). After aggregation, export a fresh release directory:

```sh
python3 scripts/export_authority_v2.py --run results/new-heldout --out data/releases/new-heldout
```
