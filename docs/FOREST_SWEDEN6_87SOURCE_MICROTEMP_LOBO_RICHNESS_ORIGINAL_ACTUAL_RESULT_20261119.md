# Sweden6 forest saproxylic beetles — original 87-plotshade microclimate incremental leave-region-out richness: NON-SUPPORT (2026-11-19)

## Scientific decision: new exploratory out-of-region microclimate increment not supported

The independent real source model **actually completed** under a single prospective protocol frozen *before any original richness or temperature value was read*, [protocol](FOREST_SWEDEN6_87SOURCE_LOBO_MICROCLIMATE_INCREMENTAL_RICHNESS_ONEPASS_PRESPEC_20261119.md). The original study is Goßmann et al. 2024, *Diversity and Distributions*, DOI [10.1111/ddi.13836](https://doi.org/10.1111/ddi.13836), which **already studied** beetle communities, shade and regional climatic temperature: these published ecology associations are PRIOR ART. This new Structural question was specifically whether measured previous-year under-bark temperature added incremental **unseen-region richness prediction** beyond climate, horizontal shade, bark and diameter. 

**Outcome: NON-SUPPORT of extra geographical prediction, NOT absence of biological microclimate effects, NOT a thermal refugium/3D resource-lock test.** No retuning or re-scoring after observed result.

## Exact original source/independence receipts

- Original official SLU [dataset DOI 10.5878/dhmc-bq15](https://doi.org/10.5878/dhmc-bq15), only `boreal_forest_climate_data.csv` **7,019 bytes**, SHA256 **`d546273c352fb2cab97f63f35883f970baea09790348fa4c0dda3e1bc55ba776`**, 12 exact author fields. Identifiers authenticated **BEFORE** numeric environment/richness read.
- Original response-blind source identity diagnosis [Actions #44475592190](https://github.com/zuizui0223/Structural/actions/runs/44475592190), anonymous source artifact **#14506107626**, ZIP SHA256 **`7b902c5669d660d56635331805feb6069c1d62781d16f56baa63348b1c30c598`**: source climate **87 data rows, 29 original `Block×Plot` physical sites**, six source regions (4,5,5,5,5,5 plots), three **horizontal forest-edge shade** groups at each plot, **87 unique matching `Block×Plot×Shade`** physical cells, **zero duplicates, zero missing shades**, all within independently published Block/Plot codebook ranges.
- Separate original beetle raw species list was verified in the source-ID-only audit but was **NOT downloaded/opened during this new biological model**. Its original 3,459 positive species-record rows contain **two extra author-invalid Block5 Plot keys**, so the earlier full species↔climate strict join STOP remains permanently preserved. These two unmatched keys were not reassigned or treated as response zeros. Only original **source-authored richness field** in the 87-row environmental summary was used as the response.
- Actual one-pass source GitHub Actions [#44477278936](https://github.com/zuizui0223/Structural/actions/runs/44477278936), **SUCCESS**, aggregate artifact **#14506544163**, SHA256 **`f733b43e558844d1f32504814f18d65d9e7b8819d39048333a2c44db47d3047c`** (independently hash-verified). No raw plot IDs, temperature values, original source rows, taxon names or author `CTI/Totlab` values exported; old historical PREDICTS, Finland, Carpathian, England, Thai, NEON, BALA and GEB scores sealed.

## Prespecified one held-region-out response contrast — actual numbers

Response: log1p of original author `Species richness` from 2021 spruce-log observations, 87 plot×shade nested sampling units. Six geographically blocked folds, whole original Block left out each time (heldout 12, 15, 15, 15, 15, 15 source rows). Original baseline **E0** has `Regional climate`, 2020 measured `Makrotemp`, two shade indicators, `Bark`, `Diameter`, and sin/cos of circular `Aspect`. **E1 adds only original 2020 measured under-bark `Mikrotemp`**. Ridge penalty λ=10 with unpenalized intercept, train-only z scaling, no tuning.

| Result — heldout original regions equally weighted | Source original value |
| --- | ---: |
| E0 region-equal MSE, log-richness | **0.0415338578067** |
| E1 (+ microtemp) region-equal MSE | **0.0412326375028** |
| E0 − E1 ΔMSE (positive means improvement) | **+0.00030122030388** |
| Relative regional MSE reduction | **0.72524%**, **small** |
| Source regions with positive ΔMSE | **4/6** |
| Exact 64 region sign-flip two-sided conditional p | **0.78125** (50/64 as extreme) |
| Frozen 4,000 region bootstrap percentile 95% CI | **[−0.0014672219, +0.0020696625]** |
| Site-equal relative heldout MSE reduction (secondary descriptive) | **0.59332%** |
| Original exploratory support criterion | **FAILS** |

All calculations above were independently checked against the original ZIP source aggregate. A small positive average difference is not a supported generalizable improvement: uncertainty includes both signs, p is far above 0.05, and only four of six source regions improve.

## Scientific scope

1. This is a **single-country six-region retrospective field study**, not globally independent forests/biomes. Six Block bootstrap/signflip uncertainty is conditional and limited, and plots/shades are nested within each region, not 87 independent macroecological geographic tests.
2. Observational nature: spruce wood substrate was present in **all** treatments; microclimate logged under bark in **2020**, emerging beetles in **2021**. The gradient is **horizontal forest-edge shade**, not different vertical canopy layers. We cannot test actual movement, source-sink processes, heat escape, resource absence or the cause of region-dependent richness.
3. E0 already includes shade, 2020 macro air temperature, regional climate, resource bark and diameter, so microclimate might be partly redundant as a predictor, but this exploratory non-support does **not** prove physiological or ecological redundancy.
4. Source authors already published macroclimate × shade association and species richness/CTI; this new result is **a bounded predictive increment**, not novel experimental field work. Do not reformulate a positive thermal filtering causal claim from its small ΔMSE.

## Next non-retry decision

**Freeze the one-pass result permanently.** No alternative richness transformations, different ridge λ, dropping regions/sites, CTI response, post-hoc microclimate interactions or raw beetle list correction should be used to rescue a favorable outcome. To directly test the stronger proposed 3D ecological hypothesis, seek an **independent multi-forest source jointly sampling same-method canopy/understory heights, co-temporal microclimate, presence/absence of actual hostwood substrates, standardized effort and taxon-comparable responses**; predefine leave-region-out predictions before opening new biology.

Prior forest + island mammal results and original GEB holdouts unchanged, no eBird/TinyFish; PR #469 Draft/unmerged, `main` unchanged.
