# Boreal safe-row projection v0.74

## Purpose

v0.74 prepares Stage B before any real mixed-file row value is opened.

It can run only after a separate repository revision has frozen the exact
Stage-A header manifests and explicitly authorized safe-row projection.

## Geometry projection

From `alpha_diversity_ALL_islands.csv`, the runner requests only:

- `Island`
- `Lat`
- `Long`

All richness/occupancy-response columns remain protected and all other columns
remain closed.

A successful geometry projection must contain exactly the frozen 42 island IDs,
once each, with finite decimal-degree coordinates in valid latitude/longitude
ranges. No coordinate repair or map digitization is allowed.

The emitted geometry CSV stores numeric values using Python's exact hexadecimal
float representation for deterministic replay.

## Habitat projection

From `RDA_environmental_variables.csv`, the runner requests only `Island`
plus the six prospectively documented local habitat-structure variables frozen
in v0.71.

For each habitat column, the decision rule is fixed before row access:

1. all 42 values must be present, numeric and finite;
2. complete zero-variance columns are excluded;
3. complete nonconstant columns survive;
4. population mean and population SD (denominator n=42) are frozen using Python `math.fsum` accumulation so row order cannot change the frozen constants;
5. zero survivors → STOP before biological response;
6. one survivor → later reference is its population z-score;
7. two or more survivors → later reference follows the already-frozen v0.68
   deterministic PCA rule.

No species response can affect this selection.

## What v0.74 does not do

- it does not run until a real header-manifest freeze exists;
- it does not fit the PCA yet;
- it does not construct the spatial graph yet;
- it does not open beetle, bird or plant responses;
- it contributes zero empirical evidence;
- it does not authorize v0.11.

The point is to ensure that once Stage A clears, safe predictor access itself is
mechanical rather than improvised after seeing the file rows.
