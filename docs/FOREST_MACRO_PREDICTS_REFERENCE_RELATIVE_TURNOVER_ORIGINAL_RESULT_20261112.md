# Structural forest macro: PREDICTS reference-relative turnover (2026-11-12)

## Original biological result — EXECUTED

**Observed difference:** mean Simpson taxon replacement between altered and reference forests MINUS mean replacement among reference forests = **+0.0942**, equal-weighted across original studies. Original Study bootstrap (4,000) 95% percentile CI **[+0.0638,+0.1253]**. Two-sided Study-level 9,999 sign flips **p=0.0001**. **36/39 original studies positive**, 3 negative, 0 zero.

Original source: official Natural History Museum PREDICTS 2016+2022 public diversity extract, joined to original 35,738 site summaries. Source-site selection had already been frozen before opening biodiversity: **1,145 original sites; 39 original Study × method × common-taxon strata; 39 unique Studies; 20 countries**. Exactly **242,677 original eligible taxon measurement records** were used, not species. All 39 study groups passed the original metric and taxon-ID eligibility rule; no group rescues or exclusions. Each source Study contributes one weight, not the many dependent site pairs.

Study-local original Taxon_number was used only within the original Study and a nonnegative Abundance/Occurrence measurement was converted to detection when >0. Mixed taxonomic identification levels remain possible: result is TAXON replacement, not necessarily strict biological species turnover.

**Biomes, purely descriptive:** temperate broadleaf/mixed five study groups: five positive, mean +0.0361. Tropical/subtropical moist broadleaf 34 study groups: 31 positive, mean +0.1028. Not a statistical biome interaction or test across all forest biomes.

**Reproducibility:** [GitHub Actions #43164680231](https://github.com/zuizui0223/Structural/actions/runs/43164680231), both original site support and new original taxon-response jobs SUCCESS. Biological-only aggregate artifact ID 13919791026, digest sha256:e8c5106790a4a055c26eecfbea37a3bd3a4afa47620d873468efe4f335cb564e. Original site-only aggregate artifact ID 13920090031. Pre-effect specification: FOREST_MACRO_PREDICTS_REFERENCE_RELATIVE_TURNOVER_PRESPEC_20261112.md. Implemented analysis: analysis/forest_macro_global/predicts_forest_turnover_original.R. Executed workflow: .github/workflows/forest-macro-global-predicts-support.yml. Source-free synthetic β=0, β=1/3, β=1 and equal-alpha full replacement PASS.

## Ecological interpretation and limitation

This is a positive *within original study* association: an altered forest community differs more in detected taxon identity from the study's reference communities than the reference sites differ among themselves. Simpson component limits pure richness-nestedness confounding, but **there is no demonstration that absolute richness is unchanged**.

This is not an experimental causal impact of modification; not a temporal turnover measurement; not forest structural complexity, a temperature refuge, species dispersal, colonization or extinction. Forest plots and source measurements are historical (strict forest 2019+ sites=0) and provide no contemporaneous validation of a 2020 canopy-height model.

**Important unresolved geographic confounding:** Same-study reference/reference vs altered/reference pairs may have different spatial distance distributions. Geographic distance decay has not been matched or controlled. Do a strict source-site-only geometric support audit before promoting the result to an environmental filtering explanation. Do not revise the current primary effect to select a more favorable geographic outcome.

**Prior art, not claimed novelty:** PREDICTS local forest land-use and beta diversity already extensively studied, including 2026-11-10 Nature Ecology & Evolution (DOI 10.1038/s41559-026-03205-z), based on 38,010 site pairs from 184 studies and Bray–Curtis beta. This analysis adds an explicit study-internal Simpson replacement minus reference/reference dispersion estimand, still a retrospective shared-source reanalysis, not a first independent ecological observation.

**No raw source release:** 2016 CC BY-NC-SA and 2022 CC noncommercial. No source site IDs, coordinates, taxon names, taxon-number values, raw measurements or noncommercial location rows exported to this repository. eBird unused.

**Status:** Study-scale original taxon endpoint DONE. Geography-only conditional support IN PROGRESS. THERA original two-forest HOLD, BALA frozen scorer and GEB mapped-mammal scientific HOLD unchanged. Draft PR #469 unmerged.
