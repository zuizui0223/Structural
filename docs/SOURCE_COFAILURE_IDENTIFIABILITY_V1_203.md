# Source cofailure and patch-grain admissibility (v1.203)

## What the literature *already* establishes

Castorani et al. (2017, https://doi.org/10.1098/rspb.2016.2086) investigated **469 giant-kelp patches** with 22 semiannual survey states and separately reported 893 local extinctions and 891 colonizations. Temporal differences in source fecundity were already substantially more informative than variations in transport. Wanner et al. (2024, https://doi.org/10.1002/ecy.4270) treated **117 kelp-bearing ROMS cells** over **44 quarters** for the 1996–2006 dispersal–synchrony analysis. They already showed ocean-modelled dispersal is associated with biomass synchrony beyond distance, nitrate and waves.

These are not two interchangeable `site_id × time` surfaces, nor two independent pristine validations: they overlap ecologically and spatially. The 2017 paper cites a spore-dispersal DOI ending in `14a2849b...`; the author's lab lists a version 3 DOI ending `7e5ff54e...`; the 2024 cell-grid study uses a different 2023 transport DOI ending `28a62732...`. None is a verified drop-in replacement for another. Until we have independently checked exact source entity names, patch IDs, cell IDs, directional edge orientation and semester/quarter alignment, joining these tables is prohibited.

## New identifiability result — higher-order cofailure

The *general* idea that dispersal induces synchrony and synchrony can erode metapopulation insurance is not new (e.g., Fox et al. 2017, https://doi.org/10.1038/s41559-017-0271-y; Yang et al. 2022, https://doi.org/10.1086/720715). The narrower unresolved methodological question is whether **number of accessible source patches + pairwise synchrony + total-input mean/variance** can tell us the chance that **all** sources delivering to a target simultaneously fail.

A synthetic, fully specified counterexample proves they cannot, even before ecological confounding:

Take three binary effective-delivery sources `X1, X2, X3`, each active with probability 1/2, each weighted 1/3. Compare exactly these distributions:

| Distribution over 3-source activity states | P(all zero) | P(all one) |
|---|---:|---:|
| All eight states equally likely (independent) | 1/8 | 1/8 |
| Even-parity states: 000, 011, 101, 110 | 1/4 | 0 |
| Odd-parity states: 001, 010, 100, 111 | 0 | 1/4 |

Each distribution has exactly the same marginal active-source probabilities (1/2), pairwise coactivity (1/4), pairwise covariance (0), expected equally weighted total delivery (1/2), and variance of that delivery (1/12). Yet the probabilities that **no source can supply the target** are 12.5%, 25% and 0%, respectively. The null would therefore miss up to a 25-percentage-point difference in joint source failure despite matching all pairwise statistics.

The identity explains why:

```
P(all three fail)
  = 1 − Σ_i E[Xi] + Σ_{i<j} E[Xi Xj] − E[X1 X2 X3].
```

The triple joint moment is not determined by pairwise synchrony. For two sources the analogous joint-zero probability *is* fixed by means and covariance; the ambiguity becomes relevant with at least three candidate sources.

This is a **known-truth mathematical example, not a new empirical discovery** and not proof of a conservation effect. Observed colonization may fail despite nonzero source supply because of establishment, habitat, detection or dormancy processes.

## Scientific target and testable contradiction

Structural v1.181 found relatively balanced but spatially co-covering graph-derived source influences; v1.119 predicted *mapped* positives using a coordinate-defined network. Neither indicates independent, functioning source populations. A source-ensemble insurance claim requires (i) repeated independently documented functional source production; (ii) a properly directed, time-lagged transfer opportunity; (iii) supported no-source-supply episodes; and (iv) later separated 0→1 and 1→0 occupancy outcomes.

Predefine the donor-to-target source set without using the future target response. Estimate joint source failure from **preceding training periods**; control for common oceanic shocks and habitat; do not calculate covariance using any heldout season. Require measured differences in higher-order cofailure, not just repeated pairwise correlations. If joint events are too rare to estimate in disjoint burned pilot, stop.

The proposed incremental ecological hypothesis is: *jointly functioning accessible source ensembles, not simply source counts or pairwise spatial synchrony, predict interruptions of immigration and later recolonization.* It is untested in Structural. Not all ecological systems have three independent candidate sources or observationally identifiable viable delivery, so the binary known-truth model cannot itself determine whether this hypothesis is estimable.

## Frozen research boundary

The 2017 kelp raw source pair is **already published/outcome-context exposed** and would be a retrospective mechanism stress test even if exact metadata matches. Its 469-patch series and the 2024 117-cell series may not be silently merged or counted as separate confirmations. Biological source observations and transport values were not opened in v1.203. A new, truly independent system must separately pass the Structural v0.31/v0.42 disjoint burned-pilot gate before confirmatory use; GEB scientific HOLD remains.

