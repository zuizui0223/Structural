# RMNP 2021 pre-response reference state v0.24

## Decision

The v0.23 AMMA protocol now has a frozen **response-free 2021 reference state**.

No AMMA, PSMA or LISY value has been opened.

## Identifier normalization

The raw source contains trailing whitespace in some 2022 site names. Before any response access, site identifiers are frozen as:

> strip leading and trailing whitespace only.

This changes the 2021→2022 common-site count from 92 under raw-string identity to **93** under normalized identity. One concrete case is `Dutchtown Campsite Pond ` in 2022 versus the same name without the trailing space elsewhere.

No fuzzy matching, alias repair or coordinate-based renaming is permitted.

## High-effort universe

Using only safe metadata:

- 2021 source pool: **116 sites**
  - valid transformed 2021 geometry;
  - at least one 100% survey in 2021.
- both-year high-effort common sites before geometry gate: **70**
- final evaluation universe: **69 sites**
- excluded for missing source-year geometry: `Timber Lake #3`

The evaluation universe is now frozen before AMMA access.

## Geometry

All connectivity geometry comes from 2021 only.

- NAD27 UTM Zone 13 is transformed from EPSG:26713 to EPSG:26913;
- NAD83 UTM Zone 13 is retained;
- each site receives the median transformed 2021 coordinate;
- 2022 coordinates are never used.

## Local reference

The frozen R1 physical/current-state variables are:

- fish ever present in 2021;
- median 2021 site length;
- median 2021 site width;
- maximum 2021 depth category encoded 0/1/2.

Missingness among the 116 source sites:

| variable | missing |
|---|---:|
| fish | 0 |
| site length | 4 |
| site width | 5 |
| max depth | 0 |

Among the 69 evaluation sites, only two length and two width values are missing. The already-frozen training-fold median + missingness-indicator rule will apply after response opening.

## Spatial blocks

The 69 evaluation sites occupy six frozen 15-km UTM blocks:

- 28_297: 23
- 28_298: 14
- 29_296: 6
- 29_297: 16
- 29_298: 9
- 30_296: 1

The one-site block remains visible and may later be non-estimable under the frozen test-row gate.

## Reference fingerprint

The canonical 116-row source/reference table has SHA-256:

`1680ffd22cb5c524b32be668f9bb1a7e19c8ffacdb9d3ef44c8eebdc7538769c`

The derived bytes remain in the working evidence package rather than the public repository.

## Next irreversible step

A separate Stage 1 authorization must now pin v0.23, this reference fingerprint, AMMA, the 500/1000 m worldset, and the exact 2021-only response fields.

Only after that authorization is merged and CI-green may 2021 AMMA state be opened.
