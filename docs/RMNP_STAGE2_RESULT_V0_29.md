# RMNP Stage 2 result v0.29

## Terminal result

The authorized 2022 AMMA target was opened once under the frozen v0.28 authorization and v0.27 scoring implementation.

The programme terminates as:

> **non-estimable before any model fit**

This is neither favorable nor adverse predictive evidence for typed connectivity.

## 2022 target

Across the frozen 69-site evaluation universe:

- positive: **3**
- negative: **66**
- non-estimable: **0**

All 69 sites also have estimable 2021 lagged state.

Target-table SHA-256:

`2dca70e103452f932bc3169ebce7f5f7a08b7a149dd20bd12e679df7d59cc903`

## Frozen class gate

Every leave-one-15-km-block-out training set fails the predeclared requirement of at least five positive targets.

Training positive counts are only 1–3 in every block split.

The smallest block, 30_296, also contains only one applicable test row and therefore fails the test-row gate.

No R0, R1, R2 or C model is fitted.

## Model accounting

- estimable blocks: **0 / 6**
- model fits: **0**
- prediction rows: **0**
- block-macro log loss: not estimable
- block-macro Brier: not estimable
- primary `C − R2`: **not estimable**

The prediction-table fingerprint corresponds to the empty/header-only prediction surface:

`942a61faf1f2614d1262c5dc373b7222cb035d55ba9fdffd593ada466f689da9`

## Interpretation

RMNP does **not** show that connectivity fails.

It shows that the prospectively frozen AMMA 2021→2022 endpoint contains too few positive future site-use outcomes to support the planned heldout comparison.

This is the mirror image of PNW:

- PNW collapsed toward positives: 108 positive / 3 negative on joint applicable sites;
- RMNP collapsed toward negatives: 3 positive / 66 negative.

Both pass the structural/protocol machinery and fail the endpoint-variation gate before fitting.

## No rescue

The following are forbidden:

- lowering the 5-positive training gate;
- changing AMMA endpoint semantics;
- switching to PSMA/LISY;
- changing 2021→2022;
- changing movement worlds;
- changing spatial blocks;
- changing learner or class weighting;
- selecting a replacement dataset as an RMNP rescue.

A future empirical attempt must be a new protocol/version.

## Current empirical status

There is now **no active prospective/focal-response-unseen empirical candidate** in this connectivity lane.

The next scientifically valid step is not candidate hunting. It is to close the current empirical denominator and extract the methodological lesson about **endpoint-transition estimability** before any future protocol is designed.
