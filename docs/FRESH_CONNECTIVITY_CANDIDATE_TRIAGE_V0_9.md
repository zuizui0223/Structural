# Fresh connectivity candidate triage v0.9

## Current decision

The fresh lane now has **two pending USGS raw-monitoring candidates**, with the Rocky Mountain National Park release ranked first.

No candidate is yet qualified for outcome access.

## Priority 1 — Rocky Mountain National Park amphibians, 1986–2022

Source:

- USGS data release DOI: **10.5066/P9EX70L7**
- Data Catalog identifier: **USGS:657ca143d34e23d35331ce9d**

Public metadata supports the following without opening response values:

- data span **1986–2022**;
- after 2002, data were collected under an occupancy framework;
- waterbodies were visited at least twice during the active season;
- sites were selected within pre-defined catchments using the National Wetlands Inventory, with incidental waterbodies added in the field;
- the USGS catalog classifies the release as spatial data.

The candidate biological operator is fixed provisionally as:

> **whole-individual dispersal among amphibian breeding waterbodies.**

The candidate dynamic endpoint is:

> **future waterbody occupancy/colonization conditional on previous state and a frozen local reference.**

This is still **pending**, not qualified, because two physical-schema questions remain unresolved:

1. Does the released file set contain a reproducible per-waterbody geometry/coordinate key suitable for constructing inter-waterbody connectivity without consulting response outcomes?
2. Can detection/occupancy response fields be physically firewalled while site identity, geometry, local covariates, years and split definitions are frozen?

No species-specific dispersal scale is selected yet. That rule must be frozen from external movement biology or an outcome-blind multi-scale rule before any response access.

### Freshness boundary

A 2025 study later used long-term Rocky Mountain National Park amphibian data to study occupancy/persistence and environmental mechanisms. During this triage we did **not** inspect species-specific response directions or connectivity effects, and connectivity was not the stated mechanism under inspection.

Therefore the candidate remains eligible for metadata/schema-only triage. If future searching exposes the focal response result before protocol freeze, it must be moved permanently to STOP.

## Priority 2 — Pacific Northwest montane ponds, 2012–2013

Source:

- USGS DOI: **10.5066/P13PGN55**
- identifier: **USGS.84c9499d-d840-4277-9ffd-d5d800bca97f**

This remains pending for the same two physical-schema questions: reproducible pond geometry and response-firewall separability.

It is now secondary because it spans only two years, whereas the Rocky Mountain National Park release provides a much longer dynamic occupancy history.

## Permanent STOPs

### Great Lakes frogs, 2011–2023

Dryad DOI: **10.5061/dryad.hmgqnk9v8**

Fresh STOP because public response trends/landscape associations were inspected during discovery.

### Hungary 100 ponds, 2023

Dryad DOI: **10.5061/dryad.70rxwdc6w**

Fresh STOP because response results were inspected and the release does not document reproducible pond coordinates.

## Promotion rule

A pending candidate may advance only through **metadata or physical schema inspection that does not read response values**.

The next admissible step for Rocky Mountain NP is therefore:

    locate physical source files
        → inspect filenames / headers / geometry fields only
        → verify response-column/file separation
        → freeze species, operator scale rule, reference, split and metric
        → v0.5 admission
        → only then consider one-shot response access

No published effect direction may be used to choose species, radius, kernel or endpoint.
