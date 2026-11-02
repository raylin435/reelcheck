# Machine-reviewed short-video pilot

No human action is required to run this track. Its reference labels are model
assessments, with unresolved cases retained. The existing human-reviewed admission
track remains separate. Do not call these labels human-verified ground truth.

The current inputs are `data/machine_semantic_inputs_v2.jsonl`: six previously
tested development claims and nine original-claim paraphrases from three new clips.
The new clips are 90.01, 126.59 and 53.74 seconds, each 1080 × 1920. Full decoding,
display dimensions, duration and hashes are recorded. One 12.03-second discovery
clip was excluded under the existing 15–180-second rule. These are publisher-hosted
vertical exports; native Shorts/Reels/TikTok publication has not been verified.

GLM checked the nine new claims against publisher captions and sampled frames.
All nine were assessed as faithful extractions. This does not establish factual
truth and does not replace full audio transcription. The science claims are visible
text overlays; its incidental audio captions do not contain them. Four malformed
caption cues in the reinstatement video are outside the selected claim intervals.

Kimi K3 and DeepSeek independently assessed the fixed evidence, with high reasoning
effort. GLM provided a third opinion where needed. Thirteen of fifteen references
resolved; `sf_05` and `new_07` remain unresolved. Any explicit material scope
ambiguity prevents an automatic label, even with a majority. No reference verdict
is supplied to the candidate models.

The old development cases also received fresh references under this protocol.
Their resulting scores are not directly comparable with earlier reports using the
old AI-draft labels. In particular, `sf_06` now has an insufficient-evidence reference.

The source audit corrected one omission in `new_09` before candidate generation:
the article itself directly characterizes the change in experiment scope. Its
summary now includes that statement. The initial inputs and all 33 initial votes
are preserved. Only the changed case received two new votes; all unchanged exact
cases reused their original votes. The merged bundle was frozen before generation,
and costs include the superseded votes. See `data/machine_inputs_revision_02.json`.
Claim text, timestamps and media did not change, so the original clip-fidelity
audit remains applicable through a checked evidence-only revision.

The evidence is explicitly limited to supplied source summaries. A claim such as
the number of people contacted can be unsupported by this packet even when another
source might establish it. This is not a claim that the video statement is false.
The data includes one arithmetic contradiction: the chart's displayed percentage
does not equal its displayed numerator divided by its denominator. Keep the raw
clip, chart and original report available for inspection.

## Download and ingest

The portable export is `data/releases/machine-pilot-01/`. It contains model inputs,
frozen references, clip-fidelity outputs, configuration, protocol and a manifest
covering all six clips used across both partitions. The optional media archive is
`results/machine-pilot-01-media.zip`; `media_archive.json` records its checksum.
Nothing was uploaded or published.

Keep code, JSONL inputs, references and the manifest in GitHub. Put permitted large
media in a GitHub Release asset or a media store, and retain original-source URLs
and SHA256 values as a fallback. The current six assets are marked public domain
by DVIDS; the manifest records creator credit and per-asset terms. Do not imply
government endorsement or apply the repository's code license to third-party media.

For fixed-evidence testing, send only the claim and supplied evidence in `inputs.jsonl`.
For a future audiovisual test, send actual video bytes to an API that supports them,
or timestamped frames plus audio/transcript to compatible modalities. A source URL
alone is not reliable ingestion. Keep OCR, speech, context extraction and final
verification errors distinct. This pilot tests only the final fixed-evidence step.

Use `reelcheck.media.download` with the manifest's expected SHA256 for verified
downloads; it has a 200 MiB per-file cap, bounded retries and atomic writes. Original
files here are below the cap. If the publisher changes bytes, stop and create a new
version instead of silently treating the asset as the same clip.

## Reproduce

The checked-in configuration and protocol specify settings and budgets. Use fresh
output directories; historical traces must not be overwritten. For a new evaluation
of the unchanged frozen inputs:

```sh
python3 scripts/run_semantic_comparison.py \
  --config config.machine_semantic.json --inputs data/machine_semantic_inputs_v2.jsonl \
  --references data/releases/machine-pilot-01/references.frozen.json \
  --out results/my-semantic-preview
```

That command is a dry run. Add `--live --shell-keys ~/.zshrc --max-calls 30 --max-cost-usd 1`
to make paid calls. Credentials are read locally without executing the shell file.
Use `scripts/judge_run.py` with the same inputs, configuration and reference bundle,
then `scripts/report_machine_eval.py` to generate coverage-aware comparisons.

Keep all future claims from the same original video, creator and event together
when splitting data. One new clip shares a creator with the earlier set, and all
clips come from one government publishing ecosystem. Results on three new clips
cannot establish general superiority across political news or nutrition advice.
