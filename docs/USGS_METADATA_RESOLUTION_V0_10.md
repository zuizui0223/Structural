# USGS metadata resolution v0.10

## Why this layer exists

The user-supplied USGS metadata URL resolves an important ambiguity:

> a dataset landing page is **not** the same thing as a resolved physical data schema.

For the Pacific Northwest montane-pond candidate, the public catalog exposes two DCAT resources:

1. **Digital Data** → the DOI landing page;
2. **Original Metadata** → the XML metadata file.

The catalog surface does **not** expose the underlying spreadsheet/CSV/R-code file inventory. Therefore the candidate cannot yet be promoted from metadata triage to protocol freeze.

## v0.10 physical-schema gate

A pending candidate advances only when all of the following are true:

- the source landing is resolved;
- the actual file-level distribution is resolved;
- a reproducible geometry/site key is physically verified;
- response fields/files can be firewalled before model design;
- no response value has been read.

This is stricter than merely finding a DOI or a map.

## Pacific Northwest montane ponds

DOI: **10.5066/P13PGN55**

The public Data.gov/DCAT record confirms a public dataset and describes two years of pond-breeding amphibian surveys plus R code and hydrologic resources.

However, its two visible distributions are only:

- DOI landing page;
- original XML metadata.

Current state:

`pending_physical_schema`

Unresolved:

- actual file inventory;
- physical coordinate/geometry fields;
- physical separation of response values from predictor/schema metadata.

## Rocky Mountain National Park

DOI: **10.5066/P9EX70L7**

The catalog confirms a long spatial monitoring release, occupancy-framework surveys after 2002, repeated within-season visits, and public/CC0 access.

But the current tool path cannot resolve the file-level ScienceBase inventory. Direct automated metadata fetch also returned HTTP 403.

Current state:

`pending_physical_schema`

This is an **access/infrastructure boundary**, not a scientific STOP.

## Operational rule

The sequence is now:

    metadata-only triage
        → DOI/catalog resolution
        → file-level distribution resolution
        → geometry verification
        → response-firewall verification
        → protocol freeze
        → v0.5 admission
        → only then response access

No candidate may skip from DOI discovery directly to model fitting.
