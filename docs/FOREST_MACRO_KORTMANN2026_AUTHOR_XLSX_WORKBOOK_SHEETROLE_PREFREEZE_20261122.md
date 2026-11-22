# Frozen 2026-11-22: Kortmann 17775805 original workbook sheet-role index ONLY

## Scientific status (binding)
The frozen original Kortmann 2026 trial has 40 triplets, only 39 with a full 3-state field frame (117 patches, 690 sampled records). A single original OTU schema read found 1 20,898×702 dataframe with a 702-column labelled sample axis but ZERO eligible prespecified method-record sample IDs; `SOURCE_OTU_SAMPLE_LINK_HOLD`. No OTU numeric values or new beta effects were computed. The OTU RData was deserialized for metadata; pristine original-response claim is no longer permissible.

[Original source receipt](https://github.com/zuizui0223/Structural/blob/analysis/forest-macro-plot-environment/outcome/kortmann39_otu_identity_20261121/receipt.json), [method issue #471](https://github.com/zuizui0223/Structural/issues/471).

Two author R code members from the exact original 17775805 source ZIP were hash-verified and statically scanned. The 825-byte `iNEXT3D.R` references the original `otu_matrix.rda` and `phylogenetic_tree.rda`, but not `diversity_satellite.rda`; the 16,103-byte `models.R` references `diversity_satellite.rda` but not the OTU matrix. Both report zero direct `merge`, `left_join`, `inner_join`, `full_join` or `group_by` function calls. These findings **do not prove** that the authors lack a separate sample codebook or use no nonstandard join, but there is no documented explicit sample crosswalk in the audited source code. Original source method code audit [#44761846381](https://github.com/zuizui0223/Structural/actions/runs/44761846381), artifact #14640079717 SHA256 `9eb9427f8218aa9a928617195c5f9205fc950a767ea25ae03486a037ee9e8a7c`.

## Why inspect original workbook container

The fixed same-author 17775805 original `data_code.zip` (MD5 `41f9a8428d80e833e4785be198a5c886`, 46,205,253 bytes) also contains one large Excel workbook called `data_public/FT_Retz_RV-UniWue-2022-003_COI_w-1-tons_results_AIMIDs.xlsx` with outer-ZIP-advertised uncompressed member length **73,378,007** bytes. Its **worksheet and cell contents have not been inspected**. This stage asks ONLY whether the workbook's structural sheet titles indicate an original sample/collection metadata ledger, without reading or inferring taxon, OTU or site values.

## Exactly ONE permitted source-method operation

On isolated branch `audit/forest-kortmann39-ledger-synthetic-20261122`, fetch exact official Zenodo record `17775805` and the same original ZIP through its publisher-supplied link, verify the already-frozen archive size and MD5, confirm original outer ZIP directory, extract and validate **only the one named XLSX member** at its frozen 73,378,007-byte uncompressed length (the XLSX member's complete opaque bytes are obtained in memory, **NOT a pristine-unopened biological source status**).

Open only the XLSX **ZIP central directory** and the bounded `xl/workbook.xml` document (max 512 KiB). Read sheet-name attributes exclusively; never `xl/worksheets/sheet*.xml`, `sharedStrings.xml`, `styles.xml`, values, formulae, comments, images, tables, external links, defined names or any source taxon, site or sample IDs.

Output exclusively total worksheet count and counts of sheets whose *names* contain precommitted broad token groups: `sample/collection/trap/bottle/event/field/metadata/method` vs `otu/taxon/species/ident/aim/match`. Do not export source sheet titles. If method-like title exists: `SOURCE_AUTHOR_WORKBOOK_SHEETROLE_CANDIDATE_ONLY_NO_CELL_READ`; otherwise `SOURCE_AUTHOR_WORKBOOK_SHEETROLE_NOT_EVIDENCED_NO_CELL_READ`. An absent title is **NOT** proof no ledger exists inside the workbook. Any mismatch, XML issue, unexpectedly large/inaccessible source is `SOURCE_WORKBOOK_SHEETROLE_STOP_*` and not a biological null.

Synthetic workbook tests must verify that sensitive hidden sample strings and biological values are absent from the receipt and only workbook XML is accessed. No original OTU numeric values may be read, no RData original member deserialized, no model fitted. Do not reopen any previously sealed BETA-FOR99, Finland, Slovakia, Swedish, PREDICTS, BALA, NEON or island response scorer. No eBird/TinyFish. Main PR #469 remains draft and unmerged.

The inspection can only narrow **where to ask for the missing author ledger**, not justify a row-order join. Original `SOURCE_OTU_SAMPLE_LINK_HOLD` remains until actual author sample-to-method ID, sample period, offset and treatment-code metadata are source authenticated.
