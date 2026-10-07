# Source-leverage semantic correction v1.182

## Correction

The v1.121/v1.122 response-free diagnostic established that, among ultrarare mammal species with 2–4 occupied pilot sources, **aggregate graph-pressure contributions are more evenly distributed among sources than in bioregion-matched random placements**.

It did **not** by itself establish spatial complementarity.

The prior shorthand “more complementary than matched random placements” was too strong.

## Why

For source s, v1.121 first summed its kernel access over all heldout geometry targets,

A_s = sum_t exp(-d_graph(t,s)/lambda_t),

then normalized those totals across sources and calculated an inverse-Simpson effective source number.

A high effective source number therefore means that no single source monopolizes the **aggregate access mass**.

Two very different spatial configurations can produce the same aggregate effective source number:

1. **territorial complementarity** — different sources dominate different target subsets;
2. **balanced redundancy** — the same sources co-cover the same target subset with similar contributions.

v1.121 did not distinguish these cases.

## What remains valid from v1.122

The numerical results remain unchanged:

- median dominant aggregate source share = 0.6607;
- median aggregate effective / nominal source count = 0.7436;
- mean actual-minus-null aggregate effective source count = +0.2824;
- 95% species-bootstrap interval = [+0.2050, +0.3624].

The correct interpretation is:

> **Observed ultrarare source sets distribute total graph-access leverage more evenly among their occupied sources than bioregion-matched random source placements.**

Do not infer from v1.122 alone that those sources occupy non-overlapping source territories or provide independent spatial insurance.

## Discriminating test

v1.181 was frozen before its execution to distinguish territorial complementarity from balanced redundancy.

For each target island, source access is normalized among the focal species' occupied sources. Hill-number partitioning then gives:

- alpha: effective number of sources contributing locally to a target;
- gamma: effective number of sources represented across the complete target surface;
- beta = gamma / alpha: turnover in source identity across target space.

Interpretive fork:

- actual beta > matched null: aggregate balance reflects stronger target-space partitioning;
- actual beta <= matched null: aggregate balance does not reflect stronger target-space partitioning and may instead reflect co-coverage/redundancy.

The v1.181 result must be interpreted independently of the earlier v1.122 label.

## Evidence boundary

This is a semantic correction to an interpretation, not a numerical reanalysis.

It changes no v1.119 heldout occurrence result, no BALA result and no evidence class. It uses no new occurrence response and authorizes no new occupancy threshold.

The terms “spatial complementarity”, “irreplaceable source territories” and equivalent wording must not be derived from v1.122 aggregate N_eff alone.
