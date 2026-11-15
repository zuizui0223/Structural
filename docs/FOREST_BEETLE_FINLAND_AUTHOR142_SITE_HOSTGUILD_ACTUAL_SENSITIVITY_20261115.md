# Finland author-verified 142 physical sites: post-result Host_tree guild divergence sensitivity (2026-11-15)

## Main conclusion — original positive direction survives source-author physical-site grouping

One frozen post-result robustness sensitivity executed successfully in [GitHub Actions #43678622814](https://github.com/zuizui0223/Structural/actions/runs/43678622814), known-truth site-OR / guild distance tests SUCCESS, all 3 original source file MD5s PASS, source-only original metadata 142/10/1 gate PASS before taxon response scoring. Anonymized aggregate artifact **14147507390**, SHA256 `c5445de235ec01bd4051bc3e443d061c9781ae7ebf0892b05a280dce7522cc5d`.

This is an **actual computed observation**, not a proposal. The original three-country source event-column conditional-null effect D=+0.091059 and p=0.000333 has **not** been recalculated or overwritten. The new Finland-only physical-site sensitivity remains positive relative to **its own** trait-label shuffle null:

| Original Finnish forest beetle analysis | Frozen original 153 sample-year EVENT columns | NEW 142 physical Site sensitivity |
| --- | ---: | ---: |
| Original source sampling columns included | 153 | **152** author-linked, 1 unlinked excluded BEFORE biological scoring |
| Distinct author-verified physical field `Site` keys | not established by frozen sample-column endpoint | **142** |
| Repeated sampling years within 2023-author Site identity | not collapsed | **10 events** above 142 physical sites |
| Within-country host-guild sqrt-JSD observed | **0.117609** | **0.118481** |
| Country-conditional species-guild-label null mean | **0.082926** | **0.083244** |
| **Observed minus trait-label-null mean** | **+0.034683** | **+0.035237** |
| Source original shuffle iterations | 2,999 | **2,999** |
| Two-sided conditional label-shuffle p | previous aggregate p not separately reported here | **0.000333** |
| Centered 95% conditional-null reference quantiles (NOT sample CI) | not claimed | **[-0.008629,+0.010933]** |
| Original active `Host_tree`-known beetle species in the Finland cohort | 358 | **358** |
| Physical site pair contrasts (DEPENDENT, not independently randomized forests) | not applicable | **10,011** |

**Scientific conclusion:** Within the Finnish source cohort, the source-conditional association between beetle species composition and relative `Host_tree` affiliation composition persists after author-verified 142 physical-site pooling of repeated years. The finite post-result sensitivity and exact one original unlinked event cannot establish a novel independent ecological replication, field-forest causality, or a spatial-cluster-robust effect. It is stronger than a pseudoreplicated 153-column description for *sampling-unit robustness*, and no stronger than the data warrant for environmental mechanism.

## Strict original site identity and source-only population

[Independent author-release source-only CI #43678389641](https://github.com/zuizui0223/Structural/actions/runs/43678389641) verified the original Finnish 2022 Zenodo v1 153 source year-prefixed sampling labels against the original **2023** same-author `Site_covariates.csv` `rowID`, `Year`, `Site` source fields (142 original author Site IDs, 142 source field rows):
- **142** exact `Year_Site` source ID matches between releases.
- Additional **10** 2022 survey-year labels share one of the **142** author-recognized physical Site identities, so may be pooled as repeated years.
- The remaining **1** 2022 original year-label has a non-year Site token not in that 142-site original author metadata and was **excluded BEFORE any new taxon value was read**; no alias guessed or data-driven taxon exclusion.
- Original 2022 source sample population 153 eligible of 153 under the unchanged trait-coverage thresholds. After original field-source exclusion of one unlinked event and source-site OR, all **358** originally active `Host_tree`-known species remained present. Both original 2022 MD5s and 2023 metadata MD5 fixed.
- Original 2023 `Site_covariates.csv` has field metrics for climate, forest age, deadwood and sampling effort, but its numerical environmental values were **not used** in this fixed sensitivity. 2023 source is the same Finnish study population, NOT an independent forest network.

Source citations: Burner 2022 [Zenodo 5950610](https://doi.org/10.5281/zenodo.5950610), 2023 [Zenodo 8322080](https://doi.org/10.5281/zenodo.8322080), 2021 [JBI DOI 10.1111/jbi.14272](https://doi.org/10.1111/jbi.14272), 2023 [Ecology & Evolution DOI 10.1002/ece3.10588](https://doi.org/10.1002/ece3.10588).

## Full estimator and nonindependence restrictions

Within each of the 142 source-author physical sites, the original species `count>0` incidences over one/two survey years were OR-combined into a single physical-site presence vector. The frozen original original-event trait gate `>=5` source-detected Host_tree-coded beetles and `>=60%` original trait coverage was preserved exactly, original `both` is a separate third guild, missing traits were not inferred. Any original species that became entirely absent due only to the pre-response unlinked event exclusion would be removed as an inactive species; in the original actual data **none** did.

For each of 10,011 source site-pairs, compute sqrt Jensen-Shannon distance between the source-guild species-incidence proportion vectors across `broadl, conifer, both`; take one unweighted mean across all unordered author physical-site pairs. Reuse exactly the original code's `mean_guild_sqrt_js` pair aggregation and fixed `np.random.default_rng(20261115)` 2,999 permutations across observed species' Host_tree labels. The physically grouped site×species incidence matrix, original source-year grouping and group sizes remain fixed. The null is conditional on the observed data; p compares absolute observed-minus-null expectation to the centered trait-label null with +1 correction.

This p is **not** a bootstrap p for 142 spatially independent field experiments, and the null does not account for phylogenetic clustering of traits, source study clusters, geography, sampling effort heterogeneity or imperfect species detection. The conditional-null quantile bracket cannot be reported as a conventional sampling 95% CI. The small difference between original sample-year delta .034683 and site-collapsed delta .035237 is **NOT** an independent effect size contrast with tested significance (different sampling units, one unlinked event excluded, and different null species pool if applicable).

Norway 1,111 repeated survey columns had 468 source header candidate site IDs, but only an unconfirmed year-stripped source-identity count match, not a second physical-site response reanalysis. Germany originally sampled 386 site once but original study networks are clustered. **Do not** combine the new Finland site-level null p with the existing Norway and Germany sample-column p to present a physical-site-validated three-country meta-test.

## Scope for larger forest ecology

The new result establishes source-conditional **host-affiliation differentiation** of Finnish saproxylic beetle assemblages after repeated years are pooled. It DOES NOT show how many broadleaved or conifer host trees were present at each field plot; the `Host_tree` categorical trait is beetles' affiliation, not actual local resource availability. No causal evidence for forest tree species turnover, canopy height, deadwood supply, climate buffering, species movement, colonization, biomass change or conservation intervention.

Retain as an exploratory **bridge** alongside (not meta-pooled with) PREDICTS 39 independent Study forest alteration Simpson replacement difference +0.0942 [0.0638,0.1253] and NEON CHMv2 p90 height-difference beetle beta partial slope +0.0349/10m, p=.1759 (non-support). Old BALA and GEB scientific HOLD datasets not reopened, no eBird or TinyFish, PR #469 stays Draft and unmerged.

Code `analysis/forest_macro_global/finland_author_site_hostguild_sensitivity.py`; original 2022/2023 source-only crosswalk `analysis/forest_macro_global/finland_author_2023_siteyear_source_crosswalk.py`; biological sensitivity workflow `.github/workflows/forest-macro-finland-author142-site-hostguild-sensitivity.yml`. [Prespec frozen before secondary biological calculation](FOREST_BEETLE_FINLAND_142_AUTHOR_SITE_COLLAPSED_SENSITIVITY_PRESPEC_20261115.md).

## Next original measurement gate

The same 2023 author's 142-site covariates (`VD10` local deadwood volume, `agedomin` forest age, `OldFor_1km` old-forest volume) are legitimate **measured and derived environmental variables**, unlike unobserved host-tree local species composition. A future one-test **resource gradient** question would be whether any *preselected* measure of forest resource variation improves prediction of the source-verified site-level host-guild composition beyond original study/year/geographic structure; it must be separately defined and be labelled post-result exploratory, with independent field-region holdouts. Do NOT reinterpret `VD10` as actual conifer/broadleaf host amounts or infer causality from a positive association.
