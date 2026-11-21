# Sweden six region spruce beetles: microtemperature and wood substrate out-of-region CTI prediction — ONE actual original exploratory result (2026-11-19)

## Scientific decision: substrate properties DO NOT improve held-region predictive CTI

**Frozen E1 + Bark/Diameter vs E1 microtemperature-only incremental prediction is NOT SUPPORTED.** The novel value of this source-level run is a measured, precommitted **out-of-region predictive comparison**, not the discovery of a new thermal/vertical sorting mechanism. Adding 2020 spruce substrate Bark and Diameter **worsened**, rather than improved, prediction of original 2021 beetle community temperature index (CTI) in the six-region-equal pre-frozen model. It is NOT proof that the substrate properties are ecologically irrelevant, nor the missing-host thermal-refuge/3D resource-lock hypothesis.

Source prior art: Goßmann et al. (2024) already established regional climate×shade relationships for richness and CTI (DOI [10.1111/ddi.13836](https://doi.org/10.1111/ddi.13836)); the [SLU source record](https://doi.org/10.5878/dhmc-bq15) contains the original data but is not independent of that publication.

## Original file and source integrity

Exact public SLU eArchive climate source `boreal_forest_climate_data.csv` **7,019 bytes**, SHA256 **`d546273c352fb2cab97f63f35883f970baea09790348fa4c0dda3e1bc55ba776`**. Original author 12-column semicolon header `Block;Mikrotemp;Makrotemp;CTI;Plot;Shade;Bark;Diameter;Regional climate;Aspect;Species richness;Totlab`. The record has **87 data rows +1 header**, not 88 data records. The author nominal 30 physical plots ×3 shade categories corresponds to a fully measured subset of **29 plots ×3 shades =87 rows**. The one missing physical plot was in original geographic Block 3; measured Block sizes **15,15,12,15,15,15 plot×shade rows** (plot counts 5,5,4,5,5,5). All six measured environmental predictors finite on **87/87 source rows**. No missing shade treatment within the 29 actually measured plots.

Method/source receipts:
- Original species header source mismatch resolved independently: original seven-field species CSV (not original README six) [source header diagnostic #44454288129](https://github.com/zuizui0223/Structural/actions/runs/44454288129). Exact three-file first-header receipts [#44454611956](https://github.com/zuizui0223/Structural/actions/runs/44454611956).
- Original climate source 88 lines INCLUDING header [#44455179126](https://github.com/zuizui0223/Structural/actions/runs/44455179126), and original actual 29 measured plots (not 30) diagnosed without accessing `CTI` or original beetle species values [#44455751943](https://github.com/zuizui0223/Structural/actions/runs/44455751943), artifact #14498200140 ZIP SHA256 `308f977da59ca5c2ebf9f62d68fbd0604fb6cf0f7364e41ce4ce5f953a12cf4c`.
- All earlier initial six-field, 88-DATA-record and 30-plot source admission STOPs **remain unchanged**. The new original 29-plot source cohort was explicitly precommitted **BEFORE CTI source values were opened**, [original CTI onepass protocol](FOREST_SWEDEN6_CTISUBSTRATE_REGION_HOLDOUT_EXPLORATORY_ONEPASS_PRESPEC_20261119.md).

## True original onepass biological result and independently checked arithmetic

[GitHub Actions #44456227399](https://github.com/zuizui0223/Structural/actions/runs/44456227399) **SUCCESS with actual original CTI data score**, source aggregate artifact **#14498046652**, ZIP SHA256 **`83cf68e8bac532cb6178b06f5684a1353a26d042b60b78bffdfd6e7c3327b9a7`**. Downloaded artifact JSON and its ZIP SHA independently audited. All source 87 CTI values finite, source CTI range **4.3492 to 5.105686275**. The original source paper's CTI already represents a derived, recorded community temperature index, not a newly collected observation or individual thermal-behavior measurement.

**Frozen model:** six independent **leave-one-original-geographic-Block-out** folds, source 87 plot×shade samples (Block3=12, five other blocks=15); train-only feature means/scales, multivariate ordinary ridge λ=10, unpenalized intercept, continuous CTI predictions. `E0`: original long-term regional climate, original 2020 macro air temp, shade2/shade3 dummy, circular plot aspect sin/cos. `E1`: E0 + original measured 2020 under-bark `Mikrotemp`. `E2`: E1 + 2020 `Bark`, `Diameter`. Specieslist's original 3,460 beetle record body rows, and source `Species richness`/`Totlab` biological columns, were **never opened** by this workflow.

| Source leave-region-out model | Region-equal heldout MSE (original CTI²) |
| --- | ---: |
| **E0:** regional/ambient climate + shade + aspect | **0.008924347807** |
| **E1:** E0 + measured under-bark Mikrotemp | **0.008523818686** |
| **E2:** E1 + Bark + Diameter | **0.008726307245** |

- **Primary fixed substrate increment** `Δwood = E1 MSE − E2 MSE = −0.000202488559 CTI²`: NEGATIVE, meaning E2 is **worse by ~2.376%** relative to E1. Original six geographic block deltas positive in **2/6**.
- **4,000 fixed-seed six-block bootstrap 95% percentile interval:** **[−0.001458379128, +0.000927678796] CTI²**, crosses 0.
- **Exact 64 two-sided block sign-flips:** **44/64 = p 0.6875**; one precommitted support criterion fails. Not a statistically significant out-of-region resource-predictive improvement.
- **Secondary purely descriptive microtemperature increment** `E0−E1 = +0.000400529121 CTI²`, **4.4880%** reduction in prediction error from E0 to E1, positive in **4/6 regions**. **No separate formal inferential test** was precommitted for this secondary contrast, so do NOT claim significance/replication/temperature causality from its positive average.
- All difference arithmetic was **independently recomputed from the SHA-matched original aggregate ZIP**, agreeing with the actual scorer at floating-point precision. Exact p recomputed 44/64. No original site/plot/taxon/CTI raw outcome rows exported.

Final source scientific status: `EXPLORATORY_SWEDEN6_WOOD_CTITEMPERATURE_OUTOFREGION_INCREMENT_NOT_SUPPORTED`.

## What the result DOES and DOES NOT mean for forest ecology

1. In this **one original six-Swedish-region source**, wood remaining-bark and mean diameter **did not add robust out-of-block prediction** of the already published thermal composition endpoint after measured microclimate and strong regional macro/shade controls. All original logged wood was standardized spruce, and the exposure is mean 2020 substrate attributes paired with 2021 observed beetle CTI — not simultaneous individual species habitat use.
2. The finding is about **incremental prediction of one aggregate community trait**, not whether tree identity, host scarcity, wood availability, vertical niche accessibility, deadwood causal microclimate, individual dispersal, species abundance, or resistance to warming are important. Given fixed host spruce, **the resource-absence mechanism has no observed contrast**.
3. Six regions nested within one country/sample are not six independent global forest biomes, and the small conditional p/bootstrap have only six geographical support units. The original authors' 2024 within-dataset thermal/shade associations are PRIOR ART.
4. This negative Swedish CTI outcome is **not** a strict independent replication or contradiction of Finnish Host_tree guild Hellinger² increment +0.00024237 (different response/model/grain) or Carpathian trophic-guild deadwood increment −0.00106793 (different trait ontology). Do not average their signed coefficients or label one "universal".
5. The full **three-dimensional resource lock hypothesis remains untested**: requires source-comparable same-method canopy/subcanopy species, measured contemporaneous microtemperature and actual availability of limiting host/wood at each layer, multiple original independent forests. A 6-region spruce-source CTI model does not provide such data.

## Next action, bounded

Freeze this single CTI source score. **Do NOT** adjust its six-block eligibility, λ, input transformations, CTI score, shade encoding or forestry covariates after viewing the outcome; do not read `specieslist_xylo.csv` to chase a favourable subgroup. Rather, seek an original independent experimental forest network with source verified **same sampling method × height × resource availability × microclimate × beetle species** source records for a genuinely 3D thermal-resource access test. If missing any required field at the physical location/time, scientific hold before biology; no post-outcome rescoring.

PR #469 remains **Draft, unmerged**, `main` unchanged; all original NFI, Finland, Carpathian, PREDICTS, Thai, NEON, BALA and global mammals frozen. No eBird/TinyFish.
