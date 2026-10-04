# Source-loss leverage candidate triage v1.127

## Candidate 1 — global eBird islands 2002–2019

Dryad DOI: **10.5061/dryad.8931zcrpc**

Metadata are unusually promising:

- 18 annual waves (2002–2019);
- 4,205 represented islands;
- stable `ISLAND_ID` linked to the Sayre global islands database;
- global non-marine bird observations;
- the original study reports 1,644 islands as well surveyed annually.

This is the strongest current candidate for an independent occupancy-regime/source-loss test.

However, the Dryad archive description lists **observed species rows** with `SCI_NAME`, `SUB_ID`, coordinates and `ISLAND_ID`. It does not by itself establish that an unlisted species on an island-year is a valid absence.

Therefore the candidate is **HOLD_METADATA_INCOMPLETE**, not qualified.

The next safe action is metadata/schema resolution only:

1. determine whether the archived eBird submissions are complete checklists;
2. determine whether sampling effort / checklist completeness metadata are present or can be crosswalked without opening species outcomes;
3. freeze an island-year survey-quality rule before any species-level annual occupancy matrix is constructed.

Do not open the 464 MB species archive merely to see whether a favourable source-loss pattern exists.

## Candidate 2 — Apostle Islands carnivores 2014–2017

The system is ecologically attractive:

- actual islands;
- four monitoring years;
- 19 monitored islands;
- 160 camera traps;
- 49,280 trap nights;
- explicit occupancy/detection modelling.

But published reports already expose island-level occupancy and distribution outcomes.

Therefore it is **STOP_RESPONSE_EXPOSED** for fresh confirmation.

It may be useful later only as a retrospective implementation test.

## Current priority

1. resolve eBird checklist/effort semantics without opening species response values;
2. keep Apostle Islands out of the fresh evidence chain;
3. continue searching only for independent three-wave systems whose future species outcomes remain uninspected.
