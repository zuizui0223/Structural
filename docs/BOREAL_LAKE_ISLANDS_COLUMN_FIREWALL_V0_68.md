# Boreal lake-island documented column firewall v0.68

## Status

The 42-island boreal beetle system remains **below v0.11 intake**.

No safe metadata row value and no beetle/bird/plant matrix value has been opened by Structural.

Dryad file identities are frozen, but two safe-file transport attempts stopped before content:
- v0.66: relative Dryad URL wrapper bug;
- v0.67: resolved Dryad API download endpoint returned HTTP 401.

The next step is therefore **not another blind Dryad retry**.

## What can already be frozen from public documentation

The Dryad README and article describe the safe variables prospectively enough to build a column firewall before row-value access.

### Required geometry / routing

From `alpha_diversity_ALL_islands.csv`:

- `Island`
- `Lat`
- `Long`

These are required before any biological response can open.

### Required classical island / disturbance reference

Also required:

- `log10area`
- `buffer5000`
- `time.since.fire.beetles`

Public documentation defines:

- `log10area` = log10(area + 1);
- `buffer5000` = proportion water within 5 km, with 1 meaning no surrounding land and therefore stronger isolation;
- `time.since.fire.beetles` = years between estimated oldest-tree age and beetle sampling.

This means fire history, area and external isolation can be required in the reference before source-pool information is added.

## Explicitly forbidden response-derived fields

The alpha-diversity file contains response-derived summaries.

These are forbidden from the fresh reference:

- `beetle.richness`
- `bird.richness`
- `plant.richness`
- `beetle.msom.richness`
- `bird.msom.richness`

The RDA file also contains biological-response summaries that are forbidden:

- `plant.richness`
- `frugivore.abund`
- `insectivore.abund`
- `Bird.abundance`
- `Beetle.catch.rate`

No row from those columns may be opened while the candidate remains pristine.

## Prospectively safe habitat structure

The public README documents response-independent habitat measurements in the RDA file, including:

- `charcoal.yes`
- `charcoal.no`
- `Basal.area`
- `deciduous.canopy.cover.percent.a.d`
- `deciduous.understory.cover.percent.a.d`
- `conifer.canopy.cover.perecent.a.d`
- `conifer.understory.canopy.percent.a.d`
- `total.cwd.volume`
- `cwd.dc1` through `cwd.dc5`

Their exact mechanical presence/spelling has **not yet been verified from file bytes**.

Therefore v0.68 freezes them as an allowlist, not as already-open data.

Any unknown RDA header remains closed.

## No response-selected habitat scale

The source paper explicitly chose taxon-specific habitat-amount scales by comparing the relationship between richness and habitat amount.

Therefore `buffer_1` and `buffer_10` are documented variables but are **not automatically admissible to the fresh Structural primary**.

The fresh test must not inherit a habitat scale because it produced a stronger response slope in the source paper.

## Response-independent habitat rule

If exact safe values become available, the primary reference uses habitat structure only under this frozen rule:

1. mechanically verify the predeclared safe headers;
2. retain only prospectively safe habitat variables observed on all 42 islands;
3. select no variable by association with beetle occurrence;
4. if at least two safe habitat variables survive, z-standardize them and compute PCA using safe values only;
5. retain the smallest number of PCs reaching at least 80% cumulative variance;
6. if exactly one safe habitat variable survives, use it directly;
7. if no additional safe habitat-structure variable is complete, STOP before biological response rather than inventing a surrogate after seeing outcomes.

Thus the reference cannot be weakened later to make source-pool information look stronger.

## Current blocker

The blocker is now narrow:

> obtain exact response-independent 42-island safe row values and coordinates through an auditable route.

Acceptable routes include:

- an independent public supplement;
- an author repository;
- prior-study metadata containing the same island IDs/coordinates;
- an exact user-supplied safe file matching the frozen Dryad SHA-256.

Repeated guessing of Dryad download endpoints is not an acceptable route.

## Biological-response boundary

Still unopened:

- beetle 0/1 matrix;
- bird 0/1 matrix;
- plant 0/1 matrix.

The candidate does not yet count as an active fresh system or empirical evidence.

v0.11 intake, burned pilot and confirmation remain unauthorized.
