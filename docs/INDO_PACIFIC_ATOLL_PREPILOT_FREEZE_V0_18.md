# Indo-Pacific atoll plants pre-pilot freeze v0.18

## Scientific purpose

This is the first fresh island system admitted after the Structural gate-first infrastructure was frozen.

The hypothesis is the A-Islands-derived **source-pool handoff** prediction:

> under extreme isolation from continents or large high islands, native plant occurrence should depend increasingly on continuity with occupied insular source networks rather than on generic major-landmass access alone.

A-Islands is discovery evidence only. It does not count as confirmation here.

## Response-independent geometry

The physical graph retains all **310 atolls**. Eighteen atolls lack the frozen rainfall covariate and therefore cannot be model targets, but remain physical intermediate nodes.

The model-target universe contains **292 atolls**.

Frozen nearest-neighbour graph radii are:

- 36 km;
- 58 km;
- 126 km;
- 233 km.

The largest/coarsest admissible spatial partition is 233 km, yielding **63 target-populated spatial components**:

- 13 burned-pilot blocks;
- 50 confirmatory blocks.

The source-pressure length scale is 57.820370321631 km.

The primary extreme-isolation threshold is the response-independent upper quartile of major-landmass distance among the 292 model-target atolls:

**775.3375 km**.

q70 = 720.81 km and q80 = 900.914 km are sensitivity checks only and may not rescue a failed q75 primary.

## v0.31 feasibility protocol

Protocol fingerprint:

`0ffd3ced3e09b94bd001ea5dea036253cdd5bf1c0969ebc117431631bdf6a129`

The pilot is estimability-only.

Frozen gates inherit the established v0.30 defaults:

- minimum held-out applicable rows = 3;
- minimum training positives = 5;
- minimum training negatives = 5;
- minimum estimable spatial blocks = 3.

No pilot effect size or predictive score is permitted.

## Fold-specific native occurrence endpoint

The species universe is not read globally from the response.

For each held-out pilot spatial block:

1. use only the other burned-pilot blocks;
2. identify species with at least one native code `N` in those training blocks;
3. treat those species as the fold-specific test universe;
4. within each source-designated complete vascular-plant inventory in the held-out block:
   - `N` = 1;
   - `I` = 0;
   - no row for the training-defined species = 0.

Thus held-out species occurrence never defines its own eligibility or source state.

A block with no complete held-out catalogue or no applicable training-defined species receives one missing-target sentinel row and can fail v0.42 response-quality survival.

## v0.42 response-quality contract

Quality-contract fingerprint:

`056dffbd219716ae06f2bbe4eac37acb653f524a4bf8fe130d0a04d3b63c084a`

At least 3 burned-pilot spatial blocks must retain at least the frozen minimum test rows.

No block may be rescued by:

- adding an excluded rainfall-missing atoll;
- imputing rainfall;
- merging blocks;
- substituting country or source group after response access;
- lowering the minimum;
- changing native/introduced semantics.

## Monolithic-response firewall

The source plant table is one response file spanning all atolls.

Before pilot access, the router is frozen to decode:

- the **atoll field only** for every row, solely to route it;
- species and presence only after the atoll is proven to belong to a frozen burned-pilot block.

For confirmatory rows and the 18 response-independent target-excluded atolls:

- species bytes are not Unicode-decoded;
- presence bytes are not Unicode-decoded;
- they are not logged;
- they are not summarized;
- they are not counted by class;
- they are not retained.

Synthetic tests place invalid UTF-8 in sealed species/presence fields and require the router to succeed, proving those fields are not decoded.

## Evidence ceiling

Before the one-shot pilot:

- empirical effect estimate: none;
- predictive score: none;
- confirmatory response access: false;
- confirmatory evidence contribution: zero.

A clean pilot can only enter the existing v0.42 admission chain. It cannot itself confirm source-pool handoff.
