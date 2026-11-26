# NEON: 35サイト×17ドメインの森林区画で植物・地表甲虫の年次群集置換を結合する前段階（2026-11-12）

## Data source, original sampling unit and new site eligibility

Original-source metadata-only intake finished. Public pre-existing derivative **neonDivData 0.3.1**, ground beetles DP1.10022.001 and vascular plants DP1.10058.001, year 2019–2023. The actually observed source `nlcdClass` values are **evergreenForest**, **deciduousForest**, and **mixedForest** in camelCase; initial source code erroneously screened literal space-separated labels and returned zero. This is a diagnosed original-category mapping bug, not a zero-forest ecological result. Source-only fixed-codebook CI [#43203812728](https://github.com/zuizui0223/Structural/actions/runs/43203812728) SUCCESS with no species response read.

After correcting author-provided plot-level labels across all 47 NEON beetle/plant sites:
- **35 siteIDs** have at least one forest NLCD labeled sampled plot in both taxa in same calendar year.
- **166 source site×years**, across **17 NEON ecoclimatic domains**.
- **1,036** beetle forest `siteID×plotID×year` keys, **2,799** plant forest keys; exact shared `siteID×plotID×year` keys **957**. These are source sample opportunities, not species-richness/occupancy, nor 957 independent forests.
- Official site metadata `NEON_Field_Site_Metadata_20260805` SHA256 `d123c8dd131635bbfb1869f8c899f4c0a7930549a6ec531c612a01bd9ad03461`, which has 81 site rows, remains the independent domain/height context. **Eight** strictly all-forest-source-context sites (40 siteyears / 7 domains) remain a nested conservative sensitivity cohort, not the main plot-specific forest frame. A site can have forest plots despite dominant site NLCD including other habitats.
- No original site coordinate, plot ID, taxon identifier/abundance/name was exported. Neither official site mean canopy height nor NLCD plot class is a *contemporaneous plot-level three-dimensional forest structure* measure.

## Source-only field and temporal comparability gate (before taxon values)

The original **NEON Distributed base plot** is the location unit, years are repeated measures. The 2025 published NEON ground beetle guide changed sampling from ten sites' plots per site until 2022 to six plots starting 2023; same-site-but-different-plots cannot be a true temporal turnover contrast. Plant 10/100 m² survey scales can be alternating years; use **1 m² plant subplots** as the source-comparable group. Publication documentation: https://www.neonscience.org/data-samples/data-collection/observational-sampling/site-level-sampling-design and https://daijiang.github.io/neonDivData/ .

Each candidate co-observed plot×year requires:
- plotID is present in **both beetle and plant** data for that site×year and **both plot-level NLCD classes are one of the three exact forest classes**;
- ground beetle original `unique_sample_id`, `trapID`, original `trappingDays>0`; any trap sample with declared `trapConditionFlag` (or `sampleCondition`, if source has it) is **excluded from the strict unflagged effort tier**;
- plant `sample_area_m2=1`, original subplotID and unique sample IDs present; no species response inspected;
- within that original plot×year the nearest plant–beetle sampling dates are ≤30 days. Different activity phenology/trait observation windows remain a caveat.
- a strict consecutive year interval requires at least one **same original forest plotID**, and **one shared unflagged original beetle trapID and one shared 1 m² plant subplotID** sampled in both years. Merely 2019 and 2020 at the same NEON siteID is insufficient.

Only inspect source sample IDs/plotIDs for joins within the CI; export no identities or coordinates. Report eligibility by year, new strict 2022→2023 retention, count **unique physical siteIDs** and distinct NEON domainIDs, never multiply independence by number of plot-years or trap-years.

### Pre-biological admission threshold

For exploratory *forest cross-taxon temporal compositional turnover* to be scored at all, require at least **15 original distinct forest-sampled NEON sites across ≥8 original ecoclimatic domains**, and **≥40 consecutive site×year transitions** satisfying all strict same forest plot, 1 m² original plant subplot, unflagged original beetle trap and 30-day conditions in **both** years. Fix 2019–23 and all original plot/effort rules before seeing species data. If this is not met, the conclusion is **SCIENTIFIC_STOP_SAMPLE_SUPPORT_INSUFFICIENT**, not evidence of absent coupling. Do not shift thresholds, switch years, expand to 10/100m² plant plots, or reinterpret remote sensing as observed forest structure to rescue a positive result.

### Possible single ecological endpoint (NOT YET SCORED)

If the source-only gate passes, compare per-site×consecutive-year **within exactly repeated plot+subplot+trap** Jaccard/Sørensen identity replacement for plant and ground beetle source `taxon_id` sets; do not pool 2019 ten-plots and 2023 six-plots as one changing site community. A plant–beetle synchrony association is observational, with all repeated intervals and physical plots clustered in sites and 17 domains (effective site n≤35), not causal food-web or ecosystem-service transfer. Source taxonomy and zero-catch rows must be verified before any score. Prior PREDICTS baseline reference-relative Simpson replacement (+0.0942 39 Studies; geo secondary +0.0847 in 31 Studies) remains sealed and is a different spatiotemporal estimand.

**State:** 35/166/957 and 8/40/7 are ACTUAL source-only observations; the strict same-plot/same-subplot/trap/source-effort time gate and any biological results are pending. Draft PR #469 unmerged. eBird/TinyFish not used.
