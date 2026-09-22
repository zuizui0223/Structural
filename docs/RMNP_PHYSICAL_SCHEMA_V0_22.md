# RMNP physical schema receipt v0.22

## Decision

The uploaded Rocky Mountain National Park package passes the physical-schema gate **without opening amphibian response values**.

Status:

`advance_to_protocol_freeze`

Evidence class remains:

`focal_response_unseen_system_context_exposed`

## Source snapshot

Two user-supplied files are SHA-pinned:

- `romo_datarelease.xml` — metadata
- `ROMO_data_release.csv` — mixed predictor/response table

The CSV contains 26 columns and 4,886 survey rows. Six response columns are protected:

- psma / psma_stage
- lisy / lisy_stage
- amma / amma_stage

All other columns are metadata, geometry, local habitat or survey-condition fields and may be used only as explicitly frozen by later protocol stages.

No protected value has been summarized or used for candidate selection.

## Taxon boundary

PSMA is consistently defined as *Pseudacris maculata* and LISY as *Lithobates sylvaticus*.

AMMA remains eligible, with an explicit nomenclatural caveat. The uploaded XML abstract identifies tiger salamander as *Ambystoma mavortium*, while one taxonomy/attribute label says *Ambystoma maculatum*. The current USGS data-release page for DOI `10.5066/P9EX70L7` explicitly identifies the tiger salamander as *Ambystoma mavortium*. Historical NPS pages also use *Ambystoma tigrinum*. The protocol therefore binds the physical token `AMMA` to the current USGS release identity *Ambystoma mavortium* while retaining the source inconsistency.

During external movement-literature triage, prior RMNP occupancy/connectivity results for PSMA and LISY became visible. Those two taxa are permanently STOP for the fresh lane. No RMNP-specific AMMA response direction was inspected. The evidence class is therefore not pristine; it is `focal_response_unseen_system_context_exposed`.

## Response-independent transition choice

The dynamic transition is selected by a rule that uses only dates, site names and geometry.

A consecutive pair after 2002 must have:

1. at least 80 common sites;
2. at least 95% source-year coordinate coverage;
3. at least 95% explicit source-year NAD27/NAD83 datum coverage;
4. UTM zone 13.

Five pairs reach the 80-site threshold. Only **2021→2022** satisfies the complete geometry/datum rule.

Therefore 2021→2022 is frozen before any species response value is opened.

## Geometry

2021 contains 123 unique sites. 122 have convertible UTM geometry.

The 2021→2022 intersection contains 93 sites; 92 have valid source-year geometry. `Timber Lake #3` is excluded because source-year coordinate/datum information is insufficient. Safe survey-effort metadata show 70 common sites with at least one 100% survey in both years; 69 of those also have valid source geometry. This 69-site high-effort universe is a response-independent candidate for the biological protocol, not yet an authorized endpoint.

Coordinates are standardized before analysis:

- NAD27 UTM 13N → NAD83 UTM 13N using EPSG:26713 → EPSG:26913;
- existing NAD83 coordinates remain unchanged;
- each site receives the median transformed 2021 easting and northing.

The largest within-site spread after transformation is ~231.97 m.

2022 geometry is never used to construct predictor-side connectivity.

## Spatial holdout

The 92 evaluation sites are assigned response-independently to fixed 10-km UTM grid cells:

`floor(easting/10000), floor(northing/10000)`.

There are 13 blocks. Small blocks remain visible and may later be non-estimable under a predeclared fold-size/class-support gate.

## Next step

The physical schema is now sufficient to freeze the biological protocol.

Before any response access, the protocol must fix:

- species family;
- movement worldsets from external biology;
- source-year local reference;
- R0/R1/R2/C definitions;
- target construction;
- block estimability gate;
- exact preprocessing/model/scoring implementation;
- two-stage 2021-state → feature freeze → 2022-target firewall.
