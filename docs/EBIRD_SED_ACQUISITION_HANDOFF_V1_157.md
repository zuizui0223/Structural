# eBird Sampling Event Data acquisition handoff v1.157

## Current status

The only live prospective candidate is **global eBird islands 2002–2019**.

All response-independent scientific rules required before species response access are already frozen:

- SED schema/coverage audit: `development/ebird_sampling_event_metadata_audit_contract_v1_154.json`
- island-year survey support: `development/ebird_island_year_survey_contract_v1_155.json`
- same-byte audit chain: `development/ebird_sed_support_chain_contract_v1_156.json`

No eBird species-response row may be opened until the official checklist-level Sampling Event Data pass this chain.

## Official product to request

Request the **eBird Basic Dataset Sampling Event Data** product, not the species-observation EBD table and not the public API.

The Sampling Event Data must contain checklist-level fields including:

- SAMPLING EVENT IDENTIFIER
- OBSERVATION DATE
- LATITUDE / LONGITUDE
- OBSERVATION TYPE + PROTOCOL NAME (current schema) or PROTOCOL TYPE (legacy schema)
- PROTOCOL CODE
- DURATION MINUTES
- EFFORT DISTANCE KM
- EFFORT AREA HA
- NUMBER OBSERVERS
- ALL SPECIES REPORTED
- GROUP IDENTIFIER

The Structural analysis years are frozen as **2002–2019**. If the official download is not date-subsettable, obtain the official SED file and let the frozen audit ignore rows outside 2002–2019.

## Data-request description

Suggested project title:

**Occupancy-state dependence of island connectivity and source-loss leverage**

Suggested research-purpose text:

> This project tests whether the ecological information associated with occupied source islands depends on species occupancy state, and whether losses of spatially distinctive occupied source islands predict later contraction in island occurrence. We require eBird Sampling Event Data only to establish response-independent checklist completeness, effort, temporal coverage, and island-year survey support before any species-level annual occupancy is constructed. The primary prospective candidate is a global non-marine island analysis for 2002–2019. Only complete checklists will later support nondetection, and all survey-quality, island-mapping, three-wave window, pilot/confirmation, source-leverage, and scoring rules will be frozen before species response access.

Do not describe the project as estimating rescue, extinction prevention, or realized dispersal; the present protocol tests held-out occurrence prediction only.

## After approval/download

Keep the original official SED file unchanged.

Run:

```bash
python scripts/run_ebird_sed_handoff_v1_157.py \
  /path/to/official_sampling_event_data.txt.gz \
  /path/to/USGS_Global_Islands.gpkg \
  --output-dir /path/to/ebird_v157
```

The island geometry must be the public USGS **Global Islands** dataset (DOI **10.5066/P91ZCSGM**) containing stable `OBJECTID` polygons. Structural maps checklists by strict point-in-polygon only; nearest-island rescue is forbidden.

The launcher executes the frozen v1.156 chain and then checks that:

- v1.154 and v1.155 used identical SED bytes;
- no species-response headers were present;
- no species detection/nondetection was read or constructed;
- the annual support surface uses at least 10 deduplicated complete checklists and 4 sampled months per island-year;
- raw SED rows are not copied to the output directory.

## What success does — and does not — authorize

A successful v1.157 handoff still contributes **zero biological evidence**.

It authorizes only the next response-independent step:

> freeze eligible three-wave windows and disjoint burned-pilot/confirmatory partitions from the surveyed island-year support surface.

It does **not** authorize opening the Dryad observed-species archive.
