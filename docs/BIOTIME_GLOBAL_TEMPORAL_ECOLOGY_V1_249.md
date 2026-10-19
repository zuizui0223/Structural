# Structural v1.249 — Global ecological turnover, not just static graph prediction

Date: 2026-10-19

## Research question

**Does occupied-source spatial context genuinely improve next-interval, same-species site-detection transitions, or can the previously observed occupancy-dependent presence/absence log-loss reversal be explained by a calibration-only probability shift?**

This is a distinct ecological question from the original same-year IUCN polygon-based 529-mammal spatial prediction. The original source-map comparison must remain frozen; no original heldout is reopened. New studies use the independent public BioTIME 2.0 temporal ecological database. Do not equate habitat patches with literal oceanic islands without a polygon-based geography crosswalk.

## Why the existing signature cannot establish a biological role inversion alone

The frozen global-mammal class-specific C−R3 log-loss differences are:

| Pilot occupancy stratum | Heldout presence | Heldout absence | Evidence level |
|---|---:|---:|---|
| >=13 | +0.11644 | -0.00580 | exploratory |
| 5–12 | -0.27744 | +0.000430 | sealed prospective species stratum |
| 1–4 | -0.5962587 | +0.000236 | sealed prospective species stratum |

A **constant within-stratum** probability model is an exact counterexample. If R assigns every cell probability a and C assigns every cell probability b, then
D_presence = log(a/b), D_absence = log((1-a)/(1-b)).
For observed opposite-signed pair (D_presence,D_absence), the solution is
b=(1-exp(D_absence))/(exp(D_presence)-exp(D_absence)); a=b*exp(D_presence).

All three existing signed differences are exactly reproducible by a/b constant predictions in the open unit interval. Such models have zero spatial resolution or source-position discrimination. This does NOT prove that original R3 and C were constant or that their genuine heldout graph-null result fails; it proves **class-specific signed mean losses alone do not identify an ecological constraint-to-opportunity mechanism**. A future independent study needs calibration-only controls and discrimination/transition endpoints, without retuning the consumed 529-species response.

This is known-principle score calibration/discrimination nonidentifiability applied to the frozen ecological signature, not a new theorem about probability scores.

## Independent original source and metadata-only evidence

BioTIME 2.0 official Zenodo version 15 April 2025, DOI 10.5281/zenodo.15222193. Original public metadata file publisher MD5 3daed71ed554888309f9f2443a847bea was verified in GitHub Actions run 39203984350, artifact 12164982767. All 708 STUDY_ID values are distinct.

Outcome-blind study-level screening found:
- 356 studies with >=3 calendar years between first/last record and >=5 georeferenced positions;
- 264 with >=5 calendar years and >=10 positions;
- **226** with >=5 calendar years, >=10 positions, >=100 sample events, >=10 identified species: marine 107, terrestrial 61, freshwater 58;
- 89 with >=8 calendar years, >=20 positions, >=1000 sample events, >=20 species.

These are **potential** replication units, NOT verified repeated same-site visits. Realized study duration may include unsurveyed intervening years or shifting sampling locations.

## Stage 2: standardized survey frame, before ecological outcomes

For each of the 226 prospectively screened STUDY_ID, inspect only survey-event keys (study, date, season/month, sample descriptor, plot if available, latitude/longitude, sampling classification). The physical event universe is one unique sampling event, not one species row. Group into fixed georeferenced location-by-year cells. Do not infer absence where a location-year was never sampled. Treat coordinate instability, changing sampling gear, changing season or time-varying detection as separately reported attrition, not as 0→1 colonization.

Verify how many independently re-sampled local sites exist for at least three **observed years**, and how many within-site consecutive-year pairs have comparable effort and season. This frame screening cannot itself supply ecological effects. Sample ID and site ID are not interchangeable when SAMPLE_DESC contains the year.

All current candidate source measurements derive from BioTIME records, whose taxonomic and method coverage varies by study. Biological status remains **retrospective/context-exposed** because the source data have already been published. Any later independently frozen temporal heldout is within this existing released database, NOT an untouched genuinely fresh biological study.

## Stage 3: test with ecological responses (future authorization only)

**Response:** site-level next-year species *detection*, separated into last-year sampled 0→next sampled 1 and 1→0. This is NOT a true extinction/colonization event without a detection model and relevant primary surveys. Derive the study-specific species universe from a training period, and do not infer zero for taxonomic coverage outside that scope.

**Occupancy state:** focal-species fraction of adequately sampled sites occupied at t, never the number of all globally extant populations. Within-species temporal shifts form the preferred estimate; between-species occupancy strata are secondary and may confound life-history or taxonomy.

**Prespecified comparable models** trained without using heldout future responses:
- R0: own-site prior detection, global/site/study prevalence, reference habitat, seasonal sampling and effort, and (where identifiable) sampling-method reliability.
- R1: R0 plus source number, nearest Euclidean occupied-source distance and training-selected, fixed-scale diffuse source pressure, excluding the focal recipient when forming donor features.
- CAL: R1 with training-only intercept/recalibration and *no additional spatial information*, required to distinguish class-specific probability shifts.
- C: CAL plus predeclared within-network source geometric configuration (spatial dispersion/path information), with no outcome-selected graph k, threshold or subgroups.

**Primary estimand:** C−CAL next-survey log-loss averaged over independent study networks/whole heldout years, stratified on t-state class, with honest negatives from surveyed units. Secondary: heldout ranking/discrimination of true sampled 0→1 events and 1→0 events, fixed study-weighted calibration curves, conditional performance beyond R1, and heterogeneity marine/terrestrial/freshwater. A classwise sign difference *without* conditional C−CAL or transition-event improvement must NOT be interpreted as source-opportunity evidence.

Freeze exact strata, heldout blocks, event-denominator thresholds and season/effort rules *before* target interpretation. If the inspected full database lacks sufficient matched site-years or positive transition support, STOP instead of selecting positive studies after outcomes.

## Island versus habitat-fragment claims

BioTIME is global assemblage monitoring, not itself an oceanic-island network map. A literal-island claim needs a time-independent GIS crosswalk of original site coordinates to coastlines/island polygons, separately identifying oceanic versus continental islands where geological history is supportable. No centroids-only shortcut or name-only island classification is enough. Repeat models within at least two independently surveyed archipelagos before generalizing an island-specific contrast. Terrestrial habitat fragments are separate origin strata, never casually pooled as literal islands.

## What this dataset cannot identify

BioTIME species-site abundance/detection histories alone do not establish source-to-target natal identity, realized directional migration, successful establishment or demographic rescue. They cannot verify the four-donor high-order cofailure × q mechanism without a separate measured movement/establishment source. Keep that as a clearly separate mechanism question.

## Integrity

- eBird remains excluded.
- Original A-Islands, Tanzania, global-mammal 529, BALA, Helgeland, Hopson, Gawecka and SW Finland heldout responses are not rerun.
- No source-selected calibration benchmark is fitted in this v1.249 metadata-only stage.
- Main GEB submission SCIENTIFIC HOLD remains.
- Source credentials and contacts are not printed; study citation/permissions must be respected.
