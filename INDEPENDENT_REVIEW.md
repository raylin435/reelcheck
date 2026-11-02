# Independent reference review handoff

**Optional audit.** The current workflow uses the separate machine-reviewed track
in [MACHINE_EVAL_PROTOCOL.md](MACHINE_EVAL_PROTOCOL.md). You do not need to complete
this form to run that evaluation. This page remains available if independent human
verification is wanted later; no human review has been claimed.

Open `results/independent-review-02/index.html` in a normal local browser. It presents the three
downloaded videos, six claim timestamps and source packets without model outputs
or AI reference labels. **Watch each clip, complete the six form cards, click Download review, and attach the downloaded JSONL file to the chat.** No hand-editing JSON is needed. “Needs correction / unsure” flags a case rather than forcing a label. Nothing is submitted, published or frozen automatically. Progress saves locally when the browser permits it; downloading preserves the final answers. The in-app browser blocks `file:` URLs, so open the file in a normal browser.

Generate it again in a fresh location with:

```bash
python3 scripts/build_review_handoff.py --out results/independent-review-03/index.html
```

Give the reviewer only that page, its linked media and
`data/shortform_dev_human_review.template.jsonl`, not the result reports or frozen
AI references. The page's relative paths assume the current repository layout.
The user subsequently chose automated review for the current pilot. No third party has been contacted.

Watch each entire clip and check both audio and visuals. Verify claim fidelity,
source excerpts, editorial summaries, dates and material qualifiers. Complete the
form with reviewer attribution, checks, verdicts and rationale; its download produces
the JSONL automatically. The blank JSONL template remains available as an alternative.
Flag ambiguous or malformed cases for revision/exclusion. In particular, assess
the profession and deployment scope questions in sf_05/sf_06 independently.

The downloaded file includes case hashes, selected evidence IDs and review status. Flagged cases have empty acceptable verdicts and cannot be frozen. On return, reconcile disagreements before evaluating more models. If input text,
timestamps, evidence or scope changes, create versioned inputs and references;
do not overwrite the original six cases or reinterpret the old score as if it used
the new references. For unchanged inputs with all checks completed, the downloaded file can be passed to `scripts/freeze_references.py`. Freeze only after the reviewer has actually completed the work.

Human reference review alone does not satisfy video admission. Native social
publication, full-watch review, rights, media hashes and split checks still pass
through `scripts/export_shortform.py`. The four existing downloads are technically
short portrait videos, but the admitted benchmark remains empty.

Before an independent evaluation, expand beyond these correlated development clips:
12 admitted clips across the five planned topics, preferably from multiple creators,
with a topic- and verdict-balanced mix where genuine source claims support it.
Do not manufacture claims or labels merely to balance counts. Keep creator/event/
original-video groups together; treat any cases inspected during development as
development data, and reserve a separate untouched set for the final claim.
