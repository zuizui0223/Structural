# Zenodo 318-island mammal stress result v0.54

## Status

The independent 318-island mammal stress test is complete.

This is **not fresh confirmation**. Its island split, q75 threshold and reference ladder were frozen before the later public exposure of island-level response-derived summary columns, but the species-support/pilot protocol was frozen afterward. The raw 1,474-species occurrence matrix itself remained sealed until the frozen pilot and heldout reads.

The heldout response is now consumed and may not be rerun.

## Frozen design

- 8 archipelagos;
- 309 eligible islands;
- 65 pilot islands;
- 244 heldout islands;
- fixed pilot-supported species universe: 233 species;
- q75 continent isolation: **1124.41 km**;
- heldout prediction rows: **56,852**;
- prediction SHA-256: `a5fe8326172e39ca4cf1d3d7afe9b9bd679076ffc10ec08aaa7c2da2fddeaad9`.

The R3 and C models were fitted from pilot data before heldout outcomes opened. The heldout scorer had no model-fitting path.

## Heldout outcome

The one-shot heldout read opened:

- 244 heldout islands;
- 56,852 fixed species-island targets;
- 4,185 presences;
- 52,667 absences.

Pilot/out-of-scope occurrence cells and non-focal species remained sealed during heldout scoring.

## Primary test

The predeclared primary asks whether source-pool information becomes **more useful** under extreme continent isolation:

`mean(C−R3 | extreme) − mean(C−R3 | non-extreme)`

Predicted direction: **negative**.

Observed heldout mean C−R3 log-loss increments:

- extreme q75: **−0.05593**;
- non-extreme: **−0.10138**.

Primary contrast:

**+0.04545**

Archipelago-cluster bootstrap 95% CI:

**[−0.00319, +0.08836]**

Accepted bootstrap replicates: 9,782 / 10,000.

Therefore:

**primary unsupported.**

The point estimate is opposite the predicted direction, but the interval crosses zero. It is not evidence for a statistically resolved reversal.

## What is still interesting

C improved heldout log loss descriptively in both regimes because both C−R3 means are negative.

Overall heldout mean C−R3:

**−0.08964**

By historical island type:

- Connected: **−0.09548**;
- Isolated: **−0.08592**.

These are descriptive/secondary quantities. They do not rescue the failed primary.

The important ecological distinction is therefore:

> occupied source-pool information can be useful without being specifically activated by extreme mainland isolation.

## Island-biogeographic interpretation

The original A-Islands discovery suggested a source-pool handoff under extreme mainland remoteness.

The independent mammal stress test does **not** support that as a universal isolation regime switch.

Instead, the combined evidence is more consistent with a context-dependent view:

- source-pool identity can matter beyond strong island-state references;
- but its importance is not controlled by mainland remoteness alone;
- taxon dispersal mode, archipelago permeability, historical connection and source saturation are plausible moderators for future prospectively frozen tests.

## Evidence ceiling

Do not claim:

- fresh confirmation of source-pool handoff;
- a universal remote-island switch;
- a significant opposite interaction;
- realized dispersal, rescue or colonization causality.

The 318-island response is consumed. No rerun, refit, q75 change, species-universe change, source-operator change or bootstrap change is allowed.
