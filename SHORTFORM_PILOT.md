# Short-form acquisition pilot — November 2, 2026

Latest follow-up: [primary metadata audit](SHORTFORM_CANDIDATE_AUDIT.md) verifies the eight YouTube leads at the platform-metadata level. Rights, full review and local media checks remain pending; the original acquisition records below are preserved. [Independent review](INDEPENDENT_REVIEW.md) is ready for the user.

This is the acquisition-stage snapshot. The later
[six-claim development experiment](SHORTFORM_DEV_RESULTS.md) has now run;
its AI reference drafts do not change the human-review admission status below.

This extends the completed **Review hackathon resources** session: retain direct
GLM and DeepSeek as comparisons, GPT-OSS with deterministic citation rendering as
the implementation candidate, and Kimi with explicit high reasoning as the judge.
Provider model eligibility as the hackathon frontier baseline is still unconfirmed.
No new paid inference or factual-accuracy result is claimed here.

## What is actually ready

| Stage | Count | Meaning |
| --- | ---: | --- |
| Candidate links | 12 | 3 nutrition, 3 politics/policy, 2 health/fitness, 2 energy, 2 consumer technology |
| Downloaded originals with publisher captions | 4 | Publisher-hosted social-ready DVIDS exports, marked public domain |
| Full decode, portrait, and 15–180 second checks passed | 4 | Actual bytes inspected, not inferred from titles |
| Timestamped claim drafts | 5 | AI paraphrases of publisher captions, not verified speech or labels |
| Admitted benchmark clips | **0** | Native social publication and independent full-clip review still pending |
| Paid model calls | **0** | Collection and local verification only |

Eight other links are discovery leads, not verified videos. Their rights, duration,
content and availability remain unknown. Secondary articles locate the links;
they are not evidence for the underlying factual claims. No download was attempted
without a recorded permission basis. The four acquired clips cover only nutrition
and insomnia and share a publisher. They are an ingestion pilot, not a representative
or demonstrably difficult benchmark. Do not fill the remaining slots with more of
the same easy source merely to reach 12.

| Downloaded clip | Measured seconds | Display size | Creator |
| --- | ---: | --- | --- |
| The Dangers of Dietary Supplements | 32.768 | 1080 × 1920 | Sara Barger / Defense Health Agency |
| What is Performance Nutrition? | 40.149 | 1080 × 1920 | Sara Barger / Defense Health Agency |
| Performance Nutrition: The Best Ways to Eat | 45.589 | 1080 × 1920 | Sara Barger / Defense Health Agency |
| Insomnia Factors | 23.104 | 1080 × 1920 | Taylor Stinson / Defense Health Agency |

The original MP4s total 82,554,599 bytes. SHA256 hashes and public direct URLs are in
`data/shortform_acquisition.json`; no videos or downloaded full HTML are tracked in Git.
The local review page is `data/media/pilot-01/review.html`.

## Findings worth testing

