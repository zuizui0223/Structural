# Boreal lake-island thesis safe table v0.69

## What is now resolved

The current boreal study uses **42 islands**.

Without opening any beetle, bird, or plant matrix, the island identity universe can now be reconstructed exactly from independent public thesis/article material.

Bell's 2024 thesis Table 2.1 provides 38 island rows with response-independent:

- island code;
- island area;
- distance to mainland;
- time since fire standardized to 2020;
- fire-history source.

The same thesis Figure 2.1 shows four additional current-study island labels absent from Table 2.1:

- **SR**
- **TB**
- **WD**
- **WF**

The union is exactly 42 unique island codes.

The 2026 article independently reports 42 study islands and explicitly mentions TB, providing an additional cross-source check.

No community matrix was used to recover the island universe.

## Safe attributes currently available

For **38 / 42** islands, v0.69 records:

- area (ha);
- distance to mainland (km);
- TSF in 2020;
- fire-history source.

Species richness columns visible in the thesis table were deliberately discarded and are not stored in the v0.69 object.

## Why the four extra islands are not filled in

The four current-study codes SR, TB, WD, and WF are real members of the 42-island universe, but their safe attributes have not yet been recovered from an independent source.

Their:

- area;
- mainland distance;
- TSF;
- latitude;
- longitude

remain unresolved.

Nothing may be inferred from the beetle/bird/plant matrices, from response-derived richness, or by eyeballing Figure 2.1.

## Cross-source completeness check

The 38-row thesis subset has maximum area **350.4 ha**.

The 2026 article reports the full 42-island range extending to roughly **380.7 ha**.

That mismatch is useful: it independently demonstrates that Table 2.1 is not the full current 42-island sample and prevents accidental promotion of the 38-row table to the contemporary universe.

## Current geometry state

Island identity:

- **42 / 42 resolved**

Area / mainland distance / TSF:

- **38 / 42 resolved**

Exact plot-center latitude/longitude:

- **0 / 42 resolved in the frozen Structural safe table**

The original source metadata are documented to contain Lat/Long, but Dryad content transport returned HTTP 401 before any safe-file bytes.

## Next gate

Before v0.11 intake, recover response-independently:

1. SR / TB / WD / WF area;
2. SR / TB / WD / WF mainland distance;
3. SR / TB / WD / WF TSF;
4. exact Lat/Long for all 42 islands.

Then mechanically reconcile the full 42-code universe and only then freeze spatial graph scales and pilot/confirmatory blocks.

## Response boundary

Still unopened:

- beetle matrix;
- bird matrix;
- plant matrix.

v0.69 is predictor/provenance work only and contributes zero empirical evidence.
