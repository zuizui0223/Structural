# Fresh connectivity candidate triage v0.8

## Purpose

v0.8 separates **candidate discovery** from **protocol qualification**.

The discovery layer is metadata-only. It decides whether a public dataset may advance to physical schema inspection without opening response values or reading a connectivity result.

Three terminal classes are used:

- **advance_to_schema_audit** — metadata is sufficient to inspect physical files while keeping response values firewalled;
- **pending** — one or more non-response metadata requirements remain unresolved;
- **stop** — the fresh lane is permanently closed for that candidate.

## Primary pending candidate — USGS Pacific Northwest montane ponds

Source:

- USGS data release DOI: **10.5066/P13PGN55**
- catalog identifier: **USGS.84c9499d-d840-4277-9ffd-d5d800bca97f**

Public metadata states that the release contains two years (2012–2013) of pond-breeding amphibian visual-encounter surveys from Olympic, Mount Rainier and North Cascades National Parks, with site and survey attributes and associated hydrologic data.

This is attractive because the source is a raw monitoring release rather than a connectivity paper.

Working biological operator:

> whole-individual dispersal among breeding ponds.

Candidate endpoint:

> year-2 pond occupancy conditional on year-1 state and frozen local/hydrologic reference.

However, v0.8 does **not** yet qualify it. Two response-blind metadata questions remain:

1. Are pond coordinates or another reproducible geometry physically present in the data release?
2. Can the response table/columns be physically separated from the metadata needed to freeze geometry, references and splits?

Until both are verified without reading response values, the status is:

`pending`

not qualified.

## STOP — Great Lakes frog monitoring

Dryad DOI: **10.5061/dryad.hmgqnk9v8**

This dataset is structurally excellent: 2011–2023, 1,550 point locations, 747 wetlands, site/point/year/lat/long and landscape covariates.

But during candidate discovery the project inspected public result text reporting occurrence trends and landscape associations.

Therefore:

`response_result_seen_by_project = yes`

and the candidate is permanently STOP for fresh confirmation.

It may later become a retrospective engineering dataset, but never fresh evidence.

## STOP — Hungary 100-pond amphibian dataset

Dryad DOI: **10.5061/dryad.70rxwdc6w**

The dataset contains 2023 repeated detection surveys at 100 ponds, but the release does not document reproducible pond coordinates. During triage the project also inspected published detection results.

It therefore remains outside the fresh lane.

## Why v0.8 is strict

A dataset does not become fresh merely because our exact connectivity model was not used in the original publication.

Once the project has seen the response result strongly enough to influence candidate, scale or endpoint choice, the response-blind guarantee is gone.

Likewise, a dataset with no reproducible geometry cannot support a connectivity protocol by digitizing a published map after the outcome is known.

## Next action

The only active fresh candidate is the USGS Pacific Northwest montane-pond release, and it is still **pending**.

Next work is limited to metadata/file-schema inspection that answers the two unresolved questions above. No amphibian presence values may be opened during that step.
