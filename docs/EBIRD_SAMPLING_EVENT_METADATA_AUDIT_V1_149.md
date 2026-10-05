# eBird Sampling Event Data audit v1.149

## Purpose

The eBird global-islands candidate remains on HOLD because the Dryad archive contains observed species rows, not a defensible nondetection surface.

Official eBird documentation states that Sampling Event Data contain one row per checklist and can be used to establish species absence when the checklist is complete. Cornell's eBird best-practices workflow likewise uses the Sampling Event Data to zero-fill species not reported on complete checklists.

Structural therefore freezes the checklist-metadata audit **before** obtaining or inspecting the species response.

## What v1.149 does

The audit accepts only checklist-level Sampling Event Data and requires:

- sampling event identifier;
- date and coordinates;
- protocol type/code;
- duration, distance, area and observer-count effort fields;
- `ALL SPECIES REPORTED`;
- group identifier.

If species-response headers such as `SCIENTIFIC NAME` or `OBSERVATION COUNT` are present, the audit stops.

The audit emits only aggregate support summaries:

- complete/incomplete checklist counts by year;
- monthly temporal coverage;
- protocol composition;
- fixed effort bins and missingness;
- duplicate group frequency.

It does **not**:

- open the Dryad eBird species archive;
- infer species absence;
- map checklists to islands;
- choose effort thresholds;
- construct source-loss events.

## Why the effort bins are not thresholds

The fixed bins are descriptive only. A later contract may freeze a survey-quality rule after this response-independent support surface is known, but before species outcomes are opened. That later rule cannot be chosen from source-loss or persistence effects.

## Geometry remains a separate gate

Sampling Event Data do not supply the Dryad `ISLAND_ID`. After the SED support audit succeeds, Structural must freeze a response-independent checklist-to-island crosswalk using the Sayre global-islands geometry (the Dryad `ISLAND_ID` corresponds to Sayre `OBJECTID`).

Only after checklist completeness, effort quality and geometry mapping are all frozen may species annual occupancy be constructed.

## Current state

No eBird species response has been opened for Structural source-loss analysis. v1.149 is implementation-ready but cannot execute until an official eBird Sampling Event Data extract is supplied.
