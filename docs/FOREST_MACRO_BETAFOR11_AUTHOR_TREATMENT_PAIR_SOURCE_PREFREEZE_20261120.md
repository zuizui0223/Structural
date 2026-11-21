# BETA-FOR11 author-source treatment-pair and collection-chronology metadata-only test (2026-11-20)

## Exact frozen source context

- Source already verified: 11 original BETA-FOR forests / 6 geographic regions / 9 distinct patches each / 6 original sampling rows each = 594; original `BETAFOR_information.csv` 46,965 bytes, MD5 `873f5d424904d1eed00e079b945dd5dc`, original eight semicolon fields.
- Original `com_singletons.csv` full MD5 `81e2c1269bff49fafdf497f03f5922b2`, exactly 598 first-header fields, **594 exact original sample labels**; no OTU numeric values/rows parsed to date.
- Original author R code [09_indicatorspecies.R](https://zenodo.org/records/15165462/files/09_indicatorspecies.R?download=1) (MD5 `2c7888ab3733a2b651f7650604f12345`) parses **treatment from positions 5:6** of the patch/sample label, first treatment letter for `A` (open/aggregated canopy) vs other original `D` (closed/distributed) and second for wood type (including `W` or `C`). Original experimental papers describe **nine experimental treatments per forest**, an untreated `CC` control and `A/D` conditions for `W,L,S,B` resource configurations. This R method is PRIOR ART and does not itself show a new β-diversity effect.

## A single *method-only* first source-row test, before biological read

From the same publisher source ID/DOI/CC-BY-SA/six-MD5 record, re-open ONLY `BETAFOR_information.csv` (not the original OTU table). Require exactly the original authenticated 594 rows and 99 patch/sample keys. Compare original site- and patch-level treatment labels against this **predeclared set** `CC, AW, AL, AS, AB, DW, DL, DS, DB` (one patch each per forest; four A/D matched resource pairs `W,L,S,B` per forest). Verify the patch original characters 5:6 equal the treatment field under exact author R naming, without guessing alternate parsing.

Independently inspect original `firstday` and `lastday` numeric metadata fields ONLY (not the 279 `meanday` unknown-format values) for all 594 source rows: parse as finite floats, require firstday ≤ lastday for each row, and test whether each patch has six strictly increasing `firstday` values (chronological order). Report only overall counts and syntactic truth values—never actual source patch IDs, dates, XY, or treatment row strings. If dates cannot be ordered, **no early/late community analysis** may be authorized; grouped full-six sample composition remains a separate later endpoint. `X,Y` were not numerically parseable in any original method row; no plot distance or fine-scale spatial block inference is permitted.

Outcomes of this stage: `SOURCE_TREATMENT_4PAIR_METHOD_READY`, `SOURCE_TREATMENT_PAIRING_HOLD` or `SOURCE_TIME_CHRONOLOGY_HOLD`. All statuses are method qualifiers ONLY, not ecological null/positive effects. If one original published treatment code differs, stop without post hoc recoding or dropping a forest.

## Scientific target (later, unscored)

A potential new endpoint is whether **canopy arrangement vs deadwood type** drives more *between-patch* insect taxonomic composition differentiation in each source forest; this is not the original authors' treatment effect on α Hill diversity. One future comparison could contrast A/D patch pairs with the same resource code versus patches with the same canopy regime but different resource code, with forest as the unit, and six source regions for geographic uncertainty. Relative and phylogenetic treatment effects from original 2025 paper and 2026 BETA-FOR spider work are prior art; a genuinely new original-OTU observation and a preregistered response metric/detection correction remain necessary. No within-forest control–control β is estimable from only one CC patch/forest in the original 99-patch source; the 234-patch matched district programme is a *same-network* later source, not independent replication.

Zero organism response values authorized. No existing frozen ecological scorer reopens, PR #469 Draft/main untouched, no eBird/TinyFish.
