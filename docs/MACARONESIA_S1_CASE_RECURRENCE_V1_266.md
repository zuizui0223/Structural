# Macaronesia: confirmed island-loss cases and within-taxon recurrence

Verified 2026-10-20. This is a retrospective reanalysis of the published Table S1, not a newly collected independent ecological dataset.

## Completed execution

The previous v1.265 source-access failure was a network timeout, not a rejected ecological hypothesis. Re-running the same job succeeded without changing its biological filters. The 332,776-byte original CSIC workbook matched SHA256 `767f9ea095660d77babb8eb74b2eb714e8cdc38cb0c6861051416a7c0039b0e1`.

Source: Digital.CSIC DOI 10.20350/digitalCSIC/17024; handle http://hdl.handle.net/10261/377677. Original article: Orihuela-Rivero et al. (2025), Global Change Biology, DOI 10.1111/gcb.70072. Its published extinction census and trait results are prior art, not new Structural discoveries.

## 1. Define the cases before counting

Table S1 contains 168 records: 79 Well-supported, 52 Doubtful, 17 Taxonomic problems and 20 Pre-Linnean. The 79 well-supported cases comprise 62 island-level extirpations, 8 archipelago-level extirpations, 8 globally extinct records and 1 extinct-in-the-wild record. Spatial-scale distinctions must not be collapsed.

The strict island-level subset contains **62 distinct taxon × island cases, 48 literal-name taxa, 18 named islands and four archipelagos**. No exact duplicate taxon/archipelago/island case is present. Thirty-four taxa have a recorded qualifying loss on one island; fourteen have losses on exactly two islands. These fourteen taxa account for 28/62 cases (45.16%). None of the 48 taxa has qualifying island-level loss records in more than one archipelago.

## 2. Same number of cases, different recurrence across taxa

| Archipelago | Confirmed taxon-island cases | Affected taxa | Named islands | Taxa with losses on two islands |
|---|---:|---:|---:|---:|
| Azores | 24 | 20 | 7 | 4 |
| Canary Islands | 24 | 16 | 4 | 8 |
| Cabo Verde | 13 | 11 | 6 | 2 |
| Madeira | 1 | 1 | 1 | 0 |

Azores and Canary Islands each have 24 qualifying cases. Yet only 4/20 affected taxa in the Azores recur across two islands, compared with 8/16 in the Canary Islands. **Equal loss-case counts can conceal different concentration of losses in the same taxa.** These proportions are conditional on having at least one qualifying recorded loss. They are not extinction probabilities, independent replicate tests, or evidence that Canary populations have a higher intrinsic extinction risk.

The contrast motivates a focused question: are within-archipelago losses spread across different taxa, or concentrated among several island populations of the same taxon, after accounting for each taxon's historical number of occupied islands? Historical distribution breadth alone can change recurrence opportunities. Observation effort, taxonomic treatment and shared human pressures are additional competing explanations.

## 3. Dates describe records, not extinction timing

For all fourteen two-island taxa, both last-observation years are parseable. Absolute last-record-year gaps are 0, 0, 0, 0, 0, 5, 13, 23, 27, 32, 38, 53, 120 and 168 years (median 18 years). Five pairs share the same last-record year, six are at most ten years apart, and three exceed fifty years.

These are differences between **last recorded observations**, not directly observed extinction dates. Equal recorded years do not establish synchronous extinction; different years do not estimate the speed of an extinction cascade. Repeated records can share a historical source or observation schedule.

## 4. Taxon identity and weighting

The source has 127 distinct literal name strings, whereas the article reports 126 taxa. Removing trailing numeric annotations alters six strings but merges none; both counts remain 127. Every primary 62-case/48-taxon recurrence result is unchanged under that sensitivity. The overall one-taxon discrepancy remains unresolved; do not force 126 by dropping a record or pretending annotation cleanup is synonym validation.

Event-weighted woodiness is 43/62 cases, while taxon-weighted woodiness is 31/48 taxa. Any biological trait model must use the appropriate unit and reference flora, not treat repeated loss cases as independent species. The S1 case list by itself cannot estimate trait-specific extinction risk.

## 5. What is still missing

S1 records losses but does not provide the full set of historically occupied taxon-island combinations that persisted. Without that at-risk denominator, no source-configuration extinction-risk model or demographic rescue conclusion has been fitted. Current survivors on other islands also cannot automatically be treated as pre-loss sources.

The next scientifically necessary join is historically occupied species-island combinations with both loss and persistence, at matched taxonomic resolution and credible dates. The current result is a useful case-distribution description, not a confirmatory mechanism test. S2, S3 and S4 values remain unopened in this analysis; the previous mammal, BioTIME and RLS protected responses remain unchanged. eBird is not used. GEB scientific HOLD and zero new confirmatory admissions are retained.

## Reproducibility

- Strict S1 run: https://github.com/zuizui0223/Structural/actions/runs/39239022711 ; successful rerun artifact 12240427699, SHA256 `e97f74fa33de1e11c91ffd5372d50098e91c615b6678e3c88f944fcda615e74d`.
- Recurrence and full-suite run: https://github.com/zuizui0223/Structural/actions/runs/39370340660 ; code commit `94a5ffd97523812928a9f0cad9f582c14f1a74ce`.
- Recurrence artifact 12241222259, SHA256 `5e85058f154d3c28a9f63e7779c3332ef322b801221914b5063f3f0671c06cf5`.
- Full repository suite: **1,553 passed, 13 skipped, zero failures/errors**. One warning came from an existing deliberately malformed ZIP provenance test.
- Source-free new tests were observed failing before implementation and then passing locally; the remote workflow also tested the existing S1 parser and the complete repository suite.
- Persisted aggregate result: `development/macaronesia_S1_recurrence_result_v1_266.json`.
- No individual species names or event rows were exported.
