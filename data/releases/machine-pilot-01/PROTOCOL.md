# Machine-reference semantic-check experiment

Declared 2026-11-02 before new candidate generation. Human review is optional for
this separate machine-reviewed track; no human labels or strict video admission
will be fabricated. Preserve all historical runs and references.

## Hypothesis and systems

Ordinary GPT-OSS 120B JSON-schema output is the baseline. The treatment takes that
exact draft and makes one additional call to the same model, with the same sampling
defaults and 4096-token ceiling. The second call maps material evidence requirements
and checks modality, causality, population, scope, date, and policy-stage distinctions.
A structural gate checks map/verdict consistency and quote fidelity; it cannot prove
semantic entailment. The model may still omit a material requirement. No oracle,
reference, stronger answer model, or external retrieval is available to the treatment.
Report both stages' cost and latency. Baseline is physically generated once and
shared between branches; actual experiment billing must not count that call twice.

## Machine references

Kimi K3 and DeepSeek V4.1 Flash independently assess identical evidence packets.
Use explicit high reasoning effort for these two; GLM 5.3 Flash uses its default
reasoning as a third, independently prompted assessor only if initial agreement
fails. References use JSON-object mode, not schema mode that disables reasoning
output. Candidate answers, previous AI labels and other votes are not shown.

Two non-low-confidence votes agreeing on a verdict can resolve a case. Any valid
assessor flagging material scope ambiguity leaves it unresolved regardless of vote
count. Confidence is a model flag, not calibrated probability. Frozen references
retain all cases, statuses and vote traces. No retries after API or schema failures.
This is model agreement, not ground truth; shared misconceptions remain possible.

## Data and timing

Use the existing six cases only as a separately reported development partition.
Add up to twelve untested original-claim paraphrases from up to six newly acquired,
permitted short portrait clips. Candidate inclusion depends on acquisition, claim
fidelity, checkable claims and available primary sources, never on candidate success.
Do not fabricate contradictory claims or label balance. Record exact timestamps,
media hashes and caption/frame limitations. New clips from familiar creators or
underlying series are not creator-held-out; report overlap explicitly. No claim
of end-to-end audio/video verification is made for caption/frame-derived inputs.

Freeze inputs, config and machine references before generation. Keep this semantic
prompt fixed after observing development outputs. Errors may be fixed transparently,
but model failures must not lead to favorable reruns or silent exclusions.

## Budgets and scoring

Combined experiment maximum: 18 cases, 54 reference calls ($6 reservation cap),
36 generation calls ($1 cap), 36 pointwise grading calls ($4 cap). Actual call counts
can be smaller. These are conservative local reservations, not provider billing
guarantees. No deployment, external publishing, or unlicensed media acquisition.

Before reference generation, up to six separate GLM caption/frame fidelity checks
may inspect the new clips, capped at $1 total. They assess extraction fidelity, not
truth. A false on-screen statement can be a faithfully extracted claim. Record all
uncertain/unfaithful results and settle extraction issues before any candidate run.

Kimi high-reasoning grades candidate identity-blind against frozen references.
It participates in reference construction, so its acceptance metric is not an
independent external validation. Primary metrics are objective validity, agreement
with resolved machine references, and wrong decisive answers versus those references.
Also report grounded judge acceptance, abstentions, unresolved reference coverage,
judge/reference conflicts, clip groups, cost and latency. Report all-input and
resolved-only denominators separately; unresolved is never equivalent to correct.
Keep development and new-clip partitions separate. No significance or general
superiority claims from this small pilot. Manual review remains an optional later audit.
