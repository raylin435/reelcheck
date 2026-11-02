# Compare ordinary retry with targeted evidence recovery

The completed development and 20-claim fresh results are in
[RECOVERY_RESULTS.md](RECOVERY_RESULTS.md). Open
`data/releases/recovery-fresh-01/demo.html` for the standalone recorded replay.

The new runner gives both cheap-model arms the same saved first draft, opened
pages, search results and remaining budget. The targeted arm must name the missing
fact with a follow-up query; the ordinary arm receives a strong generic review
instruction and can search too. A DeepSeek high-reasoning reference uses the same
two-phase tool allowances. See RECOVERY_PROTOCOL.md for the frozen design.

## Run

```sh
python3 scripts/calibrate_recovery_judge.py --out results/my-calibration --live
python3 scripts/run_recovery.py init --inputs data/research_pilot_claims.jsonl \
  --calibration results/my-calibration/calibration.json \
  --out results/my-recovery --partition development
python3 scripts/run_recovery.py advance --out results/my-recovery --live
```

Wait until each `advance` process exits. Run the Codex worker in
`scripts/recovery_web_worker.js` with `tools`, a reporter, absolute repository path,
and output directory. It executes exact model queries/URLs, saves all raw responses
before ingestion, and reuses saved responses when a handoff must resume. It first
checks the runner lock and in-flight API marker. Do not run it while a model process
is active. The older `research_web_worker.js` remains frozen for historical runs.

Repeat worker → advance until all drafts and recovery branches are terminal.
Branching is automatic after all initial drafts finish. Then:

```sh
python3 scripts/run_recovery.py judge --out results/my-recovery --live
python3 scripts/run_recovery.py report --out results/my-recovery
python3 scripts/build_recovery_demo.py --run results/my-recovery \
  --out results/my-recovery/demo.html
```

The demo is a self-contained recorded replay, not a live deployed fact checker.
The web worker still needs Codex's web tool; model inference uses Fireworks.

## Evaluation and accounting

The revised rubric is sanity-checked on eight controlled synthetic cases by both
Kimi and DeepSeek. It is then checked on the disputed real supplement answer.
These checks establish specific logical behavior, not broad evaluator reliability.
Final answers receive two identity-blind assessments on their actual retrieved
pages. Disagreement/ambiguity stays unresolved. Invalid execution counts as failure.
One evaluator shares the reference candidate's family; machine agreement is not
human-verified truth. Historical reports are never overwritten with new grades.

`summary.json` separates actual billing (unique API calls) from per-arm deployment
cost (shared draft included for each deployed workflow). It includes failures,
abstentions, unresolved cases, paired wins/losses/ties, and cost per accepted answer.
Raw web billing is unknown; model-service times are not production wall latency.
The development run's `worker-incident.json` additionally records an interrupted
web handoff, two reacquisitions and their unknown overhead; no model was rerun.

The code, prompts, inputs, config and calibration result are snapshotted before
generation. Paid commands reject changed frozen code. Input prompts whitelist only
the claim and date; they do not receive private evidence, expected labels, creator
metadata or evaluator feedback. All raw model/tool responses are retained locally.
Do not upload ignored full-page snapshots with a public repository export.

## Fresh-run artifacts

`data/recovery_fresh_claims.jsonl` preserves provenance; four round-robin shards
contain the same 20 cases. `RECOVERY_FRESH_PROTOCOL.md` records the transcript-only
scope and pre-run limits. `data/releases/recovery-fresh-01/manifest.json` freezes inputs,
config and worker hashes; each shard also snapshots the inference/evaluator code.
The four runners are independent and may advance concurrently, but never overlap
two writers within one shard. A transport failure is terminal for that attempt;
continuing unrelated active tasks does not retry it.

After all four shards finish generation and assessment, rebuild the report/replay
and check its integrity without any paid calls:

```sh
python3 scripts/aggregate_recovery.py --run results/recovery-fresh-01
python3 scripts/audit_recovery_run.py --run results/recovery-fresh-01
```

The aggregate replay state is presentation-only. Its local call indices overlap
across shards, so do not feed it to the inference runner or use it for billing.
The aggregator namespaces call indices by shard and counts each shared draft once.
