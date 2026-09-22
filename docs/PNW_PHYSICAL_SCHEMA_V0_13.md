# PNW physical schema and mixed-file firewall v0.13

## Decision

The uploaded Pacific Northwest montane-pond package resolves the two physical-schema questions left open by v0.8/v0.10.

**Physical result:** `advance_to_protocol_freeze_with_design_exposure_caveat`.

**Evidence class:** `response_unopened_design_exposed`.

The system is no longer a pristine fresh candidate because the legacy R analysis code was semantically inspected before a new connectivity protocol was frozen. No legacy code was executed and no focal response value was intentionally inspected, summarized, ranked or used to choose a connectivity model.

## Source snapshot

Four uploaded files are SHA-pinned in `development/pnw_file_role_manifest_v0_13.json`.

Roles:

- metadata questionnaire — metadata;
- FGDC XML — metadata;
- legacy R analysis — code;
- master CSV — **mixed**, because geometry/current-state fields and focal amphibian responses occupy the same table.

The raw files are not committed to this public repository; only fingerprints and derived schema receipts are retained.

## Mixed-file column firewall

The master CSV has 142 columns.

Before a separately authorized response opening, only these ten columns are allowed:

- year
- park
- site
- region
- datum
- UTMzone
- UTMe
- UTMn
- error
- elev.m

Protected response columns include:

- species
- life.stage
- tadpole.stage
- obs1–obs6
- species-specific stranding outcomes

All other columns remain closed by default until explicitly classified.

## Geometry result

Using only the safe columns:

- 1,091 table rows;
- 275 unique sites;
- 425 site-year combinations;
- 219 sites in 2012;
- 206 sites in 2013;
- **150 sites observed in both years**;
- no missing UTM coordinate rows.

The dynamic geometry rule is frozen as:

> For sites observed in both years, use the median 2012 UTM easting and northing per site as the geometry for the 2012→2013 forecast.

This is preferable to repairing 2013 coordinates because it uses only predictor-time geometry.

Among the 150 common sites, only two have multiple 2012 coordinate pairs and the largest within-site spread is about 29.55 m. All use NAD83 / UTM Zone 10.

Across both years, 13 site labels have multiple coordinate tuples and at least one 2013 record is grossly inconsistent. The v0.13 rule does not repair or use those 2013 coordinates.

## Response firewall result

The dataset metadata explicitly places coordinates in `Ryan_mastersheet.csv`, and the physical header contains stable site/year/UTM fields.

The same CSV also contains response values, so file-level opening is too coarse. v0.13 therefore adds a SHA-pinned **mixed-file column firewall**.

The safe-column projection returns only predeclared geometry/identifier columns. Protected values are never returned or summarized. The underlying CSV parser necessarily tokenizes records structurally; this is recorded rather than falsely claiming that protected bytes were never parsed internally.

## Legacy-code exposure

The historical R code was inspected to understand data flow before the mixed-file firewall was formalized. It reveals previous response definitions and modeling choices.

Therefore, from this point forward:

- legacy code may not justify species selection;
- legacy code may not justify the strong reference;
- legacy code may not justify dispersal scale/radius selection;
- PNW cannot count as pristine fresh confirmatory evidence.

This does **not** make the system retrospective in the usual sense: focal response values remain uninspected for the new connectivity question. It remains useful as a prospective-like response holdout and as a real test of the two-stage state/connectivity machinery.

## Next methodological step

Before any protected response value is opened, freeze:

1. the biological operator;
2. the species/endpoint using metadata + external movement biology only;
3. the dispersal-scale rule;
4. the 2012 current-state/reference representation;
5. the geometry/connectivity representation;
6. the 2013 target endpoint;
7. the evaluation unit and metric;
8. a **two-stage response-access contract** in which lagged/current state may be opened first, connectivity features are frozen, and the future target remains sealed until scoring authorization.

PNW is therefore ready for protocol design, not outcome access.
