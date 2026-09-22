# PNW temporal connectivity protocol v0.15

## Frozen question

For Rana cascadae sites observed in both 2012 and 2013:

> **Does 2012 occupied-source connectivity add held-out information about 2013 observed site use beyond 2012 site state, local habitat and generic pond geometry?**

This is a prospective-like response holdout inside a permanently design-exposed dataset. It does not count as pristine fresh evidence.

## Why Rana cascadae

The taxon is listed in the source metadata. The scale rule is not derived from the legacy R code.

Independent mark-recapture/telemetry work shows that Cascades frogs move among separated aquatic resources and across basins, with common movements on the order of hundreds of metres and documented dispersal extending beyond 1 km; broader comparative work reports movements between habitat patches up to approximately 5.2 km.

No single distance is selected from the PNW data.

## Frozen movement worldset

    250 m
    500 m
    1000 m
    1500 m
    5000 m

All five scales survive as declared worlds. The outcome is never used to select one.

## Response construction

The endpoint is **observed site use**, not latent true occupancy.

For each site-year:

- species token = RACA;
- at least two valid survey visits are required;
- presence = any RACA observation >0;
- absence = at least two valid surveys and no positive RACA observation;
- otherwise the site-year is non-estimable.

All life stages contribute to species-level site use. No post-outcome life-stage tuning is allowed.

## Geometry

All source geometry is from 2012.

- 2012 source pool: all physically valid 2012 sites;
- evaluation targets: sites observed in both years;
- site coordinate: median 2012 UTM easting/northing;
- self-source is excluded;
- 2013 coordinates are never used.

## Reference ladder

### R0 — temporal state

- 2012 target-site RACA state.

### R1 — current local state

R0 plus 2012:

- elevation;
- maximum pond size;
- maximum depth;
- wooded perimeter percentage;
- fish state.

### R2 — current state + generic geometry

R1 plus:

- nearest other pond distance;
- fraction of movement worlds with another pond reachable;
- mean all-pond exponential pressure across movement worlds.

### C — typed occupied-source connectivity

R2 plus:

- fraction of movement worlds with another 2012 occupied source reachable;
- mean occupied-source exponential pressure across movement worlds.

The sole primary contrast is **C - R2**.

This directly asks whether occurrence-conditioned dispersal opportunity contains information that generic geometry and current habitat/state do not.

## Evaluation

- held-out unit: 2012 region;
- split: leave-one-region-out;
- model family: unchanged L2 logistic regression with C=1;
- numeric preprocessing: training-only standardization;
- missing numeric values: training median plus missingness indicator;
- fish: fixed yes/no/missing categorical encoding;
- minimum training endpoint classes: 5 positive and 5 negative;
- primary metric: region-macro held-out log loss;
- secondary: region-macro Brier;
- negative C-R2 favors typed connectivity.

Non-estimable regions remain visible.

## Two-stage access

### Stage 1

Only 2012 response state may be opened.

After that:

1. construct 2012 site-use state;
2. build source-conditioned connectivity;
3. build every R0/R1/R2/C predictor row;
4. fingerprint the complete feature table.

### Stage 2

Only after the feature fingerprint is frozen may 2013 response columns be opened and the endpoint constructed.

No feature, scale, source definition, split or model setting can change after Stage 2.

## Evidence ceiling

Because the historical R code was inspected before this protocol existed:

> PNW can demonstrate that the machinery works on a real response holdout, but it cannot serve as pristine independent confirmation.

RMNP remains the pristine-fresh lane.
