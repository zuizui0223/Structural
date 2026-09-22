# RMNP AMMA temporal connectivity protocol v0.23

## Frozen question

For high-effort Rocky Mountain National Park sites surveyed in both 2021 and 2022:

> **Does connectivity to 2021 AMMA-used breeding waterbodies add held-out information about 2022 observed AMMA site use beyond lagged state, local pond condition and generic pond geometry?**

The focal response remains unopened.

## Evidence class

RMNP is not called pristine fresh.

Prior RMNP occupancy/connectivity results for PSMA and LISY became visible during external literature triage, so those taxa are permanently excluded from this lane.

The focal AMMA response direction has not been inspected. The evidence class is:

`focal_response_unseen_system_context_exposed`

## Focal taxon

Physical response token: `AMMA`.

The current USGS data release for DOI `10.5066/P9EX70L7` identifies the tiger salamander as *Ambystoma mavortium*. The uploaded XML contains a conflicting *Ambystoma maculatum* label and historical NPS pages use *Ambystoma tigrinum*. The analysis retains this nomenclatural caveat and never changes the physical token.

## Dynamic transition

Source: **2021**  
Future target: **2022**

This pair was chosen by the response-independent physical-schema rule before any amphibian response value was opened.

### Source pool

116 2021 sites have:

- valid transformed source-year geometry;
- at least one visit with `perc_surveyed=100`.

### Evaluation pool

69 sites additionally have at least one 100% survey in 2022.

## Endpoint

The endpoint is **observed annual site use**, not latent occupancy.

For a site-year:

- positive = any `AMMA=1` on any visit;
- negative = no `AMMA=1` on any visit and at least one 100% survey;
- otherwise non-estimable.

`amma_stage` is never used.

## Geometry

All connectivity uses 2021 geometry only.

- NAD27 UTM 13N is transformed to NAD83 / UTM 13N;
- NAD83 coordinates are unchanged;
- each site receives the median transformed 2021 coordinate;
- 2022 coordinates cannot repair or alter source geometry.

All 116 high-effort source sites have within-site transformed-coordinate spread <250 m.

## Movement worlds

Two worlds are frozen:

- **500 m**
- **1000 m**

The scale is external to RMNP responses.

Independent tiger-salamander movement evidence reports typical movements of tens to several hundred metres, maximum straight-line distances around 659 m in one tiger-salamander study, and *A. mavortium* movements averaging >400 m and reaching approximately 1 km in another.

The 250 m world is deliberately omitted because the RMNP source-coordinate spread can approach that scale.

No winning radius will be selected.

## Reference ladder

### R0 — lagged state
2021 AMMA observed annual site use.

### R1 — local current state
R0 plus 2021:

- fish ever present;
- median pond length;
- median pond width;
- maximum ordinal depth class.

### R2 — generic pond geometry
R1 plus:

- nearest other source-pool pond distance;
- generic reachability fraction across 500/1000 m worlds;
- generic exponential pond pressure averaged across the two worlds.

### C — occupied-source connectivity
R2 plus:

- occupied-source reachability fraction;
- occupied-source exponential pressure.

The sole primary contrast is **C − R2**.

## Spatial holdout

The 69 evaluation sites were examined under candidate UTM grids using geometry only.

A grid is admissible when:

- at least five blocks exist;
- at least 80% of blocks contain at least three sites;
- median block size is at least five.

The smallest admissible grid is **15 km**, giving six blocks with sizes:

- 23
- 14
- 6
- 16
- 9
- 1

The one-site block remains visible and will be non-estimable if it has fewer than three applicable target rows.

## Evaluation

- split: leave-one-15-km-grid-block-out;
- training class gate: >=5 positive and >=5 negative targets;
- model: fixed L2 logistic regression, C=1;
- preprocessing: training-only imputation/standardization;
- primary metric: block-macro log loss;
- secondary metric: block-macro Brier score.

All four models use identical applicable target rows.

## Two-stage firewall

### Stage 1
Open only 2021 AMMA.

Then freeze:

1. 2021 AMMA site-use state;
2. occupied source set;
3. complete R0/R1/R2/C feature table and fingerprint.

### Stage 2
Only after Stage 1 is merged and CI-green may 2022 AMMA be opened once.

No taxon, radius, reference, block, endpoint or model change is allowed after Stage 1.
