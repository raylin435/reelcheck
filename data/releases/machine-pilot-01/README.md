# ReelCheck machine-reviewed pilot

This is a portable fixed-evidence pilot, not human-verified ground truth.
Use inputs.jsonl for candidate models. Keep references.frozen.json and claim_fidelity.jsonl out of candidate prompts.
The manifest links original media and captions, byte hashes, duration/dimensions, rights and timestamped claims.
Media must pass SHA256 verification after download; do not silently accept changed files.
The optional media ZIP uses clip_id/original.mp4 and includes publisher captions, timeline, ffprobe and source pages.
Public-domain asset markings and creator credits are per clip; no government endorsement is implied.
Keep metadata/code in git and large MP4s in a release asset or licensed media store. No upload was performed.
Publisher captions can be wrong; see caption_issues and the claim-fidelity limitations.
For multimodal ingestion, pass actual video to a supported API or timestamped sampled frames plus audio/transcript; a source URL alone does not guarantee model access.

Results: baseline accepted 12/13 resolved cases; extra pass 11/13. Two of 15 cases unresolved. On new clips alone: 8/8 versus 7/8 resolved, one of nine unresolved. No improvement claim.

See [REPORT.md](REPORT.md), [results.json](results.json), and the raw files under audit/. Total estimated experiment cost: $0.494095409. The audit asset index records hashes and source paths, including relevant-primary-page extraction of search results.
