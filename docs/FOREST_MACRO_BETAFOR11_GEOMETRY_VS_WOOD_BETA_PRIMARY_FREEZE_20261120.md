# BETA-FOR 11 forests — first genuine new insect assemblage endpoint, frozen BEFORE original OTU values

Date: 2026-11-20. Experimental observational-window effect (not a global forest-law claim).

## Scientific question and prior-art boundary

Original Rothacher et al. 2025 *JAE* DOI 10.1111/1365-2664.70086 already establishes sample-coverage-standardized taxonomic Hill alpha enhancement up to 47% with canopy gaps + deadwood, and indicator OTU differences among open/closed/wood groupings: **PRIOR ART**, not novel. The author's primary one-period coverage correction uses `iNEXT.3D`, and public first-party code DOI 10.5281/zenodo.15165462 includes `01_Singleton_Filter.R` (MD5 54a9473aeba0d5e680897bde3c412787, seed1, four meta columns) and `06_iNEXT_3D.R` (MD5 ac36dd37848693eb48d35196902f6389; `OTUNr,Family,Order`, coverage 0.98).

**New quantitative endpoint:** under equal original source capture-round counts and forest, does DIFFERENCE IN CANOPY ARRANGEMENT (A vs D with matching wood type) produce more *detected-OTU taxonomic replacement* than DIFFERENCE IN DEADWOOD TYPE with same canopy arrangement? This asks about β-differentiation *relative to another within-forest treatment contrast*, not richness or original authors' indicator taxa. Neither sign is assumed positive; the outcome may favor wood, canopy geometry, or neither.

The 2026 spider BETA-FOR alpha/beta paper DOI 10.1111/1365-2656.70297 is related **PRIOR ART**, but is a different taxon/protocol and cannot count as independent forest-network replication.

## Original-source inclusion and method admission

