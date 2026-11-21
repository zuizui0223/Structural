# Structural forest macro — BETA-FOR original community Simpson geometry-vs-wood first genuine biological result (2026-11-20)

## Final scientific decision

**Observed original direction: canopy arrangement change produced slightly greater detected insect OTU species replacement than wood-treatment type change, but a prospectively fixed six-region exact support gate was NOT met.**

The single source-locked **original biological one-pass** GitHub Actions [#44735016332](https://github.com/zuizui0223/Structural/actions/runs/44735016332) **SUCCESS** (both known-truth tests and original biological model executed). This job finished with scientific status **`EXPLORATORY_REGION_EQUAL_GWD_NOT_SUPPORTED`** — NOT a source-access technical STOP and NOT evidence of no possible canopy effects. The original source results are now **consumed**: do not rerun/re-optimize the same source under new OTU thresholds, different q/correction settings, wood categories, spatial blocks, reference groups or p-value tests.

**Prospective primary effect, matched original BETA-FOR treatments:** original 11 experimentally manipulated 2025 German beech-mixed forests / six geographic regions, original 99 physical patches and six original Malaise trap sample rounds each (594). One untreated `CC` control patch per forest is retained in source integrity but excluded from the pairwise axis contrast. For four original wood classes `W,L,S,B`, the eight manipulated combinations are `AW,AL,AS,AB,DW,DL,DS,DB`. Relative species replacement among `A/D` patches with *same* wood class was compared with replacement among *different* wood classes within the *same* canopy arrangement; no unmeasured source distance or canopy height was substituted.

Let within forest `G_f=mean_w Simpson(Aw,Dw)`, `W_f = [mean_{w<w'} Simpson(Aw,Aw')+mean_{w<w'} Simpson(Dw,Dw')]/2`, and `D_f=G_f−W_f`. Inference is equal mean over six original geographic regions, each region first equally averaging its observed forests; source patches/pairs/samples/OTUs are not independent regional replicates.

| Frozen original estimate or independent denominator | Actual outcome |
| --- | ---: |
| Original publisher source (com_singletons.csv) | MD5 `81e2c1269bff49fafdf497f03f5922b2`, **28,413,720 bytes** |
| Original physical method source | **99 patches, 594 samples, 11 forests, 6 regions**, true source treatment + chronology prebiology PASS [#44733020223](https://github.com/zuizui0223/Structural/actions/runs/44733020223) |
| Raw OTU source rows and sample columns | **22,889 OTUs**, 594 original author sample columns |
| Author `01_Singleton_Filter.R` one-seed correction | **25,383 counts set to zero** across 411 sample columns; **21,114 corrected detected OTUs** remain |
| Mean source pooled-six-sample corrected OTU detections per patch | **median 2,216**, min 1,397 / max 3,182 |
| Region-equal mean Simpson (G) — canopy arrangement axis | **0.4067550823** |
| Region-equal mean Simpson (W) — wood-treatment axis | **0.3941761390** |
| **Primary region-equal (D=G-W)** | **+0.01257894334**, about +3.19% relative to the wood-axis Simpson mean (descriptive ratio only) |
| Forest signs | **9/11 positive**, 2/11 negative |
| Independent geographic region signs | **5/6 positive**, 1/6 negative |
| Region bootstrap (4000, R seed 20261120) | 95% percentile **[+0.00366490066,+0.02238286478]** |
| **Primary exact 2-sided all 64 region sign flips** | **p=0.0625**, fixed directional support criterion FAILS |
| Separate conditional 999 within-forest 8-label permutations (seed 20261121) | **p=0.006**; site-treatment labelling contains information, but **does NOT rescue the six-region decision** |
| Original sequencing read depth, mean/sample | A canopy 40,765 vs D 41,774 raw reads (not sample coverage or insect counts) |

### Independent saved-score arithmetic and evidence boundaries

The archived original anonymous six regional `D` values (sorted, no region IDs) are:

`[-0.002129694250273442, 0.002249868571373881, 0.00649962758015532, 0.01099966875261971, 0.02838233786656228, 0.02947185150129056]`.

Their simple mean exactly reproduces **+0.012578943336954718**; explicit enumeration of all (2^6=64) sign vectors yields **4/64** contrasts with absolute mean at least as extreme = **0.0625**, equal to the original scorer. Separately (0.4067550823144644-0.3941761389775097 = 0.012578943336954695). Those independent source-free arithmetic checks do **not** re-run ecological model or create six new studies. Original reader confirms 22,889 uncorrected OTUs and 21,114 after the author correction; the latter is also consistent with the original authors' `09_indicatorspecies.R` hard-coded 21,114 OTU community columns, an external analysis-code sanity check, not a new replication.

**Immutable public provenance:** original-source onepass source commit `d7410f494356d5dbdc42cb1a3c19da55a77bd64f` and [Actions run #44735016332](https://github.com/zuizui0223/Structural/actions/runs/44735016332), source-derived anonymous artifact **#14627898792**, ZIP SHA256 **`9fbab085cf77b2051992056e13f5bf682e1d7c31001638443c56e0a01306b09b`**, validated independently. Artifact contains **aggregate_only.json**, no OTU original rows, names, patch IDs, trap date coordinates or underlying matrix. Exact script `analysis/forest_macro_global/betafor11_geometry_vs_wood_beta_onepass.R`, source runner `betafor11_geometry_vs_wood_original_onepass.py` and immutable preregistration `FOREST_MACRO_BETAFOR11_GEOMETRY_VS_WOOD_BETA_PRIMARY_FREEZE_20261120.md`. Earlier source v1/version STOP, v2 method-header HOLD, v3 four-identifier STOP were not overwritten or reclassified.

## What the ecology actually supports

1. **Within the original 11-forest, 6-region German experiment**, original experimental treatment labels have a detectable relation to community replacement under a *within-forest* eight-label conditional-null test. The canopy arrangement axis has a **small +0.0126** descriptive advantage over the wood-axis contrast, with 9/11 forest and 5/6 region means positive. This is a **new, explicitly matched quantitative OTU-beta contrast**, not the authors' original alpha/Hill contrast. The source experiment is reused; it is not novel field sampling.
2. Under the fixed *region-generalization* criterion, the exact two-sided `p=0.0625` does **not pass**. The bootstrap percentile interval excludes zero under a different resampling assumption, and within-forest label permutation p=.006 tests a different null; **do not report a universal canopy-over-wood advantage or call the primary formally supported based on the smaller p**.
3. **Sampling coverage is a critical outstanding alternative**. Rothacher et al. (2025) established that canopy gaps have systematically lower metabarcoding coverage; their original alpha result **requires coverage standardization to 98%**. Repeating their singleton error correction and pooling six sampling rounds equalizes neither OTU coverage nor habitat-dependent detectability. The modest A/D raw read-depth difference (40,765 vs 41,774) does NOT diagnose coverage bias. Thus Simpson turnover is *observed detected-OTU replacement under this sampling pipeline*, not fully estimated assemblage beta or individual dispersal. No taxonomic alpha/gamma compensation mechanism or forest demographic causal rescue is identified.
4. **Prior art**: The source authors already demonstrated up to **47% coverage-standardized alpha diversity increase** in canopy gaps + retained deadwood and different indicator OTUs across open/closed and deadwood conditions (Rothacher et al. 2025 DOI 10.1111/1365-2664.70086). A separate **same parent 11-forest experiment** observed spiders with **lower alpha/gamma but increased functional/phylogenetic beta** under structural heterogeneity (Stör et al. 2026 DOI 10.1111/1365-2656.70297). This cross-taxon contradiction in local response is scientifically intriguing but is *prior published evidence*, not 11 independent new forests or proof of a shared causal mechanism.
5. **Geography and broader generality**: all 11 forest sites are nested in six **German** region contexts and largely temperate beech forest; neither 20-country PREDICTS replacement nor Finnish Host_tree guild, Slovak trophic guild or Swedish CTI incremental predictions can be meta-averaged with this experimental β difference. In particular, forest alteration/replacement across regions is better-supported than **one universal structure/wood resource predictive pathway**.

## Next scientific target (NEW dataset required, not a rescue of this result)

Replicate the **same predeclared matched canopy vs substrate identity replacement estimand** in a truly independent forest **biome/provider**, with equal capture technology, field opportunity/zero/attrition frame, contemporaneous substrate amount/identity and original sequence/sample coverage evidence, and physical regional/geographic holdout. Pre-specify detection correction or coverage-equated species composition before opening new outcomes. An independent multi-source body of same endpoint region effects would permit a proper hierarchical estimate of mean, among-region heterogeneity and *future forest predictive interval*. If the new dataset cannot support the same estimand, report method/endpoint limitation rather than converting existing disparate coefficients into a fake meta-analysis.

**Submission decision:** present this as a **secondary exploratory mechanism-discrimination candidate** in a forest macro paper, not the main universal discovery until independent same-endpoint/coverage-respecting replication exists. The main strong forest-macro result remains PREDICTS reference-relative detected-taxon replacement +0.0942 across 39 studies/20 countries in two biomes; it is a separate association, not a confirmatory causal pathway.

PR #469 remains Draft and unmerged; no original raw source redistributed, no eBird/TinyFish, no old mammal GEB/BALA/PREDICTS/Finland/Carpathian/Sweden scores re-opened.
