# Occupancy-dependent role inversion synthesis v1.179

## Central question

The obvious statement is that when only a few source populations remain, their spatial arrangement can matter more.

That is **not** the strongest result in Structural.

The less obvious result is:

> **The predictive role of occupied-source connectivity changes qualitatively across occupancy regimes.**

Across the same 5,401-island geography and the same R3→C model architecture, graph-path source information changes from an **absence-constraint signal** at higher occupancy to a **presence-opportunity signal** at lower occupancy. Exact observed topology becomes uniquely informative only at the sparse extreme.

This is a predictive-role inversion, not merely an increase in effect size.

## Frozen class-specific evidence

All values below are already frozen results.

| Pilot occupancy layer | Evidence class | Presence C−R3 | Absence C−R3 | Descriptive class-selectivity J = presence − absence |
|---|---|---:|---:|---:|
| ≥13 presences | exploratory | +0.11644 | −0.00580 | +0.12224 |
| 5–12 presences | prospective preregistered | −0.27744 | +0.000430 | −0.27787 |
| 1–4 presences | prospective preregistered | −0.5962587 | +0.000236 | −0.5964947 |

Negative C−R3 favours the graph-path candidate.

Therefore:

- in the ≥13 exploratory layer, C helped mainly by **lowering error on absences** and harmed realized presences;
- in the preregistered 5–12 layer, the preregistered higher-occupancy-style constraint signature failed and the class-specific direction reversed: C helped realized presences and slightly harmed absences;
- the unexpected 5–12 reversal motivated the sealed 1–4 presence-opportunity hypothesis, which was then strongly supported.

The cross-layer J statistic is descriptive only. Its three values were not preregistered as a monotonic gradient and must not be given a post-hoc trend p-value.

## The fitted graph terms reverse sign as well

The same two standardized C features were added beyond R3 in all three layers.

Frozen C coefficients:

| Pilot occupancy layer | z log1p nearest graph-source distance | z log1p graph-source pressure |
|---|---:|---:|
| ≥13 presences | +0.285050 | −0.070469 |
| 5–12 presences | −0.621702 | +0.012664 |
| 1–4 presences | −0.402313 | +0.004652 |

Thus the high-occupancy exploratory fit places the two graph-source terms in the opposite directional orientation from both prospective low-occupancy fits.

This coefficient sign pattern is **supporting diagnostic evidence only** because:

1. each occupancy layer has its own standardization;
2. the two graph-source variables are jointly fitted and may be correlated;
3. coefficient magnitudes should not be compared as causal effect sizes.

The key evidence for role inversion is therefore the held-out class-specific prediction pattern, not coefficient interpretation. The coefficient sign reversal is concordant with that held-out pattern.

## Why this is not the obvious scarcity argument

The finite-source identity in v1.155 predicts that relative sensitivity to source identity increases as source number falls whenever source positions are heterogeneous.

That theory can explain **why configuration becomes easier to expose at low n**.

It does **not** predict:

- that the graph candidate should help absences while harming presences at higher occupancy;
- that the preregistered 5–12 constraint signature should reverse direction;
- that the same graph features should switch directional orientation in the fitted model;
- that exact observed topology should be indistinguishable from matched null topology at 5–12 but beat all 20 nulls at 1–4.

Therefore the empirical result is not reducible to “few sources make arrangement important.”

## Sequential evidence logic

### Stage 1 — exploratory constraint signature

The ≥13 layer suggested that graph-transformed source context primarily reduced overprediction of unlikely island × species combinations:

- absence C−R3 = −0.00580;
- presence C−R3 = +0.11644.

A later post-hoc matched-null audit showed that this was **not** actual-topology-specific:

- actual minus mean rewired = +0.000225;
- actual better than 0/20 nulls.

Interpretation: network-transformed source context acted as a broad occupancy constraint, not as evidence that realized adjacency itself mattered.

