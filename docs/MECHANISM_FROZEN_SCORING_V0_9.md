# Frozen mechanism lane scoring v0.9

## Purpose

v0.7 records exactly which response file was opened.

v0.9 is the first stage that calculates a mechanism-lane metric.

It **does not** decide the biological mechanism claim.

This separation matters because a single local score is not enough for several of the prospective claims.

## Replay requirements

The scorer requires a Git-tracked v0.7 access receipt and replays the full chain:

- Structural admission;
- mechanism admission;
- lane protocol freeze;
- v0.8 response-blind scoring inputs;
- v0.6 response authorization;
- v0.7 response access.

Both the response SHA and scoring-input SHA must match.

Scoring and response keys must match exactly. There is no post-outcome row selection.

## M1 — contemporary colonization

For each nonmissing `z_t=0` row:

- outcome = `z_t1`;
- compute reference log loss;
- compute candidate log loss.

Primary metric:

`mean(candidate loss − reference loss)`.

Negative is favourable.

Block-level increments are also emitted.

A local score alone does not authorize a colonization mechanism claim; separate predeclared spatial-transfer evidence remains required.

## M2 — rescue / persistence

For each nonmissing `z_t=1` row:

- extinction event = `1 - z_t1`.

The same candidate-minus-reference log-loss metric is calculated for the extinction endpoint.

Again, scoring is separate from a rescue/persistence claim.

## M3 — historical legacy

The response-blind v0.8 pair weights are joined to the exact M3 response pair set.

Primary metric:

`weighted mean genetic_value(graph_connected) − weighted mean genetic_value(alternative)`.

This is a deterministic contrast only.

Claim adjudication must still apply the predeclared geographic/environmental/population-structure null interpretation.

## M4 — environmental proxy

Four mean log losses are computed:

- original reference;
- original reference + topology;
- enriched environment reference;
- enriched environment reference + topology.

v0.9 reports:

- original topology increment;
- enriched topology increment;
- enriched-reference improvement;
- change in topology increment after enrichment.

It does **not** call the topology effect “collapsed,” because the v0.5 protocol has not yet machine-frozen a numerical practical-null interval.

That missing interval is surfaced explicitly as an adjudication blocker rather than invented after the response is seen.

## Missing outcomes

Missing outcomes are excluded from scoring and counted.

They are never imputed as zero, absence, non-colonization, extinction or low affinity.

If no required nonmissing outcome remains, the lane is reported as:

`confirmatory_mechanism_lane_non_estimable_after_response`

and contributes no mechanism claim.

## Current state

No empirical mechanism lane is scored. CI uses synthetic fixtures and `counts_as_empirical_evidence=false`.
