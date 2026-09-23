# Mechanism admission gate v0.4

## Purpose

v0.1 defines the four mechanism hypotheses.

v0.2 qualifies M1/M2 transition estimability.

v0.3 qualifies M3/M4 response-blind sampling/predictor support.

v0.4 binds all of those to the **real Structural admission chain**.

A mechanism lane cannot advance because its own metadata look promising while the parent Structural system has not passed v0.31–v0.38.

## Structural parent requirement

Before any mechanism decision, v0.4 replays the supplied Structural v0.38 queue with:

`scripts/validate_confirmatory_queue_v0_38.py`.

The mechanism protocol must then match exactly one queue entry by:

- `system_id`;
- frozen Structural protocol fingerprint.

The Structural receipt must still say:

- `admitted_to_confirmatory_protocol_queue`;
- `freeze_confirmatory_protocol_only`;
- confirmatory response unauthorized;
- pilot denominator contribution zero.

## Raw replay rather than trusting mechanism result JSON

v0.4 does not trust a hand-written mechanism qualification result.

For M1/M2 it reruns the raw burned transition pilot through v0.2.

For M3/M4 it reruns the response-blind sampling/predictor inputs through v0.3.

Input SHA-256 values are written into the admission receipt.

## Lane-by-lane admission

Every requested lane receives its own decision.

A qualified lane receives:

`freeze_confirmatory_mechanism_protocol_only`.

A non-estimable lane receives no action and remains neutral.

Therefore a system may legitimately advance, for example:

- M1 + M3;
- M2 + M4;
- M1 only;
- all four;

without pretending that missing transition/genetic/environmental support is negative evidence.

## Partial qualification is allowed; protocol breach is not

**Non-estimability** is a scientific support limitation.

It may leave other lanes eligible.

By contrast, a protocol breach stops the entire mechanism admission. Examples:

- confirmatory partition exposed;
- unfrozen pilot partition used;
- M3 outcomes already opened;
- M4 predictors chosen after response;
- Structural queue replay failure.

## Still no mechanism result

Even a successful v0.4 admission has:

- no effect size;
- no prediction score;
- zero predictive denominator;
- zero mechanism-claim contribution;
- no confirmatory response authorization;
- no TTF handoff.

The only next action is to freeze **one separate confirmatory protocol per eligible mechanism lane**.

## Synthetic CI

CI uses the repository's existing synthetic v0.38 Structural queue.

That queue is accepted only with an explicit synthetic-only flag.

A production mechanism admission cannot use the synthetic queue.

## Current state

No empirical mechanism system is active.
