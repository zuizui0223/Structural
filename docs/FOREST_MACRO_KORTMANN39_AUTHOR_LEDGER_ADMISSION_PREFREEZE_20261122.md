# Kortmann 2026: response-free author ledger admission and independent-key validation (2026-11-22)

## Existing source HOLD is binding

The single previously frozen [original OTU schema audit](FOREST_MACRO_KORTMANN39_OTU_IDENTITY_RESULT_20261121.md) completed with **`SOURCE_OTU_SAMPLE_LINK_HOLD`**. The verified source methods have **40 triplets / 119 observed patches / 702 collection rows**. A separate source-informed, exploratory population contains exactly **39 complete triplets, 117 observed patches, 690 collection records**, balanced at **230 collection records per original three-state code**; 12 rounds are missing within these 39 triplets. The other triplet has only two observed patches, 12 records total. The `otu_matrix.rda` has one **20,898 × 702** original dataframe and a named 702-column sample axis. Predeclared legitimate method sample-ID columns and data-frame rownames produced **zero** candidate keys. The original OTU object was DESERIALIZED for a names-and-shape-only audit; no numeric organism effect has been scored.

**Do not infer that the 702 method rows match the 702 OTU columns by position.** The 20,898 row count is not an independently certified species/OTU denominator.

## One external response-free source required

[GitHub Issue #471](https://github.com/zuizui0223/Structural/issues/471) states the author-ledger dependency. Author source should have an explicit legitimate **per-bottle** identifier join between `otu_matrix.rda` column names and individual observed `diversity_satellite.rda` collection records, original triplet and patch/treatment labels, six potential round indices, collection-window start/end, interruption/effort semantics and exact `offset` units/transform. Author-defined treatment mappings must be supplied, not inferred from figure labels.

This document defines an **offline intake checker** for a future author-supplied response-free ledger. Passing it verifies ONLY self-consistency; it **cannot** establish actual authoritative crosswalk with the frozen original source unless a later, separately frozen source-to-source checker confirms the original identifiers and provenance.

### Input schema (author source, not a claim these are original CSV columns)

Use a plain CSV with exactly these ten field headers (in this order):

`triplet_id,plot_id,treatment_code,round_index,collection_start,collection_end,trap_status,otu_column_id,method_record_id,offset`

- `triplet_id`, `plot_id`, `treatment_code`: opaque **author** IDs from the source metadata, not guesses; one stable treatment per triplet/plot
- `round_index`: original author-confirmed collection round 1..6, never reconstructed from data row order
- `collection_start`, `collection_end`: ISO dates, required for observed rounds and allowed blank for non-collected opportunities
- `trap_status`: `observed` or `missing`; missing means **no bottle collected**, not zero insects
- `otu_column_id`: exact original published OTU column name, required for observed, blank for missing
- `method_record_id`: **author-attested unique original record identifier or a separately documented author-generated composite key**. The current source has no confirmed field for this; a 1..702 positional ordinal is forbidden. Required for observed, blank for missing
- `offset`: original stored method sampling-effort value, required finite for observed, blank for missing. **No physical unit is inferred from the numeric value.**
- No organism response, abundance, OTU/taxon columns, coordinates, names of persons, or location-sensitive other data permitted.

Two acceptable author-ledger representations:
1. **720-row complete-opportunity ledger**, 40 triplets×3 planned plots×6 rounds, including all 18 missing opportunities. Must have 702 observed, 18 missing, 119 observed patches, 39 triplets with 3 sampled states, one with only 2; 39 retained triplets have 690 observed rows, 117 sampled patches and 230 observed rows per treatment, with 12 missing rounds.
2. **702-row observed-only ledger**, every row an actual sampled bottle. Must have the same 40/119/39/690/230 observed facts and 107 observed patches with 6 rounds plus 12 with 5 rounds. **This representation cannot establish the missing-sample exposure frame**, so its admission is explicitly weaker and later biological calculations remain blocked.

Provide a separate small **JSON codebook** with exactly:
- `dataset_versioned_doi`: `10.5281/zenodo.17775805`
- `mapping_basis`: `author_provided_record_key` or `author_certified_composite_key`, never row order or auto-generated 1..702
- `treatment_code_to_role`: three source-code keys mapped bijectively to the semantic roles `undisturbed`, `disturbed_unmanaged`, `cleared_salvage`
- `offset_units_and_transform`: nonempty text author supplied explaining the model offset (NOT a source-verified fact from this checker)
- `sampling_time_definition`: nonempty author text explaining date conventions and interruptions.

Actual source identifiers and codebook text will not be printed in checker stdout/receipt. The codebook is NOT an independently authenticated original until source provenance can be verified.

## Fixed anonymous checker outputs, no biology

Check UTF8 CSV/JSON byte caps, exact known headers, no unlisted response columns, valid dates, unique physical site×plot×round entries, stable treatment/plot linkage, all allowed program source counts, independent full-period sample ID set uniqueness (reject default 1..702 values in any order), feasible 2022 collection dates and finite `offset` values for observed rows.

Return only **aggregate** triplet, sample and missing-opportunity counts, number of fully observed matched triplet-round groups and number with overlapping sampling windows; never original IDs, source treatment code values, dates, raw offset values, original sample labels, or OTU values. A structurally consistent ledger is **`AUTHOR_LEDGER_SHAPE_PASS_NOT_SOURCE_AUTHENTICATED`**. There is no route from this response-free format checker to a new ecology effect. Incomplete, changed or ambiguous source input returns a named `AUTHOR_LEDGER_SHAPE_HOLD` diagnostic, not an ecology null.

## Last pre-biology gates

After receiving a signed/attributed authoritative ledger: independently match its 702 `otu_column_id` values to the actual frozen OTU matrix column names; independently substantiate `method_record_id` to original 702 method observations **with a real author-documented identifier**, not row order. Match triplet/plot/treatment code semantics and seasonally comparable effort; prespecify how to handle 12 gaps. **Only then** may a new exploratory beta-simpson source effect be independently frozen and scored; no global cross-biome/causal inference from one Bavarian network.

Preserve old original 40-triplet gate HOLD, previous PREDICTS, BETA-FOR99 and 234, NEON, Finland, Slovakia, Sweden, BALA and GEB outcomes. No eBird/TinyFish, no raw source redistributions, PR #469 Draft and unmerged. The already attempted Gmail draft connection was not authorized; **no message sent**.
