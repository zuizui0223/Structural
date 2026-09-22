# RMNP Stage 2 authorization v0.28

## Authorization

The AMMA 2021 source state, occupied-source anchors, full 69-row feature table and exact scoring implementation are merged and frozen.

Stage 2 is therefore authorized **once** for 2022 AMMA.

## Allowed target opening

Only 2022:

- date
- site_name
- perc_surveyed
- amma

may be used.

The same source metadata semantics apply:

- positive: any AMMA=1;
- negative: no AMMA=1 and at least one 100%-surveyed visit with AMMA=0;
- NA: no data, never absence;
- otherwise non-estimable.

## Applicability

A site may enter scoring only if it:

1. is in the frozen 69-site evaluation universe;
2. has estimable 2021 lagged state;
3. has estimable 2022 target.

No additional response-dependent filter is permitted.

## Frozen scoring

All four models use the same applicable rows.

Heldout unit: frozen 15-km block.

A block is scored only if:

- it has at least 3 applicable test rows;
- training has at least 5 positives;
- training has at least 5 negatives.

Primary: block-macro heldout log loss.

Secondary: block-macro Brier.

Primary contrast: **C − R2**.

## No rescue

After 2022 AMMA is opened, no source, feature, scale, block, preprocessing, learner, target or gate may change.

Non-estimability is retained as a terminal result if the frozen design cannot support scoring.
