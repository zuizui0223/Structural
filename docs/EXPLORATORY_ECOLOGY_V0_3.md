# Structural exploratory ecology v0.3 — insular source decoupling

## Status

**Post-outcome hypothesis generation only.**

v0.3 does not alter the frozen Structural manuscript, A-Islands primary result, Tanzania primary result, empirical denominator, admission freeze, or TTF boundary.

It asks a more specific ecological question than v0.2:

> What exactly does species-conditioned topology represent when it becomes useful in the remote-isolation tail?

## Reconstruction boundary

For this diagnostic, the analysis is restricted to the **687 A-Islands species with all five frozen folds evaluable**.

That restriction is based on estimability, not EOG outcome direction. It allows the full 842-island observed vector for each species to be reconstructed from the already-open authoritative held-out artifact.

For each species × frozen fold:

- source islands are outer-training presences only;
- held-out labels never define source connectivity;
- the 25/50/125/250-km geographic components are rederived from the frozen 842-island coordinates using the exact authoritative haversine/component rule;
- generic mainland stepping and species-conditioned EOG connectivity are reconstructed from those frozen components.

No model is refit.

## 1. A new predictor-only state: species-specific excess connectivity

Define:

`excess connectivity = species-conditioned EOG frequency > generic mainland stepping frequency`.

There are **15,225** such held-out rows.

Every one has exactly:

- species-conditioned EOG frequency = **1.00**;
- generic mainland stepping frequency = **0.75**.

And all occur between **70.17 and 228.39 km** from continental Australia. There are **zero** excess-connectivity rows outside the frozen remote quartile.

This has a direct graph meaning.

At these rows, the focal island is connected to an occupied source of the focal species at **all four** frozen geographic scales, including 25 km.

But the same island is generically connected to the mainland-entry network at only **three of four** scales: generic mainland stepping has already failed at 25 km.

Thus the remote-tail topology signal is not merely “more connected.”

It identifies:

> **remote islands whose focal-species source network remains intact at a scale where generic mainland access is already broken.**

That is an **insular source decoupling** state.

## 2. The remote presence switch is concentrated in that state

Among remote-island true presences:

### Species-specific connectivity exceeds generic mainland stepping
- n = **2,932**;
- mean C−R3 log-loss increment = **−0.0871**;
- median = −0.0384;
- **77.8%** of rows favour C;
- C raises predicted occurrence by +0.0316 on average.

### No excess species-specific connectivity
- n = 3,979;
- mean C−R3 = **+0.0994**;
- median = +0.0390;
- 39.5% favourable;
- C lowers predicted occurrence by −0.0192 on average.

At species level, 155 taxa have both states represented in the remote tail:

- mean no-excess = **+0.1949**;
- mean excess = **−0.1067**;
- paired excess − no-excess = **−0.3016**;
- Wilcoxon p ≈ **1.4×10⁻¹³**;
- favourable species: **80.6%** in excess state versus **32.9%** without it.

This is the clearest current explanation of the v0.2 regime switch.

The interpretation is still predictive, not demographic: it does not show realized colonization or rescue.

## 3. Nearest-source distance does not contain the same path information

A graph can connect a focal island to an occupied source without a direct source lying within the graph radius.

Define a 25-km multi-hop state as:

- EOG connected frequency = 1.0, so a source lies in the focal component even at 25 km;
- nearest occupied outer-training source > 25 km.

A connection at the 25-km graph therefore requires one or more intermediate islands.

To avoid simply comparing very different source distances, consider true-presence rows whose nearest source is between **25 and 100 km**.

### Multi-hop 25-km source path
- n = **3,635**;
- mean C−R3 = **−0.1042**;
- median = −0.0528;
- **77.8%** favourable;
- candidate probability shift = +0.0331.

### No such multi-hop path
- n = 2,538;
- mean C−R3 = **+0.0810**;
- median = +0.0249;
- 35.5% favourable;
- candidate probability shift = −0.0187.

Across 211 species represented in both states:

- paired mean difference = **−0.2064**;
- median difference = −0.1870;
- Wilcoxon p ≈ **1.6×10⁻²¹**;
- 76.8% of species favour C in the multi-hop state versus 28.0% without it.

This gives a concrete ecological interpretation of what the topology term contains beyond nearest-source distance:

> **path continuity through intermediate islands.**

## 4. Direct source and multi-hop source are both support states

Among true presences that are connected at the 25-km graph:

- direct source within 25 km: mean C−R3 ≈ **−0.0504**, 75.8% favourable;
- source farther than 25 km but connected by a multi-hop 25-km path: mean ≈ **−0.1036**, 77.7% favourable.

So multi-hop connectivity is not merely a weak proxy for direct source proximity.

It can remain favourable even when direct source distance alone says the nearest occupied source is outside the smallest radius.

Again, this is held-out predictive alignment, not direct observation of organisms using those stepping stones.

## 5. Revised island-biogeographic interpretation

The current hierarchy is now:

1. **Area + mainland isolation + direct species source proximity** explain much of ordinary occurrence structure.
2. **Generic archipelago topology** represents species-independent stepping opportunities.
3. **Species-conditioned source topology** matters when the actual occupied-source network differs from that generic topology.
4. The most distinctive case occurs on remote islands where generic mainland entry has weakened but an insular occupied-source chain remains intact.

This suggests a specific extension of classical island biogeography:

> **Mainland isolation and inter-island source connectivity can decouple.**

Two equally mainland-remote islands need not be equally isolated for a focal species if one remains embedded in an occupied insular source chain.

That is a sharper ecological statement than “network connectivity matters.”

## 6. Why v0.2 extreme isolation is retained

Multi-hop source paths can be useful outside the extreme remote tail too.

Therefore remoteness itself is not the entire mechanism.

But only in the remote tail does species-conditioned connectivity actually **exceed the generic mainland-stepping representation** in this reconstruction.

So the leading hypothesis is:

> **Extreme isolation creates the conditions under which mainland isolation and focal-species source connectivity can decouple; species-conditioned topology becomes uniquely informative when it captures that decoupling.**

## Prospective consequence

The future 75%-tail primary frozen in v0.2 is unchanged.

v0.3 adds two mechanistic secondaries that must also be frozen before any future confirmatory response access:

1. **source-conditioned excess connectivity**  
   Does focal-species source connectivity exceed the generic connectivity already represented by the strong reference?

2. **multi-hop source path**  
   Is the focal unit connected to a permitted source at the smallest frozen graph scale even though direct source distance exceeds that scale?

Neither secondary may rescue a failed extreme-isolation primary.

For habitat fragments, the generic and source-conditioned operators need to be defined from fragmentation biology rather than copied mechanically from island mainland stepping.

## Claim ceiling

v0.3 does **not** establish:

- realized stepping-stone movement;
- colonization routes;
- metapopulation rescue;
- persistence caused by insular sources;
- a universal 25-km biological scale;
- a universal mainland-distance threshold.

Those are now clear prospective biological hypotheses.
