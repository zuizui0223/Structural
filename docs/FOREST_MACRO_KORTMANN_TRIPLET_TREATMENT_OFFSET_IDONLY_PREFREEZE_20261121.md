# Kortmann2026 original source: triplet × treatment × plot × effort ID-only frame

Frozen 2026-11-21 BEFORE any opening of original source field values in the newly verified 702-row RData.

## Original source and evidence downgrade (unchanged)

- Original publisher Zenodo version `17775805` CC BY-SA4 `data_code.zip`, exact MD5 `41f9a8428d80e833e4785be198a5c886`, file `data_public/diversity_satellite.rda` original uncompressed **67,238 bytes**, source member SHA256 **`8b3f47258b4d9c8f6fa0f7fac0d820ecccb860adadaa9c3c311f21fa28e3da3a`** from first original structural inspection.
- Exact one-shot first RDA STRUCTURE ONLY [#44763897159](https://github.com/zuizui0223/Structural/actions/runs/44763897159) already established **one data.frame, 702 rows × 50 columns** with exact published-safe method field names `triplet, plot, treatment, offset`. No original data values were exported or ecology fitted.
- **Important** RData deserialization of a response-bearing table occurred in #44763897159, so the cohort is no longer `response_unopened_pristine`. This ID-only followup is **source-structure-exposed and exploratory**, and cannot reset the evidence classification.
- Published methods: **40 physical triplets × 3 forest patches × 6 nominal Malaise sampling periods = 720 planned opportunities**, **702** collected samples after malfunctions. These are author-reported expectations pending actual original ID counts. Original 21,218 OTUs and alpha effects from paper are prior art.

## EXACT source columns now authorized

Re-download only original hash-pinned ZIP and extract only the same original `diversity_satellite.rda`. In isolated base R load, access **ONLY** original fields `triplet, plot, treatment, offset` from the single source data.frame; do NOT access any other 46 columns or original `otu_matrix.rda`, phylogeny or Excel. The RData deserialization necessarily materializes original response-bearing object in memory (report this truthfully).

Read these four source method fields strictly to compute anonymous **counts/consistency**, NOT publish field values:
1. Require original rows exactly **702**, field names exact and uniquely matched case-insensitively, `triplet, plot, treatment` all nonmissing/nonblank per sampled record.
2. Report number of unique `triplet` keys (required **40**), distinct `triplet×plot` combinations (required **120**), and distinct source `treatment` codes (required **3**); do **not** export the actual codes or site IDs.
3. Require exactly 3 distinct source treatment categories and exactly three physically unique `triplet×plot` combinations per triplet. Require exactly one `plot` value in each `triplet×treatment` group, and all three original treatment categories present in every triplet (120 pair groups). If the author `plot` keys are reused, group by `triplet×plot` rather than assuming global uniqueness.
4. For each source `triplet×plot`, count **rows** (proxy for observed sampled occasions) and report ONLY anonymized minimum, maximum, number with 6, number with fewer than 6, and total `sum(6 - observed_rows)`. Require all plot row counts in **1..6**, sum of deficits exactly **18**, 702 total. **Do not infer which collection period was missing**, turn missing sampling into species zero, impute sampled absences or claim all 702 row IDs unique in time.
5. Check `offset` is a numeric finite real field in **all 702 original source rows**; report only pass/fail and missing/nonfinite count, **not any offset values, means or inferred physical units**. The source authors used offset in 19 of 27 GAM expressions; a finite `offset` column does not alone prove actual trap-days or equal detection.
6. Publish only these anonymous count/boolean diagnostics and a status `SOURCE_ORIGINAL_TRIPLET_3STATE_702_FRAME_COUNT_READY_NO_OTU` if all fixed conditions pass, otherwise a named `SOURCE_ORIGINAL_METHOD_FRAME_HOLD`. No source site, plot, state/treatment label, sampling date, trap effort numeric value, coordinates, original response columns or OTU data may leave the ephemeral job.

## Scientific meaning / next boundary

A PASS is *physical sampling frame support*, **not** confirmation of an independent biome, actual site coordinates, sampling-period overlap, species response, causal salvage-logging mechanism or a published effect beyond prior art. Original 40 triplets all Bavaria/Germany; site-versus-BETA-FOR99 geographic overlap still unknown.

Only after this method ID-only check may a separately frozen original sample-date/source effort and `otu_matrix.rda` matching protocol be considered. The candidate exploratory ecological effect is per-triplet `D_i=beta_sim(U,cleared)-beta_sim(U,disturbed-retained)` using a predeclared coverage-aware operator; it is **not** a replication of BETA-FOR's `G-W` canopy pattern vs wood treatment effect. Do not use original biology to choose a favorable taxonomy, forest type, coverage threshold or sign.

Original BETA-FOR99/234, PREDICTS, BALA, Finnish, Slovak, Swedish, NEON and island outcomes remain frozen; no PR merge, no eBird, no TinyFish.
