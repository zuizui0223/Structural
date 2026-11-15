# Finland forest macroecology: local deadwood adds small geographically held-out predictive information for saproxylic beetle host-affiliation guild composition (2026-11-15)

## Main ecological result — one frozen original-source test executed

**One** original-data post-result exploratory test was fixed in [this pre-effect protocol](FOREST_BEETLE_FINLAND_142SITE_DEADWOOD_HOSTGUILD_SPATIAL_HOLDOUT_PRESPEC_20261115.md) **before joining original forest covariates to Host_tree beetle community values**. The original GitHub Actions [#43679687495](https://github.com/zuizui0223/Structural/actions/runs/43679687495) ran all source/known-truth/ridge/grid tests and the original 142-site spatial holdout end-to-end **SUCCESS**. Anonymous original aggregate artifact **14147569258**, GitHub ZIP SHA256 `4eaf044c924fdbea0a92954b02e0a8fd664808a4134df7f757e14f336fa331e9`.

**Primary answer, explicitly conditional and small:** Adding the author-measured local deadwood amount `VD10` as **one** predictor to an already specified forest environment/effort/geography baseline improved out-of-1°-latitude-by-2°-longitude-grid prediction of the **three-guild Host_tree incidence-composition** of Finnish saproxylic beetles:

| Original-source fixed primary measure | Actually computed |
| --- | ---: |
| Verified original Finland forest physical sites | **142** |
| Exact source 2022 beetle sampling-year × 2023 author forest covariate matches | **142**; exclude 10 other-year repeats and 1 unlinked event by source design |
| Source original Host_tree-known species active in same-year cohort | **332** |
| Original occupied 1° lat × 2° lon geographic holdout grid cells | **9** |
| Cells with heldout prediction improvement / worsening | **7 / 2** |
| **Primary cell-equal ΔHellinger² error** (baseline − baseline+VD10) | **+0.00024237** |
| 4,000 resampled-grid-cell 95% bootstrap percentile interval for Δ | **[+0.00012123,+0.00035658]** |
| 9,999 signed-grid-cell permutations two-sided conditional p | **0.0150** |
| Site-equal baseline heldout mean Hellinger² loss | **0.00574894** |
| Site-equal +VD10 heldout mean Hellinger² loss | **0.00556866** |
| Site-equal loss improvement | **+0.00018027 (≈3.1% relative)** |
| Largest/minimum occupied grid-cell site count | **45 / 1** |
| Source distinct actual sampling years | **5** |

The fixed exploratory support criteria Δ>0, cell-bootstrap CI entirely >0 and conditional signed-block p<.05 were all achieved. **No variance-explained claim, model selection or opportunistic hyperparameter/threshold changes are made after seeing this result.** The positive heldout gain is small relative to the low baseline Hellinger loss.

### Original measurement definitions and source-QA correction

Source publications: Burner et al. 2022 Zenodo v1 [10.5281/zenodo.5950610](https://doi.org/10.5281/zenodo.5950610), 2023 Zenodo v1 [10.5281/zenodo.8322080](https://doi.org/10.5281/zenodo.8322080), Burner et al. (2023) *Ecology & Evolution* DOI [10.1002/ece3.10588](https://doi.org/10.1002/ece3.10588). In that source:

- `VD10`: originally measured combined local standing and fallen deadwood of diameter >=10 cm in m³/ha, published here **already log-transformed and standardized**, so model coefficient unit is a source z-score, **not** 1 raw m³/ha.
- `agedomin`: age of five oldest trees in the stand, published standardized.
- `OldFor_1km`: live woody volume in forest older than 100 years within 1km (landscape old-forest **proxy**), not local deadwood volume and not broadleaf/conifer composition.
- `MeanTemp`, `TotalPrecip`, `globRad_WHm2`, `log_Nr_traps`, WGS84 latitude/longitude and `Year`: original separate climate/solar/method/geographic/temporal covariates, all available at 142 source physical sites.

The **first environment-only CI #43679235261** correctly read all 142 rows but mistakenly assumed source `VD10/agedomin/OldFor_1km` were raw positive physical amounts and therefore reported a SOURCE STOP when negative values occurred. Paper and actual original values show already log/z standardized predictors, confirmed in source-only corrected [CI #43679370273 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43679370273): each exactly mean zero / sample SD one (within displayed precision), all three **142/142 complete**, Spearman correlations `VD10~agedomin=+.427027`, `VD10~OldFor_1km=+.306154`, `agedomin~OldFor_1km=+.395610`. This **source-scale code and interpretation correction happened before any forest environment–beetle-response pairing**. No source biological outcome was opened to choose a transformation. Source-only environment artifact **14147891119**, ZIP SHA256 `4e0b4328097b0fcf744fa93e3bf871447e32f2acd136729c48b3df8103203252`.

### Fixed model implementation and testing scope

- Exactly **142 original 2023 Year_Site author rows** were joined one-to-one to original 2022 Finland species×sample-year columns BEFORE reading taxon counts. The 2023 *same-year* 142-site design differs intentionally from the older physical-site OR-incidence sensitivity that grouped **152** survey-year observations across **142** author sites. The earlier guild result, original country-wide matrix and all other countries remain sealed/unchanged.
- Per site, original species count>0 is presence for the same 2022 exact Year_Site survey; known `Host_tree` traits assign distinct guilds **broadl / conifer / both**. Observed `Y=sqrt(p)` is the 3-category Hellinger representation of the *fraction of recorded guild-known species*, NOT the amount of actual broadleaf/conifer tree or saproxylic beetle biomass. Site-level active guild-known source beetles **332**, as opposed to the previous OR-over-years 358; this is a **different pre-committed year-matched source population**, not a favorable taxon subset.
- Baseline ridge `λ=10` (intercept unpenalized), nine fixed predictors: `agedomin, OldFor_1km, MeanTemp, TotalPrecip, globRad_WHm2, log_Nr_traps, lat_WGS84, lon_WGS84, Year`. Extended ridge has those same nine **plus VD10 only**. All covariates re-centered/re-scaled on training sites per geographic fold only. The predicted 3-vector was truncated nonnegative and Euclidean-normalized; site loss `0.5*sum[(predicted sqrt guild share−observed sqrt guild share)^2]`.
- **9** occupied geographic cells using frozen `floor(latitude)`, `floor(longitude/2)` prebiology grouping, each held out in turn; all original other cells used for training. Minimum training fold size **97** sites; occupied cells sizes range **1 to 45** (median 13). Cell-equal mean loss difference used for primary estimand, site-equal difference secondary. Each test prediction was generated without access to that cell's original beetle community response. Cell-paired bootstrap **4000** and signflip **9999** came from prespec (not post hoc reruns). Synthetic original-empty, positive, null, negative and fold-leakage controls ran PASS.
- The full source fit's **descriptive** `VD10` coefficients in the sqrt-guild embedding were broadl **+0.01937166**, conifer **−0.0045084**, both **−0.01144219**. They were not separately selected or tested and cannot be used to claim a broadleaf mechanism independent of the single multivariate whole-guild endpoint.

### What this adds and what it does NOT establish

This is the **first** result in the Structural forest-macro branch linking the original Finnish forest's **measured local resource amount** to observed beetle `Host_tree` guild composition under a fixed out-of-geographic-block predictive contrast, beyond multiple fixed local-forest/climate/geography/sampling features. It contributes a bounded mechanism-consistent **association** instead of equating general taxonomic replacement with forest structure. However:

1. A 1°×2° holdout grid is an **approximate spatial split**, **not** held-out independent countries, forest biomes or study networks. One grid cell contains one source site; adjacent-grid sites may be close. Only **9** geographical blocks, so paired signflip p assumes sign exchangeability across heterogeneous cell errors and block-bootstrap intervals do not guarantee fully calibrated geographical uncertainty. No causal forest deadwood manipulation was randomized.
2. `VD10` is **total local deadwood**, not the locally measured broadleaf versus conifer or tree species inventory. A positive predictive gain cannot identify actual host resource identities, local movement pathways, species adaptation, canopy microclimate, vertical stratification, ecosystem functions or changes in biomass. Other correlated forest conditions, age, landscape history and imperfect beetle detection can drive shared patterns despite adjustment.
3. The 2023 original authors have already explored **dispersal trait–niche** associations with the same Finnish environmental data; we claim a **distinct original-data retrospective guild-composition predictive contrast**, not a new study or unrecognized absolute deadwood biodiversity effect. The signal is **3.1% relative held-out error reduction** at the source site equal scale; ecological magnitude is modest.
4. Nonrandom taxon identity, trait phylogeny, macroenvironmental history and detection bias are not fully addressed. The existing separate `Host_tree` trait-label null D=.035237/p=.000333 is **NOT** used to raise the new fixed spatial predictor test's statistical significance. The old original 3-country D=.091059, PREDICTS +.0942, NEON CHM +.0349/p=.1759, BALA and GEB holdouts remain frozen.

**Recommendation:** retain the result as a **small exploratory spatially held-out positive** for forest resource amount in the **same Finnish observational dataset**; the follow-up for independent ecological support is a fresh forest network with original tree species/host wood composition, beetle guilds and matched detection effort/time. No alternative grid, taxon threshold or source covariate rescue searches are authorized on the already-opened cohort.

## Code / CI / rights
- One-shot original code: `analysis/forest_macro_global/finland142_deadwood_hostguild_spatial_holdout.py`.
- Single workflow: `.github/workflows/forest-macro-finland142-deadwood-hostguild-spatial-holdout.yml`.
- Frozen prebiology design: `docs/FOREST_BEETLE_FINLAND_142SITE_DEADWOOD_HOSTGUILD_SPATIAL_HOLDOUT_PRESPEC_20261115.md`.
- CI run [#43679687495](https://github.com/zuizui0223/Structural/actions/runs/43679687495) SUCCESS; artifact **14147569258** ZIP sha256 `4eaf044c924fdbea0a92954b02e0a8fd664808a4134df7f757e14f336fa331e9`.
- Anonymous aggregates only; no raw author source site labels, species, tree data, geography, individual trait vectors or individual fitted site predictions exported. No eBird/TinyFish. Draft PR #469 unmerged.
