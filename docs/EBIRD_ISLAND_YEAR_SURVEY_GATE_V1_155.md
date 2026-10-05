# eBird island-year survey gate v1.155

This gate sits immediately after the current-schema Sampling Event Data audit (v1.154).

The eBird candidate remains on HOLD because the official checklist-level Sampling Event Data have not yet been supplied. No species response has been opened.

## Frozen rule

Only complete checklists (`ALL SPECIES REPORTED=TRUE`) contribute to survey support.

Shared lists are deduplicated by `GROUP IDENTIFIER`; ungrouped lists use the sampling-event identifier.

Checklist coordinates are assigned only by point-in-polygon to the USGS Global Islands polygons (DOI 10.5066/P91ZCSGM; `OBJECTID`). No nearest-island rescue is allowed.

An island-year is considered surveyed only when it has at least:

- **10 deduplicated complete checklists**, and
- **4 distinct sampled months**.

These thresholds are frozen before species outcomes. They are response-independent support criteria, not a claim of perfect detection.

The rule accepts both current eBird SED v1.16+ protocol headers (`OBSERVATION TYPE`, `PROTOCOL NAME`, `PROTOCOL CODE`) and the legacy `PROTOCOL TYPE` representation.

## Why no additional effort cutoff is frozen

Duration, travel distance, area, observer count and protocol composition are retained and summarized. They are not used here to discard checklists. This avoids selecting a favourable effort threshold before the actual support surface is known.

A later strong reference may include effort covariates, but species outcomes cannot be used to choose the present survey-support rule.

## Next gate

Once the official SED arrives:

1. run v1.154 schema/coverage audit;
2. run v1.155 deduplication + island mapping + island-year survey support on the identical bytes;
3. freeze three-wave windows and burned-pilot/confirmatory partitions from survey support only;
4. only then may species annual occupancy construction be specified.

No bird source-loss effect is computed here.
