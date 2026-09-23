# Structural exploratory ecology v0.4 — direct reference-gap test and discovery freeze

## Status

**Final post-outcome discovery layer for the current A-Islands/Tanzania evidence.**

v0.4 does not change the frozen manuscript, primary results, empirical denominator, Structural admission chain, release state or TTF boundary.

Its purpose is to answer one final mechanistic question before stopping same-data exploration:

> Does source decoupling identify information missing from the strong R3 reference itself, or did it only look useful because the fitted C model happened to exploit it?

## Direct reference-gap response

The response for v0.4 is not `C − R3`.

It is the frozen held-out R3 calibration residual:

`observed − p_R3`.

Positive values mean R3 underpredicts occurrence probability on average.

This is still a predictive residual. It is **not** demographic growth, colonization probability, extinction risk or persistence.

## 1. Source decoupling marks a gap in R3 itself

On the frozen upper-25% mainland-isolation panel, controlling species identity and island identity:

- excess species-conditioned connectivity: **β = +0.0726**, two-way clustered p ≈ **2.0×10⁻⁶**;
- continuous species-conditioned minus generic connectivity: **β = +0.0889**, p ≈ **4.9×10⁻⁸**;
- multi-hop 25-km source path: **β = +0.0644**, p ≈ **1.2×10⁻⁵**.

Positive coefficients mean that R3 is more underpredictive in those states.

By contrast, simply having a direct occupied source within 25 km gives β ≈ +0.0417 with p ≈ 0.073 in the same diagnostic.

Thus the reference gap is more clearly aligned with **source-conditioned path state** than with a direct-neighbour indicator.

## 2. The gap is not removed by nearest-source distance

The same remote-panel fixed-effect models were augmented with log nearest outer-training source distance.

The source-decoupling coefficients remain:

- excess connectivity: **β = +0.0739**, p ≈ 0.0037;
- continuous source-minus-generic connectivity: **β = +0.2125**, p ≈ 1.4×10⁻¹⁰;
- multi-hop 25-km state: **β = +0.0537**, p ≈ 0.0062.

This is important because R3 already contains nearest species-source distance and diffuse source-pressure terms.

The result therefore supports a narrower interpretation:

> **Path continuity can mark held-out occurrence support that direct source proximity and generic stepping do not fully encode.**

It still does not identify a realized dispersal pathway.

## 3. Spatial robustness and boundary

The reference-gap pattern is independently visible in the two remote spatial folds containing almost all excess-connectivity rows:

### Fold 2
- 116 remote islands;
- 11,448 excess-connectivity rows;
- excess-state β = **+0.1929**, p ≈ 4.8×10⁻¹⁰.

### Fold 4
- 39 remote islands;
- 3,629 excess rows;
- β = **+0.1314**, p ≈ 1.5×10⁻⁴.

### Fold 5
- 26 remote islands;
- only 148 excess rows;
- β = −0.0325, p ≈ 0.41.

Fold 5 is retained as a non-detected boundary.

So v0.4 does not license a claim that every remote archipelago expresses the same source-decoupling effect.

## 4. Current ecological model

The most specific hypothesis supported by the discovery sequence is now:

1. Ordinary island occurrence is largely represented by climate, island area, mainland isolation and direct/diffuse source context.
2. Generic stepping-stone context captures additional species-independent archipelago geometry.
3. Extreme remoteness creates opportunities for generic mainland connectivity and focal-species source connectivity to diverge.
4. When an occupied insular source path remains intact despite weakened generic mainland access, R3 shows a systematic held-out calibration gap.
5. Multi-hop paths can carry this information even when no occupied source lies within the smallest graph radius.

A useful shorthand is:

> **mainland isolation ≠ focal-species source isolation.**

That is the current island-biogeographic contribution.

## 5. Why exploration stops here

A-Islands and Tanzania have now served their legitimate role as discovery systems.

The project has already examined:

- reference tiers;
- range/source breadth;
- mainland remoteness;
- extreme-isolation tails;
- observed presence/absence asymmetry;
- forest-dependence / understory status in Tanzania;
- source-conditioned versus generic connectivity;
- multi-hop source paths;
- direct R3 calibration residuals.

Continuing to search thresholds, taxa, traits, islands or graph scales in the same outcomes would mainly increase researcher degrees of freedom.

Therefore v0.4 freezes this post-outcome discovery lane.

## Next independent test

The already-frozen prospective v0.3 hypothesis is sufficient.

A future system must enter independently through normal Structural admission and freeze before response access:

**Primary**
- predictor-only isolation;
- upper 25% extreme tail;
- candidate-minus-strong-reference contrast.

**Mechanistic secondaries**
- source-conditioned connectivity exceeding the generic connectivity already represented in the reference;
- multi-hop source path at a predeclared smallest graph scale;
- strong-reference calibration residual alignment with those predictor-only states.

The primary cannot be rescued by the secondaries.

No more A-Islands/Tanzania subgroup mining is needed to define that test.