- Original data only: Zenodo version-specific 15371332; exactly six published original file MD5s. `BETAFOR_information.csv` 46,965 bytes MD5 873f5d424904d1eed00e079b945dd5dc; `com_singletons.csv` published md5 81e2c1269bff49fafdf497f03f5922b2, ~28MB.
- Source row/column linkage **before biology:** 594 source `patch×sample` unique keys, 99 physical patches, six sampled opportunities per patch, nine treatment classes in each of 11 forests nested in six geographic regions (source event CI #44730282968). Original 598-column OTU table has 594 exact original sample column IDs (source #44731113423); first four header roles are unnamed/R-X, `OTUNr`, `Family`, `Order`, verified via original R author codebook (#44732613653). The old v1/v2/v3 source gate STOPs remain immutable; they are not biological failures.
- **MANDATORY PREBIOLOGY GATE**: the separate frozen treatment-pair source-only [author-code protocol](FOREST_MACRO_BETAFOR11_AUTHOR_TREATMENT_PAIR_SOURCE_PREFREEZE_20261120.md) must PASS exact `CC,AW,AL,AS,AB,DW,DL,DS,DB` one each in every original forest; verify `substr(patch,5,6)` matches original source `treatment`. No after-outcome source-code alias rescue, no fewer-forest subset.
- No original taxon matrix may be scored until original method gate PASS, a tested known-truth script and this protocol are committed separately BEFORE original biology is opened.
- The original parent 234-patch one-time data share these 11 experimental forests; not independent replication. The 99 seasonal source has **one CC patch/forest**, so it does NOT support within-forest control–control beta comparisons, nor an α-gain vs matched untreated-district β effect.

## One primary endpoint (fixed sign and operator)

Original `com_singletons.csv` author-source OTU sample count matrix (22,889 published OTUs; original raw row count may differ). Each of the 594 sample columns is independently MD5-matched with source `sample` field. Require all sample counts finite nonnegative whole numbers, unique nonblank `OTUNr`, no missing numeric cells, 99 patches/6 original sample-rounds each, no all-zero patch or near-empty species sets. Otherwise SOURCE_OR_RESPONSE_STOP without outcome-driven changes.

**Sequence error correction**: reproduce the author's documented `01_Singleton_Filter.R` one-pass scheme with fixed R `set.seed(1)`, in original column order, treating the first 4 columns as metadata. For each sample column `j`:
- `os=number of OTUs with count exactly 1`, `f2=# count=2`, `f3=# count=3`, `f4=# count=4`; follow source author replacement `if f3==0 then f3=1; if f4==0 then f4=1`;
- compute `e1 = round(2 f2^2/(3 f3)+max(0,2 f2^2/(3 f3)− f2 f3/(2 f4)))`;
- when `e1<os`, randomly set exactly `os−e1` singleton source OTU counts to zero with R `sample(..., replace=FALSE)`; `set.seed(1)` globally once; remove all-zero OTU rows as original authors did. Never export source OTU IDs, sequence reads or raw matrices. The correction uses source counts but does not produce a true ecological occupancy model.
- Convert **corrected observed reads** to `detected OTU` (corrected count>0) per sample, then take the logical **OR across all six original sampled periods** at the same patch. This is a **detection-conditional pooled-season composition**, not population incidence or movement. No abundance-to-individual-count inference.

For each original forest `f`, 8 experimentally manipulated patches form exactly 4 paired wood types `w∈{W,L,S,B}` with source treatment classes `Aw` aggregated gap/open canopy and `Dw` distributed/closed canopy. Control `CC` remains in quality frame but is **not** scored, because there is no matched within-site control-control β reference. Each term uses pooled-season OTU detected sets.

Let `β_sim(P,Q) = min(b,c) / (a+min(b,c))` for a OTUs shared, b unique to patch P, c unique to Q; stop as nonestimable if denominator 0.

- Geometry-change dissimilarity `G_f = mean_w β_sim(Aw,Dw)` (four pairs with the SAME wood class).
- Wood-change dissimilarity `W_f = 0.5[mean_{w<w'} β_sim(Aw,Aw') + mean_{w<w'} β_sim(Dw,Dw')]` (six different-wood pairs for each of the SAME canopy regimes).
- **Primary forest contrast** `D_f=G_f-W_f`; positive = geometry is associated with greater detected-OTU replacement than changing wood configuration, negative = wood categories show greater replacement; 0 = no difference. The pair count 4 versus 12 is not an independent sample-size multiplier: each **forest** supplies ONE effect `D_f`.
- **Primary geographic estimand** `D_R = equal mean across the six original geographic regions of within-region forest-mean D_f`. Keep 11 forests nested in 6 regions. Report the source site/region denominator; do not treat 594 samples, 99 patches, 22k OTUs, 4/12 pairs or source bootstrap draws as geographic replication.

## One fixed uncertainty and classification plan

- Primary uncertainty: **all 2^6=64 sign flips** of the six source **region means** relative to zero; 2-sided p is fraction with absolute mean ≥ observed. This is a conditional exchangeability diagnostic (not globally calibrated). 
- Secondary uncertainty: **4,000** region-block bootstrap draws (seed 20261120) for percentile 95% CI of region-equal D_R. Report n regions/forests with positive/negative D separately and forest-equal mean.
- Separate **fixed null**, if feasible without new inference choices: 999 treatment-label permutations within each forest over the **eight manipulated patches** while preserving the CC excluded and the original 8 A/D × wood label universe; summarize the region-equal D null. If this cannot be implemented exactly under original physical label assignments, mark unavailable rather than approximating.
- Exploratory directional support **only if** D_R nonzero direction AND 95% bootstrap CI excludes 0 AND 2-sided region signflip p<0.05; otherwise NOT SUPPORTED/MIXED. Do not change the endpoint, OTU detection threshold, taxon subset, dates, correction seed, grouping, one-tailed p or numerical thresholds after observing source response.
- Always report independent study/biome ceiling (one German broadleaf forest experimental programme) and **sample coverage caution**: the original authors found systematically lower metabarcoding completeness in canopy gaps. Equal six collection opportunities and original singleton correction do NOT equalize sample coverage. Thus even a positive D_R is *detected-OTU reorganization conditional on collection+sequencing process*, not causal species colonization, conservation fitness, full-community beta or broad biome universal mechanism. No claim that an uncovered source method makes all physical species absences observed.

## No-pooling and material-seal rules

BETA-FOR original authors' alpha/indicator effects, 2026 spider source, BALA island temporal/spatial beta, Finnish VD10 Host_tree predictive gain, Slovak trophic guild deadwood non-support, Swedish CTI non-support and PREDICTS forest community replacement are DIFFERENT estimands, cannot be meta-averaged or described as independent field experiments. No older source scorer, global mammal fresh outcome or BALA sealed biological response may be reopened. eBird/TinyFish unused; PR #469 stays Draft and `main` untouched.

**This text itself is a prebiology frozen test, not evidence that a biological outcome was run or favorable.**