### Stage 2 — prospective failure and inversion

Before the 5–12 held-out response was opened, P2 preregistered the exploratory constraint signature:

- absence C−R3 < 0;
- presence C−R3 ≥ 0.

That prediction failed in the **opposite** direction:

- absence C−R3 = +0.000430;
- presence C−R3 = −0.27744.

This is the key non-obvious event. The analysis did not merely weaken with lower occupancy; its class-specific predictive role reversed.

Topology specificity was still absent:

- actual minus mean rewired = +1.56e−6;
- actual better than 11/20 nulls.

### Stage 3 — prospective presence-opportunity confirmation

The 5–12 inversion generated the new sealed 1–4 hypothesis: source information should act as presence opportunity.

That prediction was strongly supported:

- presence C−R3 = −0.59626;
- 95% CI [−0.74385, −0.46446];
- absence C−R3 = +0.000236;
- 95% CI [+0.000077, +0.000418].

The presence gain was stronger where a graph-reachable source existed:

- nonempty minus empty presence contrast = −0.6705;
- 95% CI [−0.8009, −0.5427].

And, unlike the 5–12 layer, exact observed adjacency now mattered:

- actual minus mean rewired = −0.05853;
- 95% CI [−0.0993, −0.0163];
- actual better than 20/20 matched nulls.

## Stronger ecological interpretation

A useful interpretation is a **constraint-to-opportunity transition**.

At higher occupancy, graph-transformed source context can act as a broad exclusion or range-constraint signal: it helps identify where a relatively widespread species is unexpectedly absent.

As occupancy declines, the same source representation stops behaving as an exclusion filter and instead identifies the few locations where occurrence remains plausible.

At the sparsest tested regime, that opportunity signal becomes dependent on the actual arrangement of the remaining source islands rather than on matched surrogate topology.

This is qualitatively different from saying only that connectivity “gets stronger” as species become rarer.

## Relation to metapopulation theory

Existing metapopulation work already shows that connectivity can affect occupancy, colonization and extinction differently, and that topology effects can depend on demographic conditions. Structural should not claim endpoint dependence or occupancy-dependent connectivity as novel.

The narrower contribution is:

> **within a fixed occurrence endpoint, fixed geography and common reference architecture, the held-out predictive role of occupied-source information changes sign/class with occupancy state, and exact topology specificity emerges only at the sparse extreme.**

That is the manuscript-level novelty candidate.

## Claim boundary

Supported as frozen evidence:

- a prospective 5–12 constraint-signature prediction failed in the opposite class-specific direction;
- a subsequent prospective 1–4 presence-opportunity prediction was supported;
- actual-topology specificity was absent at 5–12 and supported at 1–4;
- graph-term coefficient directions are concordant with the role inversion.

Not supported:

- a formal continuous threshold;
- a monotonic law over occupancy;
- a causal switch from extinction regulation to colonization;
- realized dispersal along graph paths;
- rescue;
- a general result outside the mammal geography;
- management ranking.

The ≥13 endpoint is exploratory, so the phrase **“constraint-to-opportunity transition”** must be presented as a synthesis of the evidence hierarchy, not as a three-level preregistered trend test.

## Manuscript recommendation

Replace the weak headline:

> “When few populations remain, their arrangement matters.”

with the stronger question:

> **Does source connectivity merely weaken as occupancy declines, or does it change what it predicts?**

Recommended answer:

> **It changes what it predicts. In higher-occupancy mammals, source context acted mainly as an absence constraint and was not specific to observed adjacency. A preregistered 5–12 layer unexpectedly reversed toward presence opportunity but still lacked topology specificity. That reversal prospectively predicted the 1–4 layer, where presence opportunity strengthened and the observed adjacency outperformed all matched null topologies.**

BALA then supplies a separate boundary:

> **This predictive role inversion in static occurrence does not imply that structurally important sources have greater later demographic consequence.**
