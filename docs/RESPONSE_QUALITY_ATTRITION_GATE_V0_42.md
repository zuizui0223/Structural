# Response-quality attrition gate v0.42

## Why this extension exists

The frozen v0.31-v0.40 admission chain protects against a different failure than the one exposed by the later LandFrag one-shot.

PNW and RMNP failed because the future endpoint collapsed toward one class. LandFrag v0.2 failed earlier: its response-independent geometry panel contained 34 geographies, but after the frozen response-quality rules were applied only 29 independent geographies survived, below the predeclared minimum of 30. H1 was therefore never scored.

Those are not the same failure mode.

- **response-quality attrition**: too few held-out blocks retain enough usable response rows;
- **endpoint/class collapse**: usable response exists, but the frozen training design lacks the required event/non-event support.

v0.42 separates them prospectively.

## No retrospective repair

v0.42 is additive and future-only.

It does not alter the historical v0.31-v0.40 code path, does not change any threshold for PNW, RMNP or LandFrag, and does not re-adjudicate any prior system. LandFrag remains a terminal 29/30 response-quality STOP with no H1 estimate.

## Pre-pilot freeze

Before any burned-pilot response is opened, a future system must freeze a v0.42 contract that binds:

- the exact parent v0.31 protocol fingerprint;
- the system identity;
- the system-specific response-quality semantics;
- the minimum number of response-qualified held-out blocks.

The response-quality block minimum cannot be lower than the already-frozen minimum estimable-block count.

## Existing raw surface stays closed

The v0.39 raw burned-pilot surface remains exactly:

    partition_unit, block, target

No extra quality or outcome column is added.

Any row that fails the system's prospectively declared survey/completeness/effort rules must be represented as a missing/non-estimable target before the v0.32 audit. Thus the same immutable raw pilot surface supports both audits without carrying extra post-outcome information.

## Two-stage block audit

For each held-out block:

### Stage A — response-quality survival

A block survives when it retains at least the parent protocol's frozen `minimum_test_rows` applicable targets.

If too few blocks survive, the result is:

    stop_response_quality_attrition

### Stage B — endpoint estimability

The unchanged v0.32 audit then asks whether the surviving design retains the required training positive and negative counts.

If too few blocks are estimable, the result remains:

    stop_endpoint_variation

Neither stage can rescue the other.

## Synthetic discrimination tests

The CI suite includes three cases.

1. **Attrition case** — legacy v0.32 has two estimable blocks and would qualify, but only 2/3 blocks retain enough usable held-out response. v0.42 stops the system before confirmatory protocol construction.
2. **Class-collapse case** — all 3/3 blocks survive response quality, but training class support fails. v0.42 passes Stage A while v0.32 independently stops the system.
3. **Clean case** — both gates pass; the only authorized action remains freezing a separate confirmatory protocol.

## Evidence ceiling

The v0.42 output contains no effect estimate and no prediction score. Its predictive-denominator contribution is exactly zero.

A v0.42 pass does not authorize confirmatory response access. It only permits the same next action as a clean v0.33 pass:

    freeze_confirmatory_protocol_only

## Future sequence

    independent system intake
      -> v0.31 disjoint partition freeze
      -> v0.42 response-quality contract freeze
      -> v0.39 exact three-column burned-pilot surface
      -> v0.32 burned-pilot execution
      -> v0.42 response-quality survival audit
      -> v0.38 raw replay / v0.37 arithmetic verification
      -> v0.33 confirmatory-freeze gate
      -> freeze separate confirmatory protocol
      -> only later authorize confirmatory response
