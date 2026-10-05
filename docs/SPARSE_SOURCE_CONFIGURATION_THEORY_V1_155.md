# Sparse-source configuration sensitivity v1.155

## Purpose

This note provides a response-free theoretical rationale for the occupancy-regime result.

It does **not** claim a new metapopulation theorem. It records a finite-population identity showing why, whenever potential source islands contribute unequally to a target, the identity of occupied sources becomes relatively more consequential as the number of occupied sources declines.

The argument uses no mammal held-out response, no BALA outcome and no fitted ecological coefficient.

## Setup

For a focal target island i, let there be M possible source islands. Let w_ij ≥ 0 be a fixed target-specific source-access weight from possible source j to target i. The weights may come from Euclidean kernels, graph-path kernels or another prospectively defined spatial operator.

Condition on exactly n occupied source islands. Under a simple response-free null in which the occupied set is a uniformly sampled n-subset of the M possible sources, define:

A_i = Σ_j Z_j w_ij,

where Z_j = 1 when source j is in the occupied set and 0 otherwise, with Σ_j Z_j = n.

For the fixed target i, define:

μ_i = (1/M) Σ_j w_ij

and

σ_i² = (1/M) Σ_j (w_ij − μ_i)².

## Finite-source identity

Sampling n sources without replacement gives:

E[A_i] = n μ_i

and

Var(A_i) = [n(M−n)/(M−1)] σ_i².

Therefore the squared coefficient of variation across alternative source configurations with the **same source count** is:

CV²(A_i) = [(M−n)/(n(M−1))] × (σ_i²/μ_i²).

For fixed M and any non-uniform weight field σ_i² > 0,

(M−n)/(n(M−1)) = [1/(M−1)] × (M/n − 1),

which is strictly decreasing in n.

Hence:

> **Holding source count fixed, the relative variation generated solely by which sources are occupied is larger when fewer sources remain.**

Equivalently, sparse occupancy increases the relative sensitivity of source access to source identity.

## Biological interpretation

This identity gives a null mechanism for the observed occupancy-regime pattern.

It does **not** say that rare species must benefit from connectivity. It says something narrower:

- if source islands differ in their access weights to a target;
- and only a few sources are occupied;
- then replacing one occupied source by another can cause a larger proportional change in total source access than it would when many alternative sources are occupied.

Thus source scarcity can **expose geographic/topological heterogeneity** that is averaged over when many sources are present.

The key interaction is therefore:

**source scarcity × heterogeneity among source positions,**

not rarity alone.

If all potential source islands have identical weights, σ_i² = 0, configuration sensitivity is exactly zero for every n. Sparse occupancy cannot manufacture a topology effect from a homogeneous geography.

## Connection to the Structural result

The global mammal analysis already controls occupancy breadth, source proximity and diffuse source pressure in R3. The ultrarare signal therefore cannot be reduced to the finite-source identity alone.

However, the identity predicts **where residual topology information is most likely to become identifiable**: low-n regimes in which the actual source-weight field is heterogeneous.

This is qualitatively consistent with the evidence hierarchy:

- 1–4 pilot presences: strong held-out presence gain and actual topology better than 20/20 rewired nulls;
- 5–12 pilot presences: presence gain but no topology specificity;
- ≥13 pilot presences: exploratory source-context gain, but observed adjacency not uniquely informative.

The evidence does not establish a continuous monotonic curve because the three layers were not one prospectively frozen gradient and the broad near-ubiquitous layer was non-estimable.

## Leverage concentration

For an observed occupied source set, normalize non-negative target-specific source weights as:

p_ij = w_ij / Σ_k w_ik.

Then:

max_j p_ij ≥ 1/n

and the effective number of sources

N_eff,i = 1 / Σ_j p_ij²

satisfies:

1 ≤ N_eff,i ≤ n.

These identities explain why nominal source count and spatially independent source contribution are not equivalent. They do not establish that loss of a high-leverage source causes later demographic decline.

That stronger prediction was tested independently in BALA and was not supported.

## Topology-null interpretation

Rewiring changes the target-specific weight vector while approximately preserving coarse graph properties such as degree and edge-length structure.

The finite-source identity implies that any difference in the heterogeneity or alignment of those weight fields is easiest to expose proportionally when n is small.

Therefore the matched-rewiring result can be interpreted as a stronger statement than a generic rare-species effect:

> in the ultrarare regime, the **observed arrangement** of island connections carried information that coarse source scarcity and matched network summaries did not.

This remains predictive evidence. It does not identify the graph edges as realized dispersal routes.

## Falsifiable prediction for an independent system

Before response access, an independent island system can compute a response-free configuration-sensitivity index:

S_i(n) = [(M−n)/(n(M−1))] × (σ_i²/μ_i²).

A prospective ecological test can then ask whether the incremental value of exact occupied-source topology over a source-aware reference is concentrated in species/targets with high precomputed S_i(n).

This is preferable to choosing a new rarity threshold after seeing responses because it turns the mechanism into a continuous, response-independent prediction.

## Claim boundary

Supported mathematically:

- relative configuration sensitivity rises as n falls whenever source weights are heterogeneous;
- sparse source sets necessarily permit stronger leverage concentration.

Not established mathematically:

- that connectivity improves occurrence;
- that the relationship between predictive gain and occupancy is monotonic;
- that graph edges are dispersal routes;
- that high leverage causes rescue;
- that loss of a high-leverage population causes later contraction.

The last claim is specifically constrained by the non-supportive independent BALA test.
