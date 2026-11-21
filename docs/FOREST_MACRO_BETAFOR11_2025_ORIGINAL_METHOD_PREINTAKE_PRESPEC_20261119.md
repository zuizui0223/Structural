# BETA-FOR 11-forest manipulation — source-metadata-only pre-intake (frozen 2026-11-19, before any source biological read)

## Why this ONE candidate

The currently closed forest evidence synthesis finds repeated PREDICTS reference-relative replacement, one small Finnish Host_tree deadwood prediction increment, and independent negative Slovak and Swedish increments with different endpoints. Neither pooling those increments nor claiming a general resource mechanism is justified.

**New evidence need:** a field treatment with separately manipulated canopy opening and deadwood retention, standardized observation opportunities and physically independent forests, so that out-of-forest *portability* of a predeclared treatment response can be distinguished from forest structure/resource observational proxies.

**Candidate original programme:** Rothacher et al. (2025), Journal of Applied Ecology DOI **10.1111/1365-2664.70086**. The authors already established within-experiment taxonomic/phylogenetic diversity treatment effects: **PRIOR ART**. Original author publisher **Zenodo 10.5281/zenodo.15371332, published version v1 (May 9, 2025), CC BY-SA 4.0**; analytical source code DOI **10.5281/zenodo.15165462** is a distinct source to inspect separately after this gate.

Published independent design: **11 forest sites in 6 German geographic regions**, **9 original 50×50-m experimental patches per forest**, one control, eight assigned treatments, **6 trap sample periods** using the same Malaise capture technology, nominal 11×9×6=594 sample occurrences. Forest is the experimental-block unit; `patch` is a treatment assignment unit, collections are temporal repeat samples, NOT 594 forests. The 2022/2023 source years and treatment-implementation vintages differ among regions, potentially confounding geographic transfer.

## Source-only intake: exactly what is permitted

Use one official public `https://zenodo.org/api/records/15371332` record GET, and nothing else. Parse only the publisher JSON `id`, `doi`, published status, original version, original file **name/size/checksum**, and license. Verify frozen original six-file MD5 name map:

- `BETAFOR_information.csv`: `873f5d424904d1eed00e079b945dd5dc`
- `calibration_points.csv`: `6c9a9dedc5ec0958ae4964b30a7b0433`
- `com_singletons.csv`: `81e2c1269bff49fafdf497f03f5922b2`
- `insects_rainford_adapted.tre`: `491b4d81ec65e94a1b6213bf92959ef5`
- `OTUArtenlisteGesamt.csv`: `517999cb19112a261e73aed8c2e42282`
- `otus_new.fasta`: `307730de9089bef66855e13162cbceed`

These file names/MD5s are independently visible in the original Zenodo v1 publication page, NOT newly computed original file digests. Do not request `BETAFOR_information.csv` data rows, `calibration_points.csv`, original `com_singletons.csv` OTU table, taxa, phylogeny, original sequence or fitting code during this metadata stage. No original site IDs, treatment values, response fields, sample counts, species names or p-values. If exact DOI/record/license/digest count drifts or GET fails, return `SOURCE_METADATA_HOLD` and **zero** biological evidence; do not try alternate hosts/URLs or claim a null ecology effect.

The executable gate returns only a non-identifying JSON manifest with verified **six name/digest tokens**, publisher-reported byte sizes, license and an explicit zero-response-read flag. A test fixture must prove checksum/version mismatch STOP before the original record GET runs.

## Scientific admission AFTER a metadata PASS, not authorized by this stage

1. **Author source-method/ID stage (separate precommit):** original `ForestSite × Region × Patch × Treatment × SamplingPeriod × Year` exact key and true zero/attrition/effort denominator, with treatment assignments fixed *independently of OTU outcomes*. Avoid using 594 repeated sample records as 594 ecological regions.
2. **Outcome definition (another separate precommit):** choose one *comparable* insect OTU-composition/diversity and effort/coverage standardization operator *before* reading `com_singletons`; never select by favorable guild, q, year, patch or model. Same method/site unit in training and heldout.
3. **Incremental out-of-region test:** compare climate+site original environmental reference versus treatment identity (gap configuration × original deadwood category) under leave-**region**-out prediction. Predefine exactly one primary loss metric, source region equal weighting, null/randomization and STOP for weak blocks before outcome.
4. **Causal and novelty boundary:** treatment assignment can support within-experiment causal contrasts, subject to author block design, but geographic *predictive transfer* is observational across only six German regions. Original authors' gap/deadwood diversity findings cannot be presented as new discoveries. One Germany-only experiment cannot demonstrate a pan-biome law.

**End-state of this pre-intake:** admission of ORIGINAL PUBLISHER METADATA ONLY; biological model fits = 0; prior PREDICTS/Finnish/Carpathian/Swedish/BALA/mammal source seals unchanged, PR #469 Draft/unmerged. No eBird, no TinyFish.

Sources:
- Original paper: https://doi.org/10.1111/1365-2664.70086
- Original author data v1: https://doi.org/10.5281/zenodo.15371332
- Original author code: https://doi.org/10.5281/zenodo.15165462
- Upstream ecological synthesis: [FOREST_MACRO_20261119_GENERALITY_AND_NOVELTY_SOURCEFREE_SYNTHESIS.md](FOREST_MACRO_20261119_GENERALITY_AND_NOVELTY_SOURCEFREE_SYNTHESIS.md)