- The supplement prevalence sentence includes **self-reported**, **approximately**,
  and **at least once a week**. The page description drops qualifiers. The original
  [2021 survey](https://pubmed.ncbi.nlm.nih.gov/34293133/) reports 74% among respondents,
  with data collected in 2018–2019. Review scope, rounding and dates before labeling.
- The weight-loss clip ends with a probabilistic generalization about effective
  supplements being drugs. [FDA contamination evidence](https://www.fda.gov/drugs/frequently-asked-questions-popular-topics/questions-and-answers-about-fdas-initiative-against-contaminated-weight-loss-products)
  can establish examples; examples alone do not establish a population probability.
- The hydration clip presents a starting-point heuristic. Its captions render the
  example as “100 and six” paired with 80 ounces. **Do not silently correct this.**
  Listen to the source, verify the missing body-weight unit, and compare the exact
  claim with [CDC guidance on varying water needs](https://www.cdc.gov/healthy-weight-growth/water-healthy-drinks/).
- The performance-nutrition caption track has a cue ending before it starts
  (37.751 → 37.540 seconds). The parser preserves and flags it.
- Insomnia captions may misrecognize words; the treatment claim needs evidence for
  brief behavioral treatment specifically, not just general sleep-hygiene advice.
  [NHLBI treatment guidance](https://www.nhlbi.nih.gov/health/insomnia/treatment) is an
  evidence lead, not yet a complete adjudicated packet.

These are annotation questions, not model failures or truth verdicts. Draft
paraphrases and exact caption spans are in `data/shortform_claim_drafts.jsonl`.

## Admission and splits

For the primary benchmark require all of the following:

1. Entire original clip, 15–180 seconds, square/portrait display orientation after
   rotation and sample-aspect-ratio adjustment, successful full video/audio decode.
2. Actual native Short/Reel/TikTok publication verified and linked. A publisher's
   “vertical for social” export alone does not satisfy this requirement.
3. Per-asset download/redistribution basis; public visibility is insufficient.
4. A named human watches the full clip, verifies audio and visible text, and records
   exact claim spans bound to the inspected file's SHA256.
5. Evidence packets include source dates, retrieval dates, passage hashes, and an
   explicit distinction between excerpts and editorial summaries.

All current candidates are development data. Never relabel already-inspected or
tuned-on examples as held out. Group future splits by creator, event/claim family,
and original video, including reposts. The validator rejects known cross-split
groups, but grouping itself needs review; hashes cannot detect all semantic duplicates.
Pilot on 12, expand toward 60 diverse clips, then collect additional held-out cases
if feasible for the event's 100+ example guidance. Multiple claims from one clip
are correlated and do not count as independent clips.

Keep supported, contradicted, insufficient and non-checkable/advisory cases visible.
Do not mutate real speech to force balanced labels. Pure advice or predictions can
remain an extraction/abstention diagnostic, outside factual-verdict accuracy.

## Reproduce acquisition

From the repository root, restore the exact npm dependency lock into ignored local tooling:

```sh
mkdir -p .tools
cp tools/media-package.json .tools/package.json
cp tools/media-package-lock.json .tools/package-lock.json
npm ci --prefix .tools --no-audit --no-fund
```

Resolve tool paths with `node -p 'require("./.tools/node_modules/ffmpeg-static")'`
and `node -p 'require("./.tools/node_modules/ffprobe-static").path'`.
Pass those absolute paths below. Original run used ffmpeg 6.0 and ffprobe 4.4-tessus;
binary hashes are recorded in the acquisition report. Other operating systems
receive different binaries: record their versions and hashes when replicating.

```sh
python3 scripts/collect_shortform.py --out results/shortform-preview
python3 scripts/collect_shortform.py --acquire --out data/media/pilot-02 \
  --ffmpeg /absolute/path/to/ffmpeg --ffprobe /absolute/path/to/ffprobe
```

Always use a fresh collection directory. Direct HTTPS transfers have three bounded
attempts, a 200 MiB cap, atomic completion and content hashes. The public DVIDS page
is saved locally and checked for its public-domain marking and flagged third-party
restrictions before downloading its exposed MP4. No platform login, cookies, access
bypass, or YouTube scraping is implemented. Errors stay in the report. Acquisition
does not guarantee long-term upstream availability; the versioned media archive does.

Full originals, captions, timeline JSON and review frames are available locally.
The 1 fps preview frames can miss brief overlays and are **not** complete visual
evidence; full video review is required. Frames are not passed to a model by this code.
For APIs, upload actual MP4 bytes using the selected provider's documented video
interface, or use a separately declared frame/audio/OCR pipeline. A watch-page URL
and an `image_url` endpoint are not general-purpose video ingestion.

## Review, freeze, compare, judge

Copy each `review.template.json` into a separate completed-review JSONL. Keep the
templates unchanged. Human review must fill the reviewer, media hash, native
publication URL, full-watch confirmation and claims. Each claim has `text`,
`start_seconds`, `end_seconds`, `origin` (`spoken`, `on_screen`, `combined`), `as_of`
and `evidence`. Each evidence passage needs `id`, `text`, `url`, `retrieved_date`,
`evidence_kind` and the SHA256 of its exact UTF-8 text; include `published_date`
where available. Never copy a draft straight into a human-reviewed record.

```sh
python3 scripts/export_shortform.py --collection data/media/pilot-01/collection.json \
  --reviews reviewed_clips.jsonl --out data/shortform_reviewed_inputs.jsonl
python3 scripts/freeze_references.py --inputs data/shortform_reviewed_inputs.jsonl \
  --out reference_templates.jsonl
# Complete reference assessments against evidence BEFORE generating candidate answers.
python3 scripts/freeze_references.py --inputs data/shortform_reviewed_inputs.jsonl \
  --drafts reviewed_references.jsonl --out frozen_references.json
python3 scripts/run_model_matrix.py --config config.structured_video.json \
  --inputs data/shortform_reviewed_inputs.jsonl --references frozen_references.json \
  --out results/fresh-shortform-preview
```

The exporter refuses pending review, changed media, missing evidence, and unknown
native publication. No scored inputs have been exported for this pilot.
`--allow-ai-drafts` permits explicitly labeled development reference freezes only.
The matrix records the frozen-file hash **without loading reference labels into
candidate prompts**. Add the existing `--live` and spend/call limits when data is ready.
After a live candidate run, judge with:

```sh
python3 scripts/judge_run.py --run results/fresh-shortform-live \
  --inputs data/shortform_reviewed_inputs.jsonl --references frozen_references.json \
  --config config.real_video.json --out results/fresh-shortform-judge
```

This is also a dry run unless `--live` is added. The judge rejects a reference that
was not bound to the candidate run or was frozen afterward. A judge/reference
conflict becomes unresolved and requires adjudication, not a new ground truth.
Objective failures still cannot pass. Historical runs retain their original scoring;
new references cannot retroactively validate them. Freeze timestamps/hashes provide
reproducibility, not cryptographic proof that an annotator never saw an answer.

Next evaluation should report extraction and fixed-evidence verification separately,
with verdict correctness, grounded citations, wrong decisive answers, abstention,
cost and latency. Calibrate the judge against independent human reviews; use a second
model family on disagreements plus a random agreement sample. Keep all unjudged and
failed cases in denominators. Do not call AI-assessed acceptance human accuracy.

## Share media separately from code

```sh
python3 scripts/package_shortform.py --collection data/media/pilot-01/collection.json \
  --out results/shortform-development-media.zip
```

The archive contains originals, captions, timeline metadata, review templates,
attribution and per-file checksums. It is labeled unreviewed development media.
Use a versioned GitHub Release or dataset store for this archive after reviewing
the release contents; no external upload is performed by the script. Keep code,
lightweight manifests and permitted annotations in Git. Respect the
[DVIDS per-asset restrictions](https://www.dvidshub.net/about/copyright), credit Sara
Barger and Taylor Stinson / Defense Health Agency, and do not imply endorsement.
The repository's MIT license does not grant rights to third-party media.
