# Source leverage and island conservation synthesis v1.123

## Status

This is a conservation-oriented synthesis of already-frozen Structural evidence.

It adds **no new biological response access**, no new species layer, no new graph scale, no new threshold search, and no new empirical denominator.

The canonical heldout evidence hierarchy remains exactly as frozen in `development/current_status_v1_119.json`.

The source-leverage diagnostic is post-hoc and response-free. It uses only the already-open ultrarare pilot occupancy plus frozen island geometry.

## Conservation question

The v1.119 ultrarare result shows that, for species occurring on only 1–4 pilot islands, the exact island adjacency contains heldout presence information beyond mainland isolation, source count, source distance, generic island connectivity and matched rewired topology.

The conservation question is therefore no longer simply:

> How many source populations remain?

It becomes:

> **How much independent source-access leverage is lost when one occupied island disappears?**

Two species can retain the same number of occupied islands but differ strongly in how spatially redundant or complementary those islands are.

Likewise, losing one occupied island need not have the same structural consequence as losing another.

## Important graph interpretation

Structural does **not** model chains of occupied stepping-stone populations.

Graph paths traverse the full frozen island graph, including islands without a focal-species pilot occurrence. Occupied pilot islands act as source endpoints.

Therefore the relevant quantity is **source-access leverage**, not an occupied-population articulation point and not observed stepping-stone use.

## Effective source number

For source s of species j, define its graph-pressure mass across the 4,126 heldout target geometries:

A_js = sum_i exp(-d_graph(i,s) / lambda_region)

with unreachable targets contributing zero.

Let q_js = A_js / sum_s A_js.

Then define:

N_eff = 1 / sum_s q_js^2

N_eff is the number of equally influential sources that would generate the observed concentration of source-access leverage.

It therefore distinguishes nominal source count from effective source diversity.

## Frozen response-free result

The ultrarare pilot contains:

- 529 species;
- 877 occupied pilot source cells;
- 317 species with one source;
- 116 with two sources;
- 56 with three sources;
- 40 with four sources.

Among the 212 species with 2–4 sources:

- median dominant-source pressure share = **0.661**;
- median N_eff / nominal source count = **0.744**;
- 18 species have at least one source whose deletion would leave some heldout target geometries with no graph-reachable pilot source.

By nominal count:

- two sources: median N_eff = **1.584**;
- three sources: median N_eff = **2.121**;
- four sources: median N_eff = **2.567**.

Thus nominal population count can substantially overstate the number of spatially independent source contributions.

A four-source species, for example, behaves like only about 2.57 equally influential source contributions at the median.

## Matched placement null

For each 2–4-source species, 1,000 random source configurations were generated while preserving:

- nominal source count;
- exact source count within each bioregion.

Observed source configurations were, on average, **more spatially complementary** than the matched random placements:

- actual minus null N_eff = **+0.282**;
- 95% species-bootstrap interval = **[+0.205, +0.362]**;
- actual N_eff exceeded the null mean in **141/212 species**;
- actual N_eff exceeded the species-specific null 97.5th percentile in **32/212 species**;
- only **1/212** fell below the null 2.5th percentile.

Therefore the evidence does not support a simple story that ultrarare source populations are merely clustered and redundant.

Instead:

> **source count is an incomplete measure of retained source access, and observed occupied islands often contribute complementary parts of the archipelago.**

## Revised conservation hypothesis

The most specific conservation hypothesis now supported for future testing is:

> **Losses of equal population number can have unequal structural consequences because occupied source islands differ in source-access leverage and spatial complementarity.**

The relevant future quantity is not only the number of populations lost.

It is the decrement in:

- effective source number;
- source-access pressure;
- coverage of target islands by graph-reachable sources.

This predicts that removing a high-leverage source should produce a larger subsequent contraction of occupancy than removing a low-leverage source, even after controlling:

- nominal source count;
- ordinary Euclidean source distance;
- external island isolation;
- habitat/environment;
- bioregion.

## Relationship to the occupancy-regime result

The source-leverage diagnostic does not replace the v1.119 result.

The evidence hierarchy remains:

1. prospective ultrarare 1–4 layer: presence opportunity and actual-topology specificity supported;
2. prospective 5–12 layer: overall non-replication and no topology specificity;
3. exploratory >=13 layer: absence-focused source-context gain, not actual-topology specific.

The leverage diagnostic sharpens only the **ultrarare conservation interpretation**.

It suggests why source configuration could matter when very few occupied islands remain: the sources are not equally influential and are often spatially complementary.

## What this does not show

Do not claim that:

- a high-leverage source is a demographic source population;
- deleting a high-leverage source causes extinction;
- restoring a high-leverage source causes recolonization;
- graph paths are realized dispersal corridors;
- unoccupied intermediate islands are used as biological stepping stones;
- ultrarare species universally depend on source leverage;
- 1–4 pilot presences correspond to the last 1–4 global populations.

The present result is a response-free spatial diagnostic tied to one global mammal system.

## Decisive next test

The next independent test should be temporal or newly response-sealed.

For a system where occupied populations are lost through time:

1. freeze occupancy state at t;
2. calculate source leverage for every occupied source;
3. classify observed source losses by pre-loss leverage;
4. predict occupancy at t+1;
5. test whether loss of high-leverage sources produces larger subsequent contraction than loss of low-leverage sources after matching on nominal source count, distance, environment and external isolation.

This would move Structural from **predictive source configuration** to a direct test of whether source-population loss has unequal ecological consequences.
