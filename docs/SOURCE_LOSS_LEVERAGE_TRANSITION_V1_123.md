# Source-loss leverage transition hypothesis v1.123

## The non-trivial conservation question

The v1.121 diagnostic showed that equal numbers of occupied sources need not contribute equally to the source-access landscape. That observation alone does not establish a conservation consequence.

The next test is deliberately sharper:

> **If two species lose the same number of occupied island populations, does subsequent range contraction depend on which populations were lost?**

This is not tested with a two-time comparison. With only two censuses, “a source disappeared” and “the range contracted” are the same event. The minimum admissible design therefore contains three response times.

## Three-time causal ordering

- **t0 — baseline source state.** Occupied sources are defined under a frozen occurrence rule. Their leverage is computed from t0 state plus response-independent geography only.
- **t1 — source-loss event.** Sources present at t0 but absent at t1 form the lost set.
- **t2 — downstream endpoint.** Among populations that were still occupied at t1, ask which are absent at t2.

The lost t0 sources themselves are excluded from the t1→t2 endpoint. This prevents the source-loss event from being identical to the future response.

## Self-anchor exclusion

For every target population **i**, the target itself is never allowed to act as one of its own sources.

Define `S0\i` as the populations occupied at t0 other than i, and `L01\i` as the members of that external source set that disappear by t1. The kernel value `K_ii` is never used.

This matters in temporal data because a target surviving to t1 is necessarily occupied. Allowing it to contribute its own source pressure would mechanically dilute the leverage of losses elsewhere and would make the temporal operator inconsistent with the original Structural source operator.

## Target-specific loss of source access

For target population i and external baseline source s, let K_is be a frozen nonnegative source-access kernel. Define baseline external-source pressure

    P_i = sum_{s in S0\i} K_is

and the fraction of that external baseline access contributed by sources lost between t0 and t1,

    E_i = sum_{s in L01\i} K_is / P_i.

E_i is defined only when P_i > 0.

E_i has a direct interpretation. E_i=0.10 means the earlier loss event removed 10% of the target's frozen **external** source-access pressure; E_i=0.80 means it removed 80%.

This is more informative than counting lost populations. Two one-population losses can therefore have the same nominal magnitude but radically different spatial consequences.

## Primary prospective test

The reference model already receives:

- habitat/current-state covariates;
- baseline occupied-source count, with target self-anchor excluded for target-specific quantities;
- number of sources lost from t0 to t1;
- generic species-independent network context;
- Euclidean distance and diffuse pressure from surviving **external** t1 sources.

The candidate adds only E_i.

The primary question is whether this addition improves held-out prediction of **subsequent t1→t2 contraction** among populations that survived to t1.

Support requires a prospectively frozen cluster-macro C−R2 log-loss contrast below zero with a cluster-bootstrap 95% upper bound below zero.

## Why this is stronger than “configuration matters”

The hypothesis now has a falsifiable management-scale counterfactual:

> Losing one population is not a unit-sized perturbation. Its structural magnitude is the fraction of external source access that disappears from the remaining network.

If supported independently, population-loss accounting based only on the number of local populations lost would be incomplete. A low-leverage loss and a high-leverage loss would represent different perturbations even when both equal “one population.”

## Event-level summary

For source s, define A_s as its source-access mass summed over eligible geometry targets other than s. Normalizing A_s across the t0 sources gives q_s. For the actual globally lost set L01,

    Q_loss = sum_{s in L01} q_s.

Q_loss is a secondary event-level quantity. It asks what fraction of the baseline source-access landscape was carried by the populations that disappeared.

The site-level E_i remains primary because it identifies where that loss should matter, rather than assigning one exposure value to an entire species-transition event.

## Admission firewall

A candidate may be selected from metadata only. It must have at least three repeat censuses, stable/crosswalkable spatial units, response-independent geometry, and a survey-effort or detection rule that can be frozen before confirmatory t2 response access.

A burned pilot may open only to establish transition estimability. It may not estimate the effect or choose a favorable species, time window, kernel, scale or leverage threshold. Confirmatory t2 rows remain sealed until the full protocol and Structural v0.31→v0.42→v0.32→v0.33 gate chain are frozen.

## Claim boundary

Even a successful predictive result would not by itself prove dispersal, demographic rescue, recolonization or a causal effect of removing a population. It would establish the narrower but conservation-relevant fact that **the spatial leverage of populations lost earlier contains future information about where additional occupancy contraction occurs, beyond the number of populations lost and ordinary distance to surviving sources.**
