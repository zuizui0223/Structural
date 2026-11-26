# Boreal recovery: author-code audit and reference-panel age design, 2026-11-24

Status: ORIGINAL_AUTHOR_CODE_VERIFIED; SYNTHETIC_CORE_PASS; ORIGINAL_MENDELEY_RESPONSE_HOLD. No new ecological effect.

## Primary-source method audit
Macdonald et al. 2026 Nature Sustainability DOI 10.1038/s41893-026-01868-x, Mendeley original public dataset 10.17632/yt42chsskj.1 version 1, CC BY 4.0. Original author repository EllenMacdonald-UofA/Post-harvest-forest-biodiversity-recovery, exact commit db0325e263486c87c1c8bfac3f8de66617f21674. Three actual files retrieved unexecuted:
- Gamm code - all forest types - for GitHub.R: Git blob 672f627d5d8e7d2f04e07c68d58e30d760effbaf.
- Gamm code - by forest type - for GitHub.R: Git blob 456e88d40107168791a78183f8dbd9c8fad3b51e.
- Chao_Code_for Github.R: Git blob 9a6e39415c86a751e9cf633baf05450cbef50d71.

Both published GAMM scripts use a smooth of YPH and harvested-replicate-nested-in-dataset random intercepts. The all-forest script also has forest-type-specific smooths. They do not explicitly decompose YPH into dataset-centered and dataset-mean age or fit a common-reference-panel-specific within-dataset age slope. The source authors already use the dataset mean reference-reference similarity to construct the reference baseline. Their example plotting code contains an illustrative reference CI procedure; do not infer the published implementation or claim a paper error from the template.

Important new method constraint: the Chao script says some reference-reference pairs were restricted to the same survey year, with study-specific processing. Thus different age classes may be compared with different reference panels. A random intercept alone cannot prove that age differences represent recovery when reference composition also changes. Dataset.Name and Dataset.Code both appear in template scripts; do not guess original public CSV headers, replicate identity, or year semantics. Do not link public study names back to anonymized codes.

## Executed method-only work
Code: analysis/forest_macro_global/boreal_recovery_reference_panel_age_core.mjs, commit 181ada43f26c4ada562ae3d57ad7f6222619ff0a. Known-truth fixture executed in the same tool invocation before committing:
- 12 fabricated harvested units, two valid panels/eight eligible units, two single-age panels excluded.
- Within-dataset deficit slope +0.050 per decade (worsening similarity deficit), between-dataset slope -0.1166667 per decade (apparently improving deficit).
- Duplicate treatment pair, mirrored duplicate reference pair, and extra outcome column all rejected by the routing stage.
- Missing outcome rejected by scorer.
- These are intentionally constructed synthetic values, not Macdonald data or ecological results. No biological response, p-value, or generalization claim.

Core conservative development defaults: one canonical harvested observation ID has one age and one documented panel within dataset×forest×guild. All compared harvests must share the identical reference panel and exact reference ID set; complete unordered reference-reference pairs required; at least two age levels and two harvested units per included age level. These are analyst-chosen development defaults, not yet frozen as final real-source inclusion rules; real raw source method, repeated-census identity, sample opportunities, and age support must be checked before the final protocol. Each harvested unit gets equal weight in its panel slope; panels then equal-weighted per dataset; datasets equally weighted per forest×guild. Between slope from dataset-level eligible age/deficit means, not causal. If source IDs represent repeated censuses rather than physical stands, require an authoritative observation/physical-unit mapping before any biological estimate. Do not treat overlapping guild categories as independent. No p-value from the core, and anonymous datasets may share a parent study.

## Original input dependency
Publisher landing page and article available; original file roster listed Bugs_Arthropods_AllForest_REFvsREF-anon.csv, Bugs_Arthropods_AllForest_TRTvsREF-anon.csv, Metadata_Entity_Level.xlsx. Publisher API URL was not accessible through current web retrieval environment (no verified HTTP status from publisher). Original data bytes, exact headers, year/panel identifiers and age-support counts NOT obtained. Existing Mendeley original metadata gate stays authoritative, not bypassed. No new source request attempts beyond original public page/code and API availability check. Need a single author-published original download archive (or these three original files), then audit exact source fields/anonymous keys without reading numerical similarity, and finalize estimator. If panel provenance is insufficient, stop the stricter panel test; no imputed panel IDs. No old Structural biological endpoint reopened, no eBird/TinyFish, main unmodified, PR #469 stays draft.
