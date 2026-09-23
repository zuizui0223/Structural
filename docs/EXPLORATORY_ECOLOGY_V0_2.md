# Structural exploratory ecology v0.2 — isolation-regime switch

## Status

This is a **post-outcome ecological discovery layer** built entirely from already-frozen A-Islands and Tanzania outputs.

It does not alter the frozen manuscript, primary contrasts, denominators, Structural v0.40 admission machinery, or TTF boundary.

The purpose of v0.2 is narrower than v0.1:

> Is the apparent remote-isolation effect a coarse quartile artefact, or does it reveal a biologically interpretable regime switch in how species-conditioned topology behaves?

## 1. The breadth × remoteness interaction is continuous

Across all 712,515 valid A-Islands held-out predictions, a two-way fixed-effect model controlling species and island identity gives:

**range breadth × log mainland distance: β = −0.00267, SE = 0.00079, p = 7.3×10⁻⁴.**

Negative means that the EOG increment becomes more favourable as widespread species are evaluated on more mainland-remote islands.

Adding a simultaneous breadth × island-area interaction leaves the remoteness result essentially unchanged:

- breadth × mainland distance: **β = −0.00273, p = 6.7×10⁻⁴**;
- breadth × island area: β = +0.00098, p = 0.13.

So the moderation is associated with **mainland remoteness**, not simply with island size.

This matters ecologically because it separates two classic island-biogeographic axes. Large versus small island is not the same condition as near versus truly remote island.

## 2. It is a remote-tail phenomenon, not one magic quartile

The breadth × extreme-isolation interaction becomes progressively stronger as the tail definition moves outward:

| remote tail begins | distance cut | breadth × tail β |
|---|---:|---:|
| 50th percentile | 20.2 km | −0.0030 |
| 60th | 50.4 km | −0.0036 |
| 70th | 61.2 km | **−0.0074** |
| 75th | 68.9 km | **−0.0095** |
| 80th | 87.1 km | **−0.0122** |
| 85th | 161.4 km | **−0.0121** |
| 90th | 196.1 km | **−0.0132** |

This is not evidence for a universal ecological threshold at 68.9 km.

Instead it says that the topology residual strengthens as the analysis moves into the genuinely remote tail.

The already-frozen future hypothesis keeps **75%** as the primary threshold. The other cutpoints are post-outcome robustness diagnostics and cannot replace or rescue that primary threshold.

## 3. The mechanism is not “exclusion only”

v0.1 showed that, across all islands, adding EOG tends to hurt true presences much more than true absences.

v0.2 reveals that this asymmetry changes sharply under extreme remoteness.

In a two-way species/island fixed-effect diagnostic:

- true presence carries a strong excess EOG loss: **+0.1203**;
- extreme isolation attenuates that presence penalty by **−0.0931**;
- broader range increases the ordinary presence penalty by **+0.0412 per breadth SD**;
- but broad range × extreme isolation attenuates it again by **−0.0369**.

Thus the earlier “exclusion constraint” interpretation was incomplete.

For the broadest-quarter species:

### Near islands, true presences
- n = 3,348;
- mean C−R3 = **+0.1921**;
- median = +0.0652;
- only **33.7%** favourable;
- EOG lowers predicted occurrence by **−0.0156** on average.

### Most remote islands, true presences
- n = 4,663;
- mean C−R3 = +0.0161;
- median = **−0.0123**;
- **59.0%** favourable;
- EOG raises predicted occurrence by **+0.00358** on average.

So topology changes role.

In ordinary source-rich settings, species-conditioned connectivity often suppresses probabilities redundantly and hurts genuine presences.

In the remote tail, that suppression disappears and can reverse: the topology term can identify a subset of very remote islands that remain linked to occupied sources despite high generic isolation.

This motivates a more specific ecological hypothesis:

> **Generic isolation dominates ordinary landscapes; species-conditioned topology becomes informative at the remote tail because it distinguishes remote-but-linked from remote-and-effectively-unlinked units.**

This remains a predictive hypothesis. It does not prove colonization, rescue, or demographic persistence.

## 4. Original network signal is not the same as independent network information

Species with stronger original conditional concordance show only a tiny tendency toward a less-adverse later C−R3 result:

- Spearman ρ = **−0.076**;
- Pearson r = **−0.070**.

Even the top quartile of original conditional concordance has mean C−R3 ≈ **+0.00010**, essentially neutral rather than clearly favourable.

Therefore:

> **Structural detectability under a restricted reference is not evidence that topology is an independent ecological state under a stronger reference.**

This directly links the methodological and ecological conclusions.

The original pattern can be real while its information is later absorbed by area, mainland isolation, source configuration and generic stepping-stone context.

## 5. Tanzania offers a weak analogue, not a replication

The overall Tanzania far-large-fragment tail is region-confounded because every upper-quartile site lies in East Usambara.

Within East Usambara alone, however, a species/site fixed-effect diagnostic shows:

- presence penalty = +0.0747;
- presence × extreme-tail interaction = **−0.0244**, p ≈ 0.044.

So the most isolated East fragments also show some attenuation of the presence penalty.

But the continuous distance interaction is not in the same direction and is not conventionally detected (p ≈ 0.070), and there are only nine East fragments.

Therefore Tanzania contributes only:

**small-panel qualitative consistency with a non-linear regime switch.**

It does not confirm the threshold.

## 6. Connection to island biogeography

Carter, Perry & Russell (2020) decomposed insular isolation into mainland distance, stepping-stone availability and insular network position.

The Structural result now suggests a hierarchy among those axes:

1. **mainland/source state** explains much of occurrence variation;
2. **generic stepping-stone/network context** absorbs additional geometry;
3. **species-conditioned topology** becomes most informative only when generic isolation is extreme.

This is not “replace island biogeography with graph theory.”

It is closer to:

> **Graph structure becomes biologically informative when classical isolation variables stop resolving which extreme islands are actually connected to the focal species' occupied source set.**

## 7. Connection to habitat fragmentation

Brodie & Newmark's Tanzania study already showed that patch area plus matrix-aware isolation explains much of bird occurrence and outperforms isolation measures that ignore heterogeneous matrix permeability.

Structural adds a stricter question:

> after that matrix-aware reference is supplied, when does additional species-conditioned topology still matter?

The present data do not yet answer that generally.

But the remote-tail pattern generates a clean next hypothesis that connects oceanic islands and habitat fragments without pretending that they share the same movement process.

## Frozen next hypothesis

v0.2 freezes the following for a future independent panel:

**Primary**
- predictor-only isolation metric chosen before response access;
- upper 25% = extreme isolation;
- test whether topology increment is more favourable in extreme than non-extreme units.

**Predeclared robustness**
- 70% and 80% cutpoints only;
- neither may rescue a failed 75% primary.

**Secondary**
- continuous source/range breadth × extreme-isolation interaction;
- presence-penalty attenuation as a post-outcome mechanism diagnostic.

**Generalization**
- local interpolation is insufficient;
- cross-origin island/fragmentation claims require the same primary direction under separately frozen spatial-block transfer.

That is the current ecological development path.
