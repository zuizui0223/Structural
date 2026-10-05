# Finnish common eider retrospective source-loss pre-intake v1.150

## Why this candidate remains useful

Before the BALA result was known, Structural registered the Finnish Archipelago Bird Census common-eider dataset as the preferred **retrospective** stress-test option.

The public record describes:

- 3,648 islands;
- 18,516 island-year counts from 1997–2020;
- stable `Island_ID`;
- breeding-pair counts (`Eider_pairs`);
- repeated archipelago bird censuses;
- environmental/island covariates;
- a `pos2` spatial-distance object.

That is enough to justify a schema audit, but not enough to justify a source-loss score.

## Why this cannot be confirmatory

The published paper already reports a strong decline and spatial redistribution of eiders, so the broad temporal response direction is known.

In addition, the methods state that some counts reported for groups of multiple islands were redistributed to individual islands using information from other years or island size. On average about 6.2% of observations per year were affected.

Structural therefore fixes this lane as **retrospective only**. It cannot rescue the failed BALA primary or count as independent confirmation.

## Three gates that matter

### 1. Surveyed zero

A source-loss analysis requires knowing that `Eider_pairs = 0` means a surveyed island with no breeding pairs.

Missing island-years must remain missing/unsurveyed and may not be converted to zeros.

### 2. Exact spatial support

The public metadata say latitude and longitude are standardized and rounded to one decimal for sensitivity reasons. Those values are inadequate for a fine topology-specific source-leverage analysis by themselves.

The archive also describes `pos2`, a distance matrix based on 2 × 2 km grid-cell coordinates. The schema audit must determine whether this object is actually present, exact enough for the intended retrospective stress test, and keyed reproducibly to `Island_ID`.

### 3. Reconstructed grouped-island counts

If rows created by redistributing grouped-island counts cannot be identified, an apparent source loss or recolonization can be a data-construction artifact.

The retrospective lane therefore stops unless those rows are identifiable and can be excluded under a rule frozen before any source-loss effect is calculated.

## What a passing audit would allow

Only after all three gates pass may Structural freeze a retrospective three-wave rule.

The preferred comparison is the same conservation question used for BALA:

> holding source-loss count fixed, do losses of spatially higher-leverage occupied sources precede greater contraction of other island populations?

Any such result remains a retrospective stress test and cannot change BALA's confirmatory non-support.
