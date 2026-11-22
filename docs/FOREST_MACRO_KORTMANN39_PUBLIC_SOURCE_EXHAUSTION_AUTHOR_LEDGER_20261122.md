# Kortmann 2026 public source triage — source-method ID crosswalk still HOLD (2026-11-22)

## Verified current state and scope

Original Kortmann et al., *Biological Conservation* 313:111647 (2026), DOI 10.1016/j.biocon.2025.111647, archive version `10.5281/zenodo.17775805`. The original source identity gate ended `SOURCE_OTU_SAMPLE_LINK_HOLD`, not an ecological null, and remains immutable. The method-only source frame is 40 triplets / 119 sampled patches / 702 collection rows; fixed exploratory eligibility is 39 complete triplets / 117 patches / 690 observed rows, with twelve planned rounds not sampled within complete triplets and 12 records belonging to the excluded incomplete triplet. Source OTU RData is one 20,898-row × 702-column dataframe, 702 column labels but **zero** recognized exact method-record sample ID keys under the prespecified whitelist. The OTU dataframe was **deserialized for sample-axis schema**, no numerical OTU values or ecological effects were scored. [Frozen original result](FOREST_MACRO_KORTMANN39_OTU_IDENTITY_RESULT_20261121.md), [saved receipt](../outcome/kortmann39_otu_identity_20261121/receipt.json).

## Additional primary-source-method evidence, without organism scores

### 1. Previously hash-pinned original author R code
[Original exact author source-code audit CI #44761846381](https://github.com/zuizui0223/Structural/actions/runs/44761846381), artifact #14640079717 SHA256 `9eb9427f8218aa9a928617195c5f9205fc950a767ea25ae03486a037ee9e8a7c`, was downloaded **only as an existing aggregate receipt**. No source R scripts or original RData members were re-downloaded in this step.

- Original `scripts_public/iNEXT3D.R` (825 B, SHA256 `96c207052b28db90a280c427151c6b651745ce5dd7fe29d3c08fd6b3acdf9854`) statically references `otu_matrix.rda` and `phylogenetic_tree.rda`, but **not** `diversity_satellite.rda`.
- Original `scripts_public/models.R` (16,103 B, SHA256 `240d1b37150db6cf0b8b0288906dd0ba653fe92661a8a07e86a942f5af797b32`) statically references `diversity_satellite.rda`, but **not** `otu_matrix.rda`.
- Both original scripts have **zero** lexical function calls matching predeclared `merge`, `left_join`, `inner_join`, `full_join` and `group_by` categories. A separate frozen GAM-only code audit confirmed 27 GAM expressions, all 27 with `triplet`, 15 with `treatment`, 19 with `offset` [CI #44762827154](https://github.com/zuizui0223/Structural/actions/runs/44762827154). Those are author code cues, not a sample-row-level identity proof. The lexical audit does NOT prove the absence of any alternative join or external sample ledger.

### 2. NEW publisher-authenticated original XLSX structural inspection
A [separately frozen protocol in isolated audit branch](https://github.com/zuizui0223/Structural/blob/audit/forest-kortmann39-ledger-synthetic-20261122/docs/FOREST_MACRO_KORTMANN2026_AUTHOR_XLSX_WORKBOOK_SHEETROLE_PREFREEZE_20261122.md) and [actual original source Actions #45017060922](https://github.com/zuizui0223/Structural/actions/runs/45017060922) SUCCESS audited ONLY the `xl/workbook.xml` *sheet titles*, after exact publisher original ZIP MD5/size verification. Original `data_public/FT_Retz_RV-UniWue-2022-003_COI_w-1-tons_results_AIMIDs.xlsx` size **73,378,007 bytes**, new member SHA256 `8cf6cbfb16b483122899a96941cbb30d3ca66f552208afef9782637d6e1fe95d`.

- XLSX inner file count: **17**; worksheet count: **1**; sampling/metadata/method-like sheet title count: **0**; taxon/OTU/lab-like title count: **0**; other/unclassified sheet title count: **1**.
- Actual status `SOURCE_AUTHOR_WORKBOOK_SHEETROLE_NOT_EVIDENCED_NO_CELL_READ`. Anonymous artifact #14752496000 SHA256 `4fd0d55d0cee14d26a95a35037f7d1df0f72a66cf692acbdb230afc25895a3f1`.
- The original XLSX member was decompressed and its ZIP directory and **workbook XML only** parsed. **No worksheet XML, shared strings, species/taxon values, abundance cells or sample ID values were opened**. Absence of a method-like *sheet title* is NOT evidence that no method IDs exist within the sheet.

### 3. Another Kortmann software release is not interchangeable
The same author's [2025 Zenodo software release DOI 10.5281/zenodo.14747929](https://zenodo.org/records/14747929) concerns sample-coverage standardization and supplies `scripts.zip`. It is **a different code release/study** and has not been authenticated as a 2026 17775805 `otu_matrix.rda`↔`diversity_satellite.rda` sample-level mapping; do not use it as an assumed crosswalk.

## Decision and one actual dependency

We have **not** established the 702 original OTU column labels↔702 individual original method records mapping, source stored treatment-code meanings, sampling start/end and interruption/status nor offset units/transformation. Neither the 2026 original R code evidence nor the original XLSX sheet titles provide the required published-author mapping. Do **NOT** join by row order or inferred labels, impute 12 missed collections as biological zeros or score beta to search for support.

[Author metadata request Issue #471](https://github.com/zuizui0223/Structural/issues/471) and [strict synthetic-tested response-free ledger checker](https://github.com/zuizui0223/Structural/blob/analysis/forest-macro-plot-environment/analysis/forest_macro_global/kortmann39_author_sampling_ledger_gate.py) are already available. [Synthetic-only CI #45013738664](https://github.com/zuizui0223/Structural/actions/runs/45013738664) PASS (9 tests), **not** real source identity validation. A future response-free original author sampling ledger must independently authenticate exact original sample IDs against both the OTU column and method record, author triplet×patch×treatment, calendar/effort and offset before a separately frozen exploratory biological question may be scored.

PR #469 remains draft, no main merge. No correspondence was sent or Gmail draft saved because the connected email action required user permission. Other original PREDICTS/BETA-FOR99/BETA-FOR234/Finland/Slovakia/Sweden/NEON/BALA/GEB results and holds unchanged, no eBird/TinyFish.
