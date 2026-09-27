# Boreal lake-island thesis safe table v0.69

## What is now resolved

The current boreal study uses **42 islands**.

Without opening any beetle, bird, or plant matrix, Bell's 2024 thesis Table 2.1 supplies all 42 island codes together with response-independent:

- island area;
- distance to mainland;
- time since fire standardized to 2020;
- fire-history source.

The species-richness columns printed in the same source table are deliberately discarded and are not persisted in Structural.

The machine-readable safe table is:

    development/boreal_lake_islands_thesis_safe_rows_v0_69.csv

## Complete core external state

Coverage is now:

- island identity: **42 / 42**
- area: **42 / 42**
- distance to mainland: **42 / 42**
- TSF: **42 / 42**
- fire-history source: **42 / 42**
- exact latitude/longitude: **0 / 42**

The recovered raw ranges are:

- area: **1.0–350.4 ha**
- mainland distance: **0.02–7.90 km**
- TSF: **1–231 years**

No biological matrix was used.

## Prospective external reference

Because direct mainland distance is independently available for every island, v0.69 prospectively replaces inaccessible `buffer5000` as the **required** external-isolation variable.

The frozen transforms are:

    log_area = log10(area_ha + 1)
    external_isolation = log1p(distance_to_mainland_km)
    disturbance_history = z(TSF)

computed only from the frozen 42-island safe table.

`buffer5000` may later be added only if its exact response-independent bytes become independently available; it is not required for fresh eligibility.

This is a pre-response design refinement, not a response-driven substitution.

## Why TSF must remain in the strong reference

The source study explicitly reports that time since fire and isolation are positively correlated.

Therefore a source-pool signal cannot be interpreted cleanly unless disturbance history is already represented in the reference.

v0.69 makes that requirement practical because TSF is complete for all 42 islands independently of the biological matrices.

## What is still unresolved

The remaining blockers are no longer the classical island-state variables.

Still unresolved:

1. exact island-to-lake membership in a machine-readable auditable table and/or exact per-island latitude/longitude;
2. a prospectively safe local habitat-structure reference, if one can be recovered independently.

No exact coordinates are inferred by visually digitizing the published map.

## Spatial-design consequence

If exact coordinates remain unavailable but island-to-lake membership can be recovered response-independently, a future protocol may freeze a **within-lake internal source-pool operator** instead of inventing a geographic graph:

- lake identity is response-independent;
- within-lake source fraction is training-only;
- global occupied breadth belongs in R3;
- within-lake occupied source support belongs in C;
- the same operator is used for all heldout islands;
- lake membership and pilot/confirmatory allocation must be frozen before beetle response access.

That design is not yet authorized. It becomes eligible only if the full 42-island lake-membership crosswalk is independently auditable.

## Response boundary

Still unopened:

- beetle matrix;
- bird matrix;
- plant matrix.

v0.69 remains predictor/provenance work only and contributes zero empirical evidence.
