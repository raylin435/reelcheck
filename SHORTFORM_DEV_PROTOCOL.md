# Fresh-clip development comparison: protocol declared before inference

Date: 2026-11-02. The six claims below have not been run through candidate models.
This is a development experiment, not the admitted, independently reviewed benchmark.
No human review or completed native-social provenance verification is claimed.

## Inputs and references

Six source-claim paraphrases from three downloaded portrait videos: three supplement
claims, a hydration heuristic, and two insomnia claims. Original publisher captions
were read; Codex inspected contact sheets at 4-second intervals. No independent
audio listening or full-frame review is claimed. The hydration units/example and
irregular-work-schedule caption were checked against visible graphics.

The fourth acquired clip was not included: its general food-choice advice does not
yet provide a sufficiently precise factual claim. The eight other discovery links
have not been downloaded or verified. No synthetic contradictions are added.

All systems get the same claim and fixed evidence. The as-of date is 2026-11-02,
but the prevalence claim concerns the historical survey discussed in a 2022 clip,
not a new 2026 prevalence measurement. Sources include a 2021 survey, a 2022 adverse
effects study, FDA and OPSS guidance, CDC water guidance, a military insomnia guide,
and NHLBI risk-factor guidance. Short excerpts and explicitly marked editorial
summaries are hashed. Evidence selection and AI summaries remain potential biases.

AI reference drafts: sf_01 supported, sf_02 insufficient, sf_03 insufficient,
sf_04 insufficient, sf_05 supported, sf_06 supported. The risky distinctions are
possibility versus documented occurrence, contamination examples versus a probability,
and variable water needs versus a qualified starting-point heuristic. No contradicted
case is present; this set cannot measure contradiction detection comprehensively.

Freeze drafts before candidate generation with `--allow-ai-drafts`. Do not change
inputs, references, prompts, budgets, or scoring after observing candidate answers.
Reference defects must remain visible and require a later version/rerun.

## Comparison and budgets

- Direct GLM 5.3 Flash.
- Direct DeepSeek V4.1 Flash reference.
- GPT-OSS 120B baseline with its existing JSON-object response mode.
- GPT-OSS 120B with the previously developed citation-ID schema and deterministic
  quotation renderer. This is the unchanged treatment selected on earlier videos.

One run, six cases × four systems = 24 generation calls. Same 4096 output-token
ceiling, two workers, deterministic shuffled system order, no retries or repairs.
Generation cap $2; separate Kimi high-reasoning judge cap $4 and 24 calls. Caps use
the existing conservative cost reservations, not provider-enforced billing limits.
No dedicated deployment or new external provider is provisioned.

The citation-ID mode changes both response representation and generation constraints.
Its documented reasoning-output caveat remains. Any observed benefit is for this
whole configuration, not proof that deterministic rendering alone improves reasoning.

## Metrics and interpretation

Report format/quote validity separately from reference verdict agreement and blinded
LLM-assessed grounded acceptance. Include all failures and unresolved judgments in
denominators. Report same-case treatment wins/losses, actual token usage, estimated
cost and service latency; judge overhead is separate. Summarize by clip as well as
claim because six claims represent only three correlated video groups.

Judge sees the frozen reference and candidate, never candidate identity. A conflict
with the frozen reference remains unresolved and cannot silently redefine gold.
No model-assessed score is called human-verified accuracy. A win on these fresh-to-
the-model cases can support a narrowly scoped development result, not a general
superiority claim. If no improvement is found, report that without searching for a
favorable rerun or changing the test retrospectively.
