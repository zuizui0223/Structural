# BETA-FOR 2025 original `BETAFOR_information.csv`: first-header-only method gate (new pre-response freeze, 2026-11-19)

## Fixed scientific question

Can the already-published German BETA-FOR canopy-opening × deadwood intervention dataset support a **genuinely held-out region** prediction of insect community structure **without confusing 594 repeated trap-period samples with independent forests and without re-reporting published treatment effects as a new discovery**?

This protocol is strictly a **method-source intake**, *not* permission to open community observations or fit biodiversity responses.

## Correct source population hierarchy (from the 2025 published original METHODS, not a newly verified dataset count)

Original primary article Rothacher et al. DOI [10.1111/1365-2664.70086](https://doi.org/10.1111/1365-2664.70086), section 2.1–2.2:
- **6 German geographic regions; 11 forest sites; 9 source experimental patches per forest** in *the published Malaise-insect study* = **99 treated-or-control 50×50-m patches** (1 untreated + 8 assigned manipulation patches per forest).
- Each patch has **6 fortnightly Malaise trap collection opportunities** between May and July, yielding **594 source-author reported seasonal samples** (99 × 6). They are NOT 594 forests, 594 independent replicate treatments, or 99 independent regions.
- The broader BETA-FOR parent experiment also has paired treatment/control districts and **234 experimental patches** across 11 forests (some sites have 15 per district), documented in other BETA-FOR papers. **This insect paper specifically selects 9 patches per forest**, not all 234. Do not silently join the larger parental denominator to this sample.
- Insect study site-years are **2022** in Bavarian Forest, Würzburg University Forest and Passau; **2023** in Saarland, Lübeck, Hunsrück. The study-region and sample-year factors are nested/confounded; do **not** call year a clean independent intervention effect.
- Original authors' taxonomic/phylogenetic insect richness and gap+deadwood increase up to 47% after sample-coverage standardization are already **PRIOR ART**. Source authors report 22,889 metabarcoding OTUs from 362 insect families. No organism effect or sample-level richness is read in this new gate.

## Original publisher and exact static admission contract

- Original **data** Zenodo 10.5281/zenodo.15371332, v1 May 9 2025. Exact official public record endpoint `https://zenodo.org/api/records/15371332`, same six original filename/MD5 fingerprints as the preceding [publisher-only pre-intake freeze](FOREST_MACRO_BETAFOR11_2025_ORIGINAL_METHOD_PREINTAKE_PRESPEC_20261119.md).
- Original **code** Zenodo 10.5281/zenodo.15165462 is **NOT accessed** in this gate; separate source identity only, useful in later methods if original checksum/reader semantics independently admitted.
- **First original member authorized for exact-byte SHA/MD5 and first header ONLY**: `BETAFOR_information.csv` published MD5 `873f5d424904d1eed00e079b945dd5dc`, approximate publisher UI size 47.0 kB. Actual size must be verified as integer from original source API.
- The allowed link must be **provided within the exact original official publisher record** and have a validated `zenodo.org` HTTPS file endpoint; no guessed alternate original host, external redirect, URL-parameter credentials, or sibling data downloads.
- Fail closed on missing record, wrong DOI/version/CC-BY-SA license, missing/changed any of the six original file checksums, wrong `BETAFOR_information.csv` digest or non-UTF8 first header.

## Permitted new observations and forbidden ones

1. Inspect the verified original `BETAFOR_information.csv` **first physical header line only** and output a non-identifying count of columns, source delimiter class and names that EXACTLY equal the **predeclared generic nonresponse field whitelist**: `site, forest, region, patch, plot, treatment, year, period, date, duration, effort, trap` and a few explicit original English spelling variants. The code must not print unknown labels, free-form strings, original source data field values, species/OTU names, site/patch IDs, coordinates, response scores or model coefficients.
2. Obtain source file bytes solely to verify the publisher MD5 and isolate the **first header**; do not parse **any** data row or examine `com_singletons.csv`, `OTUArtenlisteGesamt.csv`, `calibration_points.csv`, FASTA, .tre, or code data. Every original non-header byte is opaque after verification; no row count from source member is asserted.
3. A header with no plausible original ID, treatment, date or field effort terminology is **SOURCE_METHOD_HEADER_HOLD**. It does not authorize ID parsing or outcome opening. Syntactic candidates alone do **not** establish plot×year×treatment×period linkage.
4. All older PREDICTS/Finland/Germany/Slovakia/Sweden/NEON/BALA/Island heldout source outcomes are immutable. No field predictor model or new response effect from this header check.
5. Next eligible future step requires a separate, fixed **ID/treatment/effort-only row authorization**, only if original methods/codebook and column roles match this source version. Do not join repeated sampling periods or impute observed zeros until it is independently established which rows denote trap opportunity and which are detections.

## Explicit future biological-test sketch (NOT frozen as a scored endpoint)

Before original OTU data opening:
- fix a source author original `Region > ForestSite > Patch > SamplingPeriod` hierarchy, complete opportunities and ineligible/attrition treatment, and one stable OTU diversity/composition target with coverage standardization (original paper documents 0.98 coverage; future primary metric must be chosen once without outcome peeking);
- have **leave-one-region-out** transfer with **6** geographically distinct held-out regions as the denominator, and suitable within-year/region nuisance adjustment so 2022 vs 2023 cannot be mistaken for spatial transfer; no independent unseen forest biome (only German largely beech forests);
- compare a baseline of sampling season/effort/source forest context with the prespecified original gap × wood-treatment representation, versus an explicit simpler gap-only comparator, then separate predictive gain from previously published treatment-effect discovery;
- if source method does not permit stable out-of-region treatment/coverage prediction, make this a scientific STOP rather than tune a favorable model after looking at OTU outcomes.

This new source-method prefreeze is **not** a grant of biological data access, and its existence does not imply that original Zenodo GET or CI has succeeded. PR #469 remains Draft; no `main` merge.
