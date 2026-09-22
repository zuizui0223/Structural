# Temporal response firewall v0.14

## Problem fixed

A dynamic connectivity predictor may legitimately depend on **current or lagged biological state**.

For example, a 2013 occupancy forecast may use 2012 occupied ponds as source anchors. That is not target leakage: the 2012 state exists at prediction time.

The earlier generic phrase `candidate_uses_outcome` was too coarse because it could be read as banning any response-derived state.

v0.14 separates:

- **lagged/current state** — allowed after its own authorization;
- **future/held-out target** — sealed until feature construction is frozen.

## Required order

    schema / geometry / protocol frozen
        ↓
    Stage 1: open lagged/current state only
        ↓
    build current-state + source-conditioned connectivity
        ↓
    freeze all feature rows and fingerprints
        ↓
    Stage 2: open future target
        ↓
    score once under frozen metric/split

The future target is never permitted to alter connectivity features, source definitions, scale selection, reference variables or splits.

## PNW translation

For PNW:

- lagged/current state time = **2012**;
- future target time = **2013**;
- ecological unit = site;
- geometry = median 2012 UTM coordinate for the 150 sites observed in both years.

A future PNW protocol may therefore use 2012 occupancy as a source-state coordinate after Stage 1 authorization, provided the species/taxon rule, connectivity scale/worldset, reference and metric were frozen beforehand.

The 2013 occupancy target remains sealed until the resulting 2012-derived feature matrix is fingerprinted.

## Claim boundary

v0.14 does not restore PNW to the pristine-fresh lane. Its design-exposure caveat remains permanent.

The purpose is to correctly distinguish legitimate temporal state dependence from future-outcome leakage, which is necessary for both Structural and EGWE dynamic state representations.
