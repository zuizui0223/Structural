# Kortmann 2026: ORIGINAL author R scripts and data-role filenames ONLY (pre-response prefreeze 2026-11-20)

## Input locked independently before this first script-member read

Previously, publisher-canonical Zenodo `17775805` was source-only verified [#44757952953](https://github.com/zuizui0223/Structural/actions/runs/44757952953): exact published `data_code.zip` **46,205,253 bytes**, MD5 **41f9a8428d80e833e4785be198a5c886**, public CC-BY-SA 4.0, publisher single-file manifest SHA256 **278910cf7c284eeb55a11fc45f4fa8b7af77530c73b059ac606410d3e5224dd2**. Then one source-only ZIP central-directory [#44759138223](https://github.com/zuizui0223/Structural/actions/runs/44759138223) verified original ZIP bytes, **8 ZIP directory entries / 6 actual files**: **2 `.R` scripts, 3 `.rda` binary data objects, 1 `.xlsx` Excel**. No source member was opened during either gate. Exact two R source members and directory sizes:
- `scripts_public/iNEXT3D.R` — **825** advertised original member bytes
- `scripts_public/models.R` — **16,103** advertised original member bytes
- Exact original published workbook `data_public/FT_Retz_RV-UniWue-2022-003_COI_w-1-tons_results_AIMIDs.xlsx` — **73,378,007** advertised bytes, **still forbidden for content read**.

The publisher paper contains **40 Bavaria study sites**, each an undisturbed–naturally disturbed–salvage-logged triplet (17 spruce, 13 beech, 5 pine, 5 oak), 120 nominal patches, 702 collected Malaise samples vs 720 nominal patch×round opportunities, 21,218 taxonomic OTUs in the authors' analysis. These counts are *published facts*, not verified rows or ecology inferred from the current ZIP inventory.

## One new independent source-only method role audit now authorized

- Reverify EXACT original Zenodo `17775805` publisher record, `data_code.zip` file size/MD5 and six-file original archive central directory; use **one** publisher-supplied same-host exact archive GET, no alternate host, no redirect follow.
- **Only** access original `scripts_public/iNEXT3D.R` and `scripts_public/models.R` text members (after checking their directory reported byte lengths). Do NOT execute them. Read them solely to fingerprint SHA256, verify expected length, and count mentions of a frozen role vocabulary: `site/plot/patch/triplet, forest/tree, disturb/clear/log, sample/trap/effort/time, OTU, iNEXT/coverage, load/read, beta/turnover`.
- Separately, from ZIP CENTRAL DIRECTORY ONLY, output exact ASCII-safe `.rda/.RData/.rds` member filenames and advertised uncompressed member lengths, without reading or decompressing ANY binary data object. Do not print source R code or any content-derived file paths, raw sample IDs, taxon labels, site names, ecological outcome variables, stored effects, coefficients, numerical matrix fields or original specimen values.
- The original `.xlsx` workbook, all `.rda` files and their internal ZIP members remain **completely UNOPENED**. Code lexical mention counts are METHOD HINTS, not proof of true source field names, observation-coverage semantics, independent forest count or taxon phylogeny.
- A successful audit yields `SOURCE_ORIGINAL_AUTHOR_CODE_ROLE_HINTS_ONLY_NO_BIOLOGY`, not 40-site source qualification or a new ecological model. Any missing/changed source file, byte hash, unexpected script encoding, unsafe ZIP filename, >500 entry ZIP, absent declared role vocabulary or source transport error produces named SOURCE STOP. Do not rescue by changing downloaded ZIP name, script member target, biological sample year or OTU filter.

## Later scientific test boundary (not authorized by this audit)

Once original source-member roles are known, separately precommit an **original physical 40-triplet×state×sampling-round identity-only** crosswalk, retaining all 720 nominal exposure opportunities and distinguishing observed 702 from documented missing exposure (not population zero). Check code's original sample-period semantics and whether 2022 coverage / underlying OTU tables actually share IDs; confirm source differs physically from the controlled 11-site BETA-FOR programme. **Do not test original biodiversity** before this.

A later genuinely new possible endpoint: within each source triplet `D_site = beta_sim(undisturbed,cleared) - beta_sim(undisturbed,disturbed_unmanaged)` with **coverage-harmonized** recorded taxon detection, one effect per original site, forest-type/space-block uncertainty. This is *not* BETA-FOR's factorial A/D-vs-wood `G-W` estimand and cannot be pooled as its replication. Source coverage and site geography must be adequate before this endpoint can be frozen as confirmatory; there may be no globally independent region support.

Old one-pass BETA-FOR99, no-file BETA-FOR234, PREDICTS, BALA and all prior holds untouched. Draft PR #469, no main merge. eBird/TinyFish not used.
