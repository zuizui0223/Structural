# v1.241 — Does symmetric island-pair predictiveness survive the KNOWN habitat-type explanation?

**Why this tougher reference matters.** v1.240 demonstrated a major retrospective chronological predictive improvement in destination forecasts when historical **undirected island-pair** arrivals were supplied, relative to destination popularity alone; an additional historical direction-specific term was not robust. However, Ranke et al. (2021, DOI 10.1111/1365-2656.13580) already found that house-sparrow natal dispersal in these SAME Helgeland islands is structured by farm vs non-farm habitat type and inter-island distance. An ostensibly novel pair effect could simply proxy known habitat sorting. We must therefore challenge v1.240 with an **ecologically grounded stronger reference** before treating structural value as novel.

Freeze exactly the author's six farm islands (Nesøy, Gjerøy, Hestmannøy, Indre Kvarøy, Lurøy-Onøy, Aldra; original IDs 20,26,27,28,33,38) and five non-farm islands (Myken, Træna, Selvær, Lovund, Sleneset; IDs 22,23,24,34,35). These labels were verified in Ranke's original published Methods, not inferred from heldout outcomes.

The data remain solely the exact v1.231 frozen observed natal-mark first-year adult resighting matrix. Use *only* pre-2014 migrant cohorts (259 documented IDs) to train, exclude 2014 (28), evaluate the later 2015–2021 cohort (173). All 11 islands stay in the scoring universe. No new individual bird record is reopened.

**Nested forecast reference** (all from historical training only):
- P0(j|i): historical global recipient immigration count plus one Laplace pseudo-event per possible target, excluding the natal island.
- H(j|i): source-specific habitat class affinity via `P0(j|i) × exp(beta 1[same farm class])`; one beta fitted solely on historical origins/destinations by maximizing the historical conditional categorical log likelihood minus beta²/2 using a fixed deterministic 801-point grid −4..+4.
- R2(j|i): symmetrical pair link count `n(i→j)+n(j→i)` smoothed toward H by τ prior pseudocounts.
- C2(j|i): directional historical i→j count smoothed toward R2 by τ.

**Primary endpoint frozen in `development/helgeland_habitat_adjusted_directional_contract_v1_241.json` before fit:** signed R2−H next-era mean log loss (lower is better). Secondary H−P0 and C2−R2. Report fixed τ=5/10/20, all 11 natal source contributions and leave-one-origin-out robustness. No choice after scoring. If R2 benefit disappears after habitat conditioning, that is evidence v1.240 might largely reflect already-published class differences; if it remains, this is *predictive detail beyond broad farm category*, **but still NOT distance-adjusted, detection-adjusted, density-adjusted or a tested demographic source-rescue mechanism**. Ranke previously established shorter-distance and habitat-class assortative dispersal. Do not call this a discovery of habitat sorting or independent confirmation.

The same archipelago and published bird records are repeatedly reused. Zero original 529 mammal heldout responses/predictions reopened, no eBird, no GEB scientific HOLD changes.
