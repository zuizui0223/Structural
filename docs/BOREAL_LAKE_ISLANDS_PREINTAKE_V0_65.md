# Boreal lake-island beetle pre-intake v0.65

## Status

**HOLD before v0.11 intake.**

No beetle, bird or vascular-plant species-matrix value has been opened by Structural.

The current Dryad file identities are frozen metadata-only.

## Why this system is useful

The 2026 Lac la Ronge study provides a compact but unusually clean true-island test bed:

- 42 lake islands;
- six lakes in the Churchill River watershed;
- island area gradient of roughly 1–350 ha;
- mainland-isolation gradient of roughly 0.1–7.9 km;
- fire-history gradient of 1–231+ years;
- one standardized 30 × 30 m sampling plot on each island;
- explicit 0/1 community matrices for beetles, birds and vascular plants;
- response-independent latitude/longitude, area, isolation, fire-history and habitat variables reported separately from the community matrices.

This is not a replacement for the global 5,592-island mammal system. It is a second pristine route to a v0.55 test while the global mammal response remains transport-blocked.

## Primary biological response

The primary taxon is **beetles**.

This was chosen before response access because public source metadata report:

- all 42 islands represented;
- 466 beetle species;
- an explicit binary presence/absence matrix.

The primary file is:

    beetles_speciesmatrix_presenceabsence.csv

Frozen identity:

- bytes: **49,005**;
- SHA-256:
  `01eef34863bfd49fdc68dfae0aec58766a6fcdd1234751a9c75824df9f038be0`.

The endpoint is **observed local assemblage occurrence under the standardized island sampling design**.

It is not automatically complete whole-island occupancy.

Therefore the eventual paper may discuss source-pool information for local insular assemblages, but not contemporary colonization, extinction or rescue from this cross-sectional endpoint alone.

## Secondary taxa

### Birds

- 42 islands;
- 54 species;
- frozen response SHA-256:
  `3838c39a7a94010569ce399a6b19e651f45fa60d0aef1793445dcb6c0b6e201c`.

### Vascular plants

- 42 islands;
- 101 species;
- frozen response SHA-256:
  `fa9bca793c58bf0a88e707c6841ede7513c4ea07662e4f3d6540088d5feea26d`.

Source documentation notes that island BS has empty plant cells because the island burned before vascular-plant sampling.

Birds and plants are prospective secondary replication only. Neither may rescue a failed beetle primary.

## Why fire history belongs in the strong reference

The source study was explicitly designed around pyrodiversity.

A source-pool analysis that omitted disturbance history could mislabel shared fire-history or habitat effects as connectivity.

Therefore the v0.55 reference for this system must represent, before internal source continuity is added:

- time since fire;
- local habitat structure where safely and prospectively available;
- island area;
- mainland isolation;
- taxon-relevant surrounding habitat amount;
- generic spatial/network context.

Only after those variables are represented may the analysis add training-only occupied-source proximity/pressure and internal source continuity.

## Dual-isolation interpretation

### External isolation

Primary available measure:

    buffer5000

The source documentation defines 1 as an island whose 5-km buffer contains no surrounding land, so larger values represent stronger isolation from surrounding land/mainland context.

### Internal source isolation

This must be built from:

- frozen response-independent Lat/Long;
- training occurrences only;
- fixed graph scales determined before response access.

The candidate source coordinate must be distinct from global training occupancy breadth.

## Proposed reference ladder

### R0
- beetle time since fire;
- prospectively safe local habitat-structure controls.

### R1
R0 plus:
- log island area;
- buffer5000 external isolation;
- prospectively safe habitat-amount metric.

### R2
R1 plus:
- generic response-independent island-network context derived from Lat/Long.

### R3
R2 plus:
- training-only global occupied breadth;
- nearest occupied source distance;
- diffuse multi-source pressure.

### C
R3 plus:
- species-conditioned internal source continuity not reducible to those direct/diffuse source terms.

Primary contrast:

    C - R3 heldout log loss

Support requires the v0.55 rule:

- point estimate < 0;
- frozen spatial-cluster bootstrap 95% upper bound < 0.

No extreme-isolation interaction is required.

## Spatial design

Response-independent coordinates are documented for all islands in the source metadata.

Before any species matrix opens, the design must:

1. verify exact Lat/Long schema and completeness;
2. compute nearest-neighbour distances;
3. freeze graph radii from response-independent geometry;
4. create spatial components/blocks;
5. demonstrate at least 3 pilot and 6 confirmatory blocks;
6. freeze the deterministic pilot/confirmatory split.

If the 42-island geometry cannot support those minima, the system stops before response.

No administrative fallback may be selected after outcomes.

## Fixed species universe

The beetle pilot will not use heldout-specific species sets.

After the burned pilot is opened, but before heldout scoring, the fixed beetle species universe is:

> species present on at least two distinct frozen pilot islands.

That same set must be used in every heldout comparison.

Confirmatory occurrences may not define species eligibility.

## Safe metadata firewall

The main response-independent metadata candidates are themselves mixed files.

### alpha_diversity_ALL_islands.csv

Prospectively useful columns include:

- Island;
- Lat / Long;
- log10area;
- buffer5000;
- taxon-specific time since fire;
- buffer_1 / buffer_10;
- fire-history variables where complete.

Richness and MSOM-richness columns are forbidden.

Frozen file identity:

- 3,441 bytes;
- SHA-256:
  `f63b37b3c4c9d5453c53b0b565c4bfb7b8485e017f257fbeea663b20cbf6bddf`.

### RDA_environmental_variables.csv

Potentially useful response-independent habitat variables include basal area, coarse woody debris and vegetation structure.

Response-derived variables such as richness, bird abundance and beetle catch rate are forbidden.

Frozen identity:

- 8,594 bytes;
- SHA-256:
  `30b296c8243d433b8c4aaa2e934dcb9d57b0f909094ad03cfc645babbab61046`.

A column-level firewall must be frozen before any row value is opened.

## Current blocker

File metadata are resolved, but safe-file schema/value transport is not yet frozen.

The next action is safe metadata only.

Do not open:

- beetle matrix;
- bird matrix;
- plant matrix.

If the safe metadata cannot be obtained without breaking the response firewall, this candidate remains HOLD.

## Evidence boundary

This is not yet an active empirical candidate.

- v0.11 intake: not authorized;
- pilot response: not authorized;
- confirmatory response: not authorized;
- counts as empirical evidence: no;
- counts as fresh confirmation: no.
