# Authority v1 — authored development data and untouched holdout

See the root [protocol](../../AUTHORITY_PROTOCOL.md) and [usage](../../AUTHORITY.md).

- `development.jsonl`: 20 claims, no reference answers or source URLs.
- `heldout.jsonl`: 20 grouped held-out claims; not used in the canary.
- `references.jsonl`: provisional evaluator-only answers and exact excerpts. The candidate runner never loads these into messages.
- `manifest.json`: selection window, deterministic balanced group split and immutable JSONL hashes.

References were authored from FDA Drug Safety Communications and CDC Health Alert Network notices retrieved November 2, 2026. Full acquisition text remains in the ignored local results directory; each reference retains its SHA-256 and a relevant excerpt. Original source URLs are included for independent review. Date metadata was checked against each source heading, but the excerpt alone may not include the heading. The reference review status remains the original authorship status; separate run review artifacts record subsequent assessments without rewriting labels.

These are constructed positive/negative statements, with some deliberately missing context. They are neither authentic user health requests nor authentic short-video claims, and there is no verified model training cutoff. Eight cases use notices from the preceding 90 days; the remainder exercise dated changes and scope. Do not report this as a 40-case fresh-knowledge or medical-accuracy benchmark.
