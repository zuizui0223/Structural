# Mechanism transition pilot gate v0.2

## Purpose

The prospective mechanism framework separates:

- M1 contemporary colonization: **0→1**;
- M2 rescue/persistence: **1→0** or its complement 1→1.

v0.2 makes that distinction executable before any confirmatory mechanism response is opened.

## Burned-pilot surface

The pilot CSV contains exactly four columns:

```text
partition_unit,block,z_t,z_t1
```

No topology, environmental, genetic, probability, residual, effect or prediction column is allowed.

The burned pilot answers only:

> Are there enough transitions to estimate each dynamic mechanism lane under the frozen held-out design?

## M1 gate

For every held-out pilot block, M1 requires:

- enough test rows beginning at state 0;
- enough training **0→1** colonization events;
- enough training **0→0** non-colonization rows.

The lane qualifies only if enough frozen blocks meet all three minima.

## M2 gate

For every held-out pilot block, M2 independently requires:

- enough test rows beginning at state 1;
- enough training **1→0** extinction events;
- enough training **1→1** persistence rows.

Again, enough blocks must meet all three prospectively frozen minima.

## No cross-rescue

This is the key rule.

If M1 passes and M2 fails, the result is:

`partial_mechanism_estimability_only`.

That does not authorize M2 and does not turn M2 into negative evidence.

The same applies in the opposite direction.

## Missing observations

A row with missing `z_t` or `z_t1` is non-estimable.

It is never converted to absence, non-colonization or extinction.

## Pilot boundary

Every output has:

- `effect_size = null`;
- `prediction_score = null`;
- `predictive_denominator_contribution = 0`;
- `mechanism_claim_contribution = 0`;
- `confirmatory_response_authorized = false`.

A clean pass authorizes only:

`freeze_separate_confirmatory_mechanism_protocol_only`.

It does not authorize confirmatory response access.

## Relation to Structural admission

This gate does not replace v0.31–v0.40 Structural admission.

A future system must already be independently admitted under the normal Structural sequence and have its mechanism protocol frozen while response-sealed.

The mechanism pilot then consumes only its predeclared burned pilot partition.

## Current state

There is no current empirical system in this lane.

The repository exercises the gate only with synthetic fixtures.
