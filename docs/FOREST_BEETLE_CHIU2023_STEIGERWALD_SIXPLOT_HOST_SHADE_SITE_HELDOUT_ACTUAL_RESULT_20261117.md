# Chiu/Vogel/Chao 2023 Steigerwald forest beetles: SIX original plot heldout host identity predictive positive, one source only (2026-11-17)

## Main new executed result — positive under fixed within-forest source-conditional test

**A precommitted one-pass new ORIGINAL biological response test was executed successfully.** Source [author GitHub public dataset and code](https://github.com/AnneChao/PTB_iNEXT.link), original source Dryad DOI [10.5061/dryad.ksn02v78d](https://doi.org/10.5061/dryad.ksn02v78d), original methodology Chiu et al. 2023 *Philosophical Transactions B*, underlying original field experiment Vogel et al. 2020 in ONE Steigerwald forest, Germany. This is an old published field experiment with previously reported sun/shade and host wood relationships, **not a new pristine or independently collected six-region ecological replication**.

**Actually executed frozen workflow [Actions #44099334768](https://github.com/zuizui0223/Structural/actions/runs/44099334768) SUCCESS**, artifact **14333904538**, original Actions ZIP SHA256 **047ae4c5b60206d3e8343a339b915b91d7e3e954b7045705e86d2381d6bcb4e7**. Source first-line/source fields qualified separately BEFORE any biological outcomes in [Actions #44098660859](https://github.com/zuizui0223/Structural/actions/runs/44098660859), source-only artifact #14334433263: 309247 original bytes, gitblob SHA1 `0d935bc5c5fbf64528aa34607ce72b0beab6d7d4`, 3891 original method rows, 6 plot labels, 3 exposure/shade treatment codes, 6 offered wood species, four collection years 2016–2019. All **108/108** plot×treatment×tree cells have positive source beetle records; **430/432** possible year cells have recorded source taxon rows. The 2 others were **not** imputed to zero, unexposed or unsampled. There were **0 original ID→method conflicts** and **0 duplicate host source-code conflicts**.

After method-only source check had *appropriately* stopped a strict 432/432 year-level opportunity completeness requirement, a **different observational estimand was frozen before original species values were opened**: the *relative species mixture among beetles detected at each plot×shade×host over 4 years*, conditional on records; this does not assume complete annual detection or equal trap-day exposures. [Exact new specification](FOREST_BEETLE_CHIU2023_STEIGERWALD_SIXPLOT_HOST_SHADE_SITE_HELDOUT_ONEPASS_PRESPEC_20261117.md), committed BEFORE original response read. No alternative years, tree hosts, shade levels, guild definitions, model penalization or thresholds searched after outcome.

### Original source response and design support actually validated

| Source unit | Actual original run |
| --- | ---: |
| Biological beetle-tree interaction lines, author original | **3891** (all positive recorded integers; zero-valued source lines = 0) |
| Source beetle species | **264**; all retained, including rare species |
| Parent geographical plots | **6** in same German forest, not six countries/biomes |
| Within-plot shade/exposure contexts | **3**: closed canopy shade, artificial net shade, open sunny |
| Offered deadwood host-tree identities | **6** |
| Distinct plot × shade × host response cells | **108**, exactly 18 per parent plot |
| Observed source ID→species duplicate positive entries | **2** (incidence UNION within cell means no double-counting) |
| Four years | **2016–2019** pooled; no year-specific effect estimated |
| Source-positive year contexts | **430/432**, two missing not imputed |
| Detected distinct species per plot×shade×host source cell | **10–50**, median **26** |
| Site-heldout folds | **6**, train 90 source cells, holdout 18 per fold |
| Species functional/feeding guild | **NOT available** in scored source; species COMPOSITION only |

### One frozen response model and genuinely tested positive result

Response: one 264-dimensional Hellinger transformed **relative distinct detected species** mixture per plot×shade×wood-host cell, pooling source-positive years and discarding original abundance weights. Predictor baseline uses **shade-conditional mean** of 30 training plot×host cells for each treatment; the extended model adds **host-tree identity**, by combining five other-parent-plot matching shade×host cell response vectors with fixed shrinkage lambda=5 towards shade-only mean. Both predictions are L2-normalized and heldout response values NEVER enter model fitting. One plot is the heldout block, NOT each of its 18 cells an independent forest.

| Primary original 6-site-heldout endpoint | Verified aggregate |
| --- | ---: |
| Baseline Hellinger² (shade only) | **0.434242622** |
| Extended Hellinger² (shade + tree-host identity) | **0.414542730** |
| **Mean plot-equal improvement ΔHellinger²** | **+0.019699892** |
| Relative heldout error reduction | **+4.53661%** |
| Improvement in original geographical plot folds | **6/6 positive; 0 negative** |
| Min / max source plot heldout improvement (anonymous) | **+0.009078979 / +0.029364857** |
| 4000 six-parent-plot bootstrap percentile 95% CI | **[+0.014590142, +0.024835923]** |
| **All 2^6=64 block-exact signed permutations, two-sided p** | **0.03125** |
| Precommitted test gate: Δ>0, bootstrap lower>0 and exact p<.05 | **PASSED** |
| Parameters post-result changed or new source endpoint tuned | **ZERO** |

Independent arithmetic: **0.434242622 − 0.414542730 = 0.019699892**; 100×Δ/0.434242622 = 4.53661%. Six positive signs give the minimum attainable two-sided signflip p=2/64=0.03125. The signed-block test assumes exchangeable/symmetrical differences between the SIX nearby original plots; they are all within one forest, so large-scale spatial/biome generality cannot be inferred. The bootstrap interval uses SIX clusters only and is not a population-wide causal confidence statement.

### Correct biological interpretation (new analysis versus original old ecology)

**New specific predictive inference**: within this historical Steigerwald cohort, knowing the offered host-tree identity conveys predictive species-composition information not captured by the **same shade treatment alone**, and this gain had the same sign in all six left-out original plots. This supports a *source-conditioned local resource-identity* prediction but is **NOT** independent evidence for a universal host-channel mechanism. The original author literature already studied deadwood-tree host, sun/shade treatment and interaction networks: their prior organismal host sorting is PRIOR ART. The current out-of-plot test is an original analytical diagnostic of **local predictive portability**, not proof of first ecological discovery.

- Does NOT directly test beetle functional feeding guild because this dataset does not contain such an ontology; do not relabel 264 species by unverified guild categories.
- Does NOT prove local woodland deadwood availability in standing forests because the experiment OFFERED substrate tree host, rather than measuring ambient forest host-resource supply.
- Does NOT establish realized population rescue, dispersal, climatic thermal escape, habitat restoration or species host preference through causal intervention at independent geographical regions.
- Reusing 4 years without confirmed zero-capture/effort means conclusions apply to relative **detected species** mixtures and are exposure-/detection-conditional, not corrected species occupancy.
- Original source contains 430/432 positive-record year combinations; two missing contexts do not imply trap failure or zero observed beetles. Original README prose describes open vs closed subplots while source has an additional **N artificially net-shaded** treatment; retain this mismatch in mechanistic interpretations.
- Same within-country historical site network cannot substitute for cross-country spatial transfer. The result also should not be meta-averaged numerically with Finnish VD10 **Host_tree** guild H²+0.00024237 or German Piccini feedingguild H²+0.00050966 because the responses and baselines have different definitions.

### Science ledger state and next meaningful gate

Prior Finnish 142 author sites: deadwood added Host_tree H² +0.00024237, signed-cell p=.015 (small conditional result). Prior original three-country Burner Host_tree trait-label D+.091059 p=.000333 (shuffle conditional, physical source identity partially unresolved). German Piccini original 8 parent sites: feeding guild stand identity added-prediction +11.70% descriptive, exact p=.09375 **UNSUPPORTED**. PREDICTS forest changed taxon replacement +0.0942 (39 studies) and Thai 18 sampling station canopy capture +24.3% are different observational endpoints, not direct resource-channel cross-country replication. NEON static canopy non-support, BALA and mammal GEB scientific holds unchanged.

**Current status: ONE NEW SOURCE-CONDITIONAL PREDICTIVE POSITIVE across six heldout plots inside one forest; ZERO VERIFIED independent cross-country or biome replication of host-resource functional-guild transfer.** Next decisive independent test requires original forest networks that directly record physical plot×offered OR naturally available deadwood/host type×positive capture/zero sampling opportunities×species (and validated guild traits if a functional-guild claim is intended). The old six-plot 2023 source is now SEALED; DO NOT switch G/O only, change lambda, rare species, expand/shrink years or retest outcomes for a more attractive p.

Original script: `analysis/forest_macro_global/chiu2023_steigerwald_6plot_host_shade_onepass.py`. Workflow: `.github/workflows/forest-macro-chiu2023-steigerwald-sixplot-host-shade-onepass.yml`. No raw author species/catch/site IDs exported; GitHub PR #469 Draft/unmerged, main unchanged; no eBird/TinyFish.
