# Davis 2026 retrospective schema adapter v0.6

## Purpose

This document freezes the **schema interpretation before any new retrospective refitting** of the Davis et al. 2026 Dryad dataset (DOI: 10.5061/dryad.3ffbg7b08).

The source is especially useful because the same fragmented tropical system includes:

- landscape geometry;
- movement-informed functional connectivity;
- contemporary pollen-mediated genetic outcomes.

The publication already reports the outcome pattern, so the system is **not fresh** and cannot pass the v0.5 response-blind admission gate. Its only role is engineering and adapter falsification.

## Source objects from the archive README

### Genetic_Data_Master.csv

Declared identifiers:

- `Mom_ID`
- `Year`
- `Pop`

Potential endpoint fields:

- `h_Pollen_Pool`
- `Outcrossing`
- `Biparental_Inbreeding`

Potential current-state/reference fields:

- `Area_ha`
- `Percent_Forest`
- `Elevation`
- `Proportion_High_Mobility`

The endpoint/reference role must be frozen by semantics, not by which variable produces the best fit.

### Hummingbird_Data.csv

Patch identifier:

- `Patch`

This file contains hummingbird species counts and high-mobility composition.

**Important:** the README uses `Patch` here but `Pop` in the genetic/landscape tables. The adapter must verify the mapping from actual source files. String equality is not assumed.

### Data_Patches.csv

Primary identifier:

- `Pop`

Landscape/current-state candidates include:

- patch area;
- forest amount in the 1 km landscape;
- elevation;
- high-mobility pollinator composition.

### Connectivity outputs

`patch_based_metrics.RData` and `whole_landscape_metrics.RData` contain structural and functional connectivity metrics.

The whole-landscape object includes, among others:

- `Si.base`;
- `Si.base.nowght`;
- `Si.probcross`;
- `Si.probcross.nowght`;
- `Si.allforest`;
- `Si.allforest.nowght`.

The archive describes a **1 km** local landscape, linked to the maximum daily hummingbird movement range used in the study.

## Typed-connectivity mapping

The initial v0.6 mapping is:

| Ladder level | Davis object | Claim ceiling |
|---|---|---|
| current reference | patch/forest/elevation/pollinator-community state | present ecological context |
| structural geometry | habitat amount/configuration and unweighted structural metrics | geometry only |
| process model | hummingbird movement / gap-crossing weighted IFM | pollen-process model |
| realized endpoint | pollen-pool diversity / outcrossing / biparental inbreeding | contemporary mating/gene-flow outcome |

No field is yet classified as a direct **realized movement observation**. The genetic outcomes are downstream realized mating/gene-flow endpoints, not observed hummingbird trajectories.

## Adapter hard stops

Before any retrospective model fit:

1. verify the archive tree;
2. inspect exact headers and data types;
3. verify `Patch ↔ Pop` mapping;
4. enumerate population/year replication;
5. separate predictor-side movement information from genetic endpoints;
6. freeze one engineering endpoint and one candidate per ladder step without using model-ranking tables.

Published result tables may be used later to check reproduction, but **not** to choose the adapter specification.

## Scientific boundary

This pilot remains:

`counts_as_fresh_evidence = false`

regardless of how well the reconstruction performs.
