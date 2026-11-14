# Forest resource vs access: fixed exploratory contrast (2026-11-08)

## Motivating ecological question

**同じ程度の周辺樹木被覆率の下で、道路・建物のような人為障壁に遮られていない方向が多いほど、在来の樹皮食・材食性甲虫が多く検出されるか？**

This directly asks whether spatial *access* to woody resources holds a distinct association beyond the local *amount* of trees, connecting the island macroecology resource availability versus realized source accessibility discussion. This is not an empirical dispersal movement measurement, a forest-fragmentation experiment, or a 3D vertical niche test.

## Data frozen BEFORE this outcome test

- Nardi et al. (2026), Ecological Applications, DOI `10.1002/eap.70194`, original Zenodo v3 `10.5281/zenodo.17044394`, four source-MD5-verified tables.
- Unit: 207 `(SITE, CELL_ID)` trap cells, 13 original landscapes across 8 countries. Landscape is the higher independent design unit; 207 trap cells are not 207 independent forests.
- Original trap covariates `composition` = tree cover (%) within 250 m; `configuration` = angular percentage of area without main roads/buildings (%), both increasing toward natural resource/access conditions. `urbanization_index` = their composite; **do not adjust for both and their composite**.
- Prior source-only support CI **#42446324361** (run SUCCESS) read only 207 trap-environment rows, no beetle outcomes: global r=0.848715, landscape-demeaned r=0.699053, residual configuration variance retained after controlling composition =0.511324, VIF=1.956; 11/13 landscapes have at least one pair differing `composition` ≤10 percentage points and `configuration` ≥20 points, 179 such *dependent* pairs. Independent-variation criteria fixed in code were satisfied. No ex-post attempt to choose a different urbanization or tree-cover radius after biological scoring.
- The 301-column `bio_cast.txt` is a 0/1 detection matrix; it exactly matches all 3,215 positive CELL×species incidences in `bio_data_trapscale.txt`. `STATUS` Native/Exotic is assigned **within (SITE,SPECIES)**, not as an invariant global species attribute (7 names switch status across study regions). Main response is **number of unique Native species labels with positive detection at a cell**, not total beetle count, since source long N sum=61,769 differs by 14 from the article’s published 61,755.

## Exactly one planned test

1. Fixed response: `Y_native_richness` = count of distinct `SPECIES` with `STATUS=Native` and `N>0` at each `(SITE,CELL_ID)`. Cells with zero native detections remain Y=0 (sampled cell is observed; species nondetection is not biological true absence).
2. Reduced source amount model: `Y ~ SITE fixed intercepts + composition` with `composition` in percentage points.
3. Full resource-plus-access model: `Y ~ SITE fixed intercepts + composition + configuration`. The **unique configuration coefficient** `β_configuration` is estimated by site-demeaning both covariates and Y, then partialling configuration on composition (FWL theorem). Interpret as additional **observed native labels per trap per +10 original configuration percentage points** *conditional on cover*; do not interpret as beetle dispersal efficacy.
4. Inference: resample **13 landscapes as whole clusters** with replacement for a 5,000-replicate bootstrap CI for β. For a 9,999-replicate two-sided exploratory Freedman–Lane-like test, obtain residuals from reduced SITE+composition model, shuffle reduced residuals **within each of the 13 landscapes** (not SITE identities, not 207 globally), add the reduced fitted values back, and recompute unique β_config with original fixed covariates.
5. Frozen support criterion: the unique configuration coefficient is positive AND its 95% landscape-cluster bootstrap lower bound exceeds zero AND the 9,999-replicate two-sided conditional permutation p ≤0.05. If not, state **not supported** and retain the estimate/interval/p as calculated. Secondary descriptive diagnostics only: β_composition in full model, leave-one-landscape-out coefficient sign stability, amount of residual configuration variation, per-landscape native richness/variation. No alternative responses or cutoffs selected afterwards.

Source-specific limitations: original Nardi et al. (2026) already found native beetle richness and abundance fall with a combined urbanization index and openly noted that tree cover and barrier-free angles were correlated (r=0.85). Their published inference did not separately distinguish resource amount and barrier-free angular availability. This is **secondary, observational, source-dependent reanalysis**, not a new independent confirmation. Correlated predictors and spatially autocorrelated traps limit transport; 13 landscape clusters and the permutation do not remove unknown confounders. Species/morphospecies source naming and lure/bait detection differences may affect diversity; no source population movements, recolonization, true local absences, canopy height, thermal refuge, or island network effects are identified.

The previously frozen exotic-share ~ combined urbanization test with 13 landscapes remained not supported (p=0.3723) and is NOT rerun or selected among multiple endpoints. The Thai 2-forest canopy beetle positive is unchanged. eBird excluded. Original source data only, with source identifiers/species names never exported by the new analysis.
