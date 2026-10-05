# eBird island-year survey gate v1.154

## Purpose

The eBird global-islands candidate remains the only live confirmatory candidate after the independent BALA source-loss primary was not supported.

The remaining obstacle is not species occurrence. It is defining, before any species response is opened, **when an island-year was surveyed well enough that later nondetection can be interpreted at all**.

This gate freezes that rule now.

## Official eBird input

Structural requires the official **eBird Sampling Event Data** export for 2002–2019.

Sampling Event Data are checklist-level data. Species rows are not permitted in this gate.

Only rows with `ALL SPECIES REPORTED=TRUE` can contribute to annual survey support.

## Shared-checklist deduplication

Shared eBird checklists can appear once per observer. Counting each shared copy as an independent survey would inflate effort.

Therefore:

- a nonblank `GROUP IDENTIFIER` defines one sampling event;
- blank group identifiers use the sampling-event identifier itself;
- the lexicographically smallest sampling-event identifier is the deterministic representative;
- groups with conflicting date, completeness state, or coordinates differing by more than 1e-6 degrees are excluded from annual support.

No species information is used.

## Island mapping

Checklist coordinates are mapped to the **USGS Global Islands** polygon database, DOI **10.5066/P91ZCSGM**.

The later Dryad island field `ISLAND_ID` is documented to correspond to the Sayre `OBJECTID`.

The mapping is deliberately strict:

- point-in-polygon only;
- zero polygon matches are excluded;
- multiple matches are ambiguous and excluded;
- nearest-island rescue is forbidden.

## Frozen annual survey-support rule

An island-year is marked surveyed only if it contains:

- at least **10** deduplicated complete checklists; and
- sampling in at least **4 distinct months**.

This rule is frozen before the Sampling Event Data support surface or any species response is inspected.

The thresholds are motivated by published eBird completeness work, which treats very small checklist samples as unreliable and uses multi-month temporal support in completeness analyses. The rule here is deliberately simpler: it is a **response-independent survey-support proxy**, not a claim that 10 checklists or four months guarantee species detection.

No duration, distance, observer-count or protocol threshold is imposed at this stage. Those variables are summarized and retained for a later strong reference so that hard filtering is not selected opportunistically.

## What this unlocks

If the official Sampling Event Data pass v1.149 and this v1.154 gate, Structural can freeze:

1. which island-years are eligible;
2. which consecutive three-wave windows have adequate response-independent support;
3. the disjoint burned-pilot and confirmatory partition;
4. only then, the species annual occupancy construction.

The Dryad species archive remains sealed until all four are frozen.

## Claim boundary

This gate produces no bird occupancy result and no conservation evidence.

It only determines where future absences could be defensibly constructed.
