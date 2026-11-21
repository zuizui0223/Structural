# NEON forest patches 2019–2020: fixed 3-plot comparable cohort for canopy-structure vs community spatial turnover (2026-11-14)

## Actual original-source sampling design qualification PASSED — no biodiversity response opened

Original original-source source-only CI [#43562142519](https://github.com/zuizui0223/Structural/actions/runs/43562142519), SUCCESS. Anonymized aggregate artifact **14100882939**, digest **sha256:0c9b163d361747fef8254645fdb581bf9b935ea0dd3b68344b2c12be3f4aa3cb**. Original NEON site/plot/year sampling identifiers, coordinates, CHM per-plot p90, original beetle or plant taxon names, organism counts and species incidence matrices were not exported or read as response.

Original population selected BEFORE species values:
- Independently published source-verified Meta/WRI CHMv2 static canopy p90: previous 237 original forest plots and 232 with positive pixel QA across 34 original NEON sites, matched to 35 overall source forest sites. [CHMv2 source raster QA](FOREST_MACRO_NEON_META_CHMV2_40M_PLOT_PIXEL_SOURCE_QA_ORIGINAL_RESULT_20261114.md).
- **Year restriction**: original 2019 and 2020 NEON beetle/plant forest plots only, because a static CHM based mainly on imagery 2018–2020 is not a 2021–2023 plot-year tree measurement. The year restriction does NOT demonstrate pixel acquisition in 2019/2020 and was fixed [before opening the taxa](FOREST_MACRO_NEON_2019_2020_CHMV2_FOREST_HEIGHT_COMMUNITY_SOURCE_DESIGN_PRESPEC_20261114.md).
- Forest plot original `nlcdClass` and same `siteID×plotID×year` in beetle and plant observation sources; `neonDivData` 0.3.1, original official NEON 81-site 2026-08-05 site/domain metadata. Source beetle unique sample/trap ID, unflagged and `trappingDays>0`; source plant 1 m² unique source sample and subplot ID. Plant's first original sampling date ±7d for plant, beetle records ±30d; at least 4 beetle source sample IDs and 4 *recorded* plant1m² subplots. Source trap effort must be consistent within an original sample ID.
- Each same site–year needs a **complete mutually compatible 3-original-plot group** (each of three beetle trapping-days effort ratios and each of three recorded positive plant subplot-count ratios 0.5–2, and first plant survey DOY difference <=30 days). Within the source group, CHM p90 of at least two plots must differ. If more than one clique, choose largest complete compatible source plot group and stable original plot ID ordering, without consulting taxa. No pairwise independent sample claim.

| Support stage | Observed original source count |
| --- | ---: |
| Candidate 2019–2020 forest plot×year original two-taxon source identity | **395** |
| Public CHMv2 source original 40m positive-pixel QA in same original plot | **388** |
| Same plot×year original beetle+plant records fully present before seasonal effort screening | **388** |
| Valid beetle>=4 source trap samples and plant>=4 recorded 1m² subplots within fixed common sampling period | **340 plot×years** |
| Original site×year groups with >=3 source-screened original forest plots, before complete pair comparability | **45** |
| **Complete eligible original three-or-more-plot mutually comparable CHM-contrast site×year groups** | **44** |
| Independent original NEON sites represented | **26** |
| Original ecoclimatic NEON domains represented | **15** |
| Original plot×year sample instances in the complete compatible groups (NOT independent) | **303** |
| Source pairwise plot contrasts in the complete compatible groups (NOT independent) | **992** |
| Site-specific chosen source year (2020 if eligible, otherwise 2019) | **26 site×years**, one/site |
| 2019 vs 2020 all original eligible siteyear groups | **26 vs 18** |
| Median within-siteyear p90 static CHM height range | **9.5 m** |
| Median within-siteyear original plot centre pairwise distance | **2.2321 km** |
| Exact coordinate-distance-zero plot pairs | **0** |
| Source CHMv2 **tile date-window** overlaps same original survey year (non-proof) | **223 selected plotyear records** |
| Predeclared minimum 10 sites / 6 domains / 12 site×years | **PASS: 26/15/44** |

**Result is a genuine source-design positive**: the earlier strict original 2019–2023 VST `sampled_with_records` + matched source dates and sample effort cohort stopped at 10 sites/8 domains/10 site×years and could not be promoted to a structural mechanism. Under a *new, independently sourced static satellite CHM population* restricted to 2019–2020, a geographically distributed source sampling design exists with 26 sites/15 domains/44 time strata. This does NOT retroactively validate the original VST source STOP. It does not indicate that beetle or plant turnover is significantly related to height.

## Scientific next step and explicit measurement limitations

The next biological **exploratory** estimand, if frozen and executed once, must keep source site/year/plot IDs, source masks, common sampling season, source thresholds and per-site-year complete original plot cliques unchanged. **Ground beetle species-rank incidence Simpson replacement** between original forest plots is the planned primary endpoint, against `abs(CHMv2 static p90 height difference)/10 m`, controlling original geodesic `log(km+0.05)` and NEON source site fixed effects. Plant recorded taxa may serve as separately labelled secondary channel, with missing zero-record surveys explicitly acknowledged. Original pairwise sites/plot-years 992 or 303 are NOT independent; inference must be original NEON site block, with site-level permutations of **plot canopy labels**, not pairwise shuffles, and site bootstrap or other source-site uncertainty. Select at most one eligible original calendar year per site (2020 preferred if both) before accessing response taxa. Source biology validity/identification ranks must be rechecked before fitting; undefined β due a genuinely zero-source-positive assemblage is missing, not a true absence.

The spatial CHM source is 40m square around original basePlot centres, **not the author-original NEON plot polygon**. CHMv2 image pixels are a single satellite composite, and source scene date-window **cannot prove which year each pixel was acquired**. The 2.23 km median spatial separation of source plot pairs means species turnover can arise from distance and habitat/history rather than canopy structure; adjusting distance is essential but cannot guarantee causal exchangeability. The independent field-vs-CHM proxy height `ρ=+0.906` across 22 sites does not establish local biodiversity effects. Model result—if any—is not a first independent field study, since organismal data are still the pre-existing publicly distributed NEON cohorts already used for temporal analyses.

Precompiled code: `analysis/forest_macro_global/neon_chmv2_2019_2020_forest_community_source_triads.R`, original source coordinates and CHMv2 40m QA code, workflow `.github/workflows/forest-macro-neon-vst2026-forest-patch-source.yml`. **No species/taxon/value or ecological response scored in this step.** Previous PREDICTS +0.0942, distance +0.0847, temporal NEON −0.0664 p=.536 are SEALED; eBird/TinyFish unused, Draft PR #469 unmerged.
