# PNW Stage 2 result v0.21

> **Status note (superseded current-lane text):** this document is the historical v0.21 PNW result. Its final “Active lane” paragraph described project status at that time. Current status is defined by registry v0.29 and the v0.40 admission freeze: PNW and RMNP are both terminal non-estimable, there are no active empirical candidates, and the live confirmatory queue is empty.

## Terminal result

The authorized 2013 RACA target was opened once under the frozen v0.19 authorization and v0.20 scoring implementation.

The programme terminates as:

> **non-estimable before any model fit**

This is neither favorable nor adverse evidence for typed connectivity.

## 2013 target

Across the frozen 150-site feature universe:

- positive: **117**
- negative: **3**
- non-estimable: **30**

After also requiring estimable 2012 lagged state:

- joint applicable sites: **111**
- positive: **108**
- negative: **3**

Target-table SHA-256:

`998961d32a7bd968744de61d2feb8afdb1188df7f8009228c9940f07e09b44a4`

## Frozen class gate

Every leave-one-2012-region-out training set fails the predeclared requirement of at least five negative targets.

Training negative counts are only 2–3 in every region split.

Additionally:

- DaggerTwisp has zero applicable heldout rows;
- Hwy20 has zero applicable heldout rows.

Therefore no R0, R1, R2 or C model is fitted.

## Model accounting

- estimable regions: **0 / 10**
- model fits: **0**
- prediction rows: **0**
- region-macro log loss: not estimable
- region-macro Brier: not estimable
- primary `C − R2`: **not estimable**

The prediction-table fingerprint corresponds to the empty/header-only prediction surface:

`9b4f5c5bb59ad027afd59122c621e9bbe9120e4d1074ebb287abf6020a036e3d`

## Interpretation

PNW does **not** say that connectivity fails to help.

It says that, under the prospectively frozen dynamic endpoint and class-support gate, the 2013 target has insufficient negative variation to support the planned heldout comparison.

This is a useful boundary result:

> a connectivity representation can be fully specified and response-separated yet remain empirically untestable because the future endpoint lacks enough variation.

## No rescue

The following are forbidden:

- lowering the 5-negative training gate;
- changing species;
- changing the 2013 endpoint;
- changing the worldset;
- changing the heldout regions;
- fitting a different learner to force a score;
- relabelling this as an adverse result;
- selecting a replacement dataset as a PNW rescue.

A future empirical test must be a new separately frozen protocol.

## Active lane at v0.21 — superseded

PNW was closed at v0.21.

At that time, the Rocky Mountain National Park long-term amphibian release remained the next pristine-fresh candidate. That status was later superseded by the completed RMNP workflow; RMNP is now also terminal non-estimable.
