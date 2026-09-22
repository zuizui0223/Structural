# RMNP Stage 1 authorization v0.25

## Authorized opening

The v0.23 biological protocol and v0.24 response-free reference are merged and frozen.

Stage 1 is now authorized for **2021 AMMA only**.

Allowed fields:

- date
- site_name
- perc_surveyed
- amma

Only the frozen 116 source-pool sites may contribute to the source state. The frozen 69 evaluation sites remain a subset of that source universe.

## AMMA response semantics

The source metadata define:

- 1 = detected
- 0 = not detected
- NA = no data

Therefore the Stage 1 state is frozen as:

- positive: any AMMA=1 in 2021;
- negative: no AMMA=1 and at least one 100%-surveyed 2021 visit with AMMA=0;
- otherwise: non-estimable.

NA is never converted to absence.

This clarification is frozen **before any AMMA value is opened**.

## What Stage 1 may produce

1. 2021 AMMA observed annual site-use state;
2. occupied 2021 source set;
3. 500/1000 m generic and occupied-source connectivity;
4. the complete 69-row R0/R1/R2/C feature table.

## What remains sealed

All 2022 AMMA values remain sealed.

PSMA, LISY and all stage columns remain forbidden for this lane.

Stage 1 may not change:

- taxon;
- transition;
- source/evaluation universe;
- movement worlds;
- 15-km blocks;
- local reference;
- model ladder.

## Next gate

After Stage 1, both the state table and complete feature table must be fingerprinted and merged. Only then may a separate Stage 2 authorization open 2022 AMMA.
