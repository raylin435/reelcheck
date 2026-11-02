# Paired targeted-recovery experiment

Frozen before development candidate calls, November 2, 2026.

Question: does a targeted evidence-gap search improve research-and-verification
over a strong generic review/retry using the same cheap model and equal limits?
This is a new retrieval-recovery hypothesis; prior requirement-map/self-check
experiments did not show an advantage.

## Evaluator gate

The version-2 rubric explicitly separates possibility from occurrence, approximate
from strict quantities, and missing sentence-level dates from available document
context. It also checks extra factual assertions in explanations. Eight predeclared
synthetic language fixtures test both false confidence and unnecessary abstention.
Kimi K3 and DeepSeek V4.1 Flash independently assess all eight; require 16/16
logical verdict/acceptance matches before scoring candidates. This small sanity
check does not validate real-world truth or source authority. Separately re-assess
the previously disputed supplement answer; retain historical grades unchanged.

## Equal-budget arms

Each case first runs GLM with a strong shared prompt, up to one search, two reads,
and five model calls including a draft. The **same recorded GLM draft and tool
history** then forks into generic_retry and targeted_recovery. Generic retry gets
objective errors and strong review/research instructions. Targeted recovery gets
the same inputs but must identify a specific missing fact with each follow-up
query. It gets no reference verdict, evaluator feedback, or curated evidence.
Both branches may use one additional search, two reads, and five additional model
calls, then finish. Limits are ceilings; no branch must spend the whole allowance.
All arms use five search results and at most 16,000 characters per read.

DeepSeek V4.1 Flash with high reasoning is an additional open-model reference,
using the same two-phase generic-retry protocol and total allowances. It is not
claimed to be a proprietary frontier model or an organizer-certified baseline.
The public event page permits improvements against a baseline; detailed rules
were inaccessible. No messages to organizers are sent by this experiment.

Invalid draft structure/quotes can be corrected within the single recovery
episode in both cheap arms. A final invalid action/quote is an execution failure.
Provider access/rate/transport failures are never silently retried. Tool errors
consume their allowance. Candidate chooses all queries and URLs. Web results are
untrusted data, not instructions. Source rendering/transport is identical across
arms. Shared draft cost counts once in actual billing, and once in each arm's
deployment-cost estimate. Report paid calls separately from attributed calls.

## Data and freeze

Use the three existing research claims for development and inspect paired cases.
Do not change prompts to rescue final examples. After development, freeze code,
configuration and the input manifest before a fresh evaluation targeting 20 claims
from different videos/creators. Retain provenance and group IDs, do not invent
claims for label balance, and state which media/claim-fidelity checks are actually
verified. Familiar creators/series must not be called creator-held-out. The
claim-only runner never receives extraction metadata or private reference evidence.

If development shows no paired acceptance benefit, stop expanding this treatment
and report the negative result; do not repeatedly tune against final cases until
it wins. A useful demonstrated recovery does not establish aggregate improvement.

## Scoring and deliverables

Two calibrated models independently assess each anonymous final answer against
its actual retrieved pages. Accept only when both accept; reject when both reject;
disagreement, ambiguity or invalid grading remains unresolved. Show each vote.
One judge shares the reference candidate's model family; expose this limitation.
Failures remain in all-case denominators. Inspect paired disagreements, excessive
abstention and weak judge approvals without silently changing frozen scores.

Report consensus acceptance, incorrect decisive decisions under consensus,
justified vs unnecessary abstention, unresolved coverage, objective failures,
search/read usage, model-service time, estimated cost per accepted answer, and
every paired win/loss/tie. Web cost is unknown and bridge idle time is not product
latency. Produce a comparison report and an inspectable replay demonstration,
clearly labeled recorded rather than live. No general accuracy claim or statistical
equivalence from a small pilot; never call machine agreement human truth.
