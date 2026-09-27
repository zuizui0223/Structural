# Structural current status v0.50

## Fresh-confirmation state

Structural still has **zero fresh active candidates** and **zero fresh confirmatory-eligible systems**.

The pristine 5,592-island mammal system remains response-sealed on HOLD because its required safe island-covariate source is not yet transport-resolved.

The Indo-Pacific atoll plant system remains terminally closed after its pilot encountered an out-of-domain response code.

## Independent 318-island mammal stress test

The separate Zenodo 318-island mammal system is an **independent stress test only**, not fresh confirmation.

Its 65-island burned pilot has now passed both frozen gates:

- fixed pilot-supported species universe: **233 species**;
- pilot species-island targets: **15,145**;
- positives: **1,002**;
- negatives: **14,143**;
- estimable islands: **65/65**;
- response-qualified islands: **65/65**;
- heldout occurrence values parsed during pilot: **0**.

## Pre-heldout model freeze

Before any of the 244 heldout island occurrence values were opened, the frozen v0.47 scoring contract was implemented exactly.

The fit uses:

- 65 pilot islands only;
- sorted full one-hot archipelago indicators;
- pilot-island mean/population-SD standardization;
- frozen log1p transforms;
- Jeffreys-smoothed global and within-archipelago pilot occupancy;
- ridge logistic regression with lambda = 1;
- all non-intercept coefficients penalized;
- deterministic IRLS from beta = 0;
- NumPy 2.3.5 under Python 3.12.

Both models converged in 9 iterations.

The complete heldout prediction surface contains:

**244 islands × 233 species = 56,852 rows**

and is frozen at SHA-256:

`a5fe8326172e39ca4cf1d3d7afe9b9bd679076ffc10ec08aaa7c2da2fddeaad9`

Heldout occurrence values opened at this stage:

**0**

No heldout log loss, C−R3 contrast or source-pool-handoff support statistic has yet been computed.

## Next scientific event

Exactly one heldout stress-scoring execution may now be authorized.

That execution must:

1. bind the pre-heldout artifact and prediction-surface SHA;
2. decode occurrence values only for the 244 frozen heldout islands and only for the 233 frozen species;
3. prohibit all coefficient refitting;
4. calculate only the already-frozen v0.47 estimands and 10,000-replicate archipelago-cluster bootstrap;
5. classify the result as stress-test evidence, never fresh confirmation.

This is now the shortest route to a real island-biogeographic result without weakening the prospective boundaries.
