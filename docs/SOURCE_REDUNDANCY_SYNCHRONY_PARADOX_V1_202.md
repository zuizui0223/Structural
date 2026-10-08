# Source redundancy versus synchrony: a mechanistic conservation paradox (v1.202)

## Why Structural's negative source-territory result matters

The v1.181 geometry-only mammal diagnostic found that source influence territories were **less differentiated** than source-count- and region-matched random placements, while co-coverage was greater. That does not tell us whether real source populations substitute for each other through time, because the graph is constructed from coordinates and the occupancy labels are range-map-derived.

A more discriminating conservation question follows:

> Can spatially overlapping potential source populations provide *less* demographic insurance than spatially separated sources, because their reproductive failures are synchronized?

It is not enough to say 'network connectivity improves rescue'. The relevant comparison is how strongly two source populations fluctuate together **before** their potential recipient undergoes colonization or extinction.

## Why this isn't already solved by a network overlap index

Suppose multiple sources have fixed relative weights `w_s`, with `sum_s w_s=1`, and source reproductive deviations `X_{s,t}`. The variance of local propagule input is

`Var(sum_s w_s X_{s,t}) = sum_s sum_r w_s w_r Cov(X_{s,t}, X_{r,t})`.

For fixed weights and equal source marginal variance, high positive covariance can keep input variable even with large nominal source count. Under independence, the same weighted ensemble could buffer fluctuations. This is an identity, **not empirical evidence** that source synchrony caused any observed extinctions.

## The crucial prior result

Wanner et al. (2024, [*Ecology*](https://doi.org/10.1002/ecy.4270)) analyzed 11 years of kelp records and ocean-modelled spore transport. Dispersal indices predicted geographic patterns of biomass synchrony even after accounting for distance, nitrate and waves. The authors themselves emphasized a trade-off: dispersal facilitates recolonization yet may reduce spatial stability by inducing synchrony.

That trade-off is **not our discovery**. Our more precise untested increment is whether the **same accessible source ensemble's residual failure covariance**, beyond geography, expected propagule supply and shared climatic disturbance, predicts subsequent colonization/persistence failures. Neither graph co-coverage nor source count directly measures this.

## Ecological discriminating predictions

- **Independent-source insurance:** with comparable expected propagule supply and habitat, additional asynchronously varying sources reduce temporal supply failures and improve later establishment.
- **Synchrony erosion:** positive source covariance eliminates that benefit; accessible sources fail together and later establishment remains poor despite high nominal or graph-effective source count.
- **Common-shock proxy:** the apparent covariance effect disappears after properly lagged disturbance and local environmental state are represented.
- **No mechanistic bridge:** covariance is measured but adds no independent next-transition information; the mammal graph result remains a static cartographic predictor with no established demographic implication.

Do not pool 0→1 colonizations with 1→0 extinctions. Distinguish fixed graph access from time-varying physically directed transport and measured lagged propagule production. Covariance must be estimated exclusively from earlier training windows, not from the target's future. The existing 1996–2006 kelp series and 2024 synchrony results are *published*, therefore they can be a retrospective feasibility and mechanism comparison only; they cannot become pristine evidence.

## Gate

No test was run here. Unresolved: exact linked file versions, spatial keys, lagged measured reproductive states, habitat controls, zero/one classification/observation process, sufficient number of events and a defensible null that preserves geographic embedding and environmental common shocks while testing residual covariance. The latest v1.202 triage remains non-confirmatory. Original GEB manuscript and all prior scores remain untouched.

