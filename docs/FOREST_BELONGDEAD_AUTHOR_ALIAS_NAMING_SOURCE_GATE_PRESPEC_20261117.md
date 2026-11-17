# BELongDead author alias/naming/effort documentation gate — before opening biology (2026-11-17)

## Scientific reason and frozen prior evidence

The original BExIS 31123 BELongDead beetle source has 30 physical plots, 379 logs and 13 offered host-tree categories. Its supposed complete-log companion 31124 has **15 unmatched six-field TrapID-containing method tuples**, despite matching all 379 logs and all 15 parent log×host×year tuples. This is an original method-key mismatch, not a beetle result. Site-level source deadwood BExIS24546 (2012) matches 30/30 physical plots but combines m³ and m³/ha in distinct measurement strata; no mixing is permitted. Neither source establishes the deployed-trap / zero-capture denominator. All existing PREDICTS, Finnish, German Chiu/Piccini, NEON, BALA and GEB endpoints stay sealed.

The original Biodiversity Exploratories Arthropods project catalogue, not an inferred or fuzzy join, lists previously unused **author-owned BELongDead naming/method datasets**:
- **BExIS13930, published tag 3** — BELongDead 06, *Alias numbers* (2013).
- **BExIS16846, published tag 1** — BELongDead 12, *Changes in log naming* (2013).
- **BExIS16427, published tag 2** — BELongDead 07, *Subplot naming* (2013).
- **BExIS16390, published tag 1** — BELongDead 04, *Instrumentation (2009/2010)* (2017).

Author catalogue: https://www.biodiversity-exploratories.de/en/projects/arthropods-i-land-use-above-ground-arthropod-diversity-and-arthropod-affected-processes/

**Do not interpret "Alias numbers" or "Changes in log naming" as proof of a TrapID crosswalk.** Those may concern logs or subplots rather than trap occasions. The 2009/2010 instrumentation record may not cover 2010–2017 deployment.

## Exact source-only admission test (predeclared before any new response access)

1. Source identities and publisher tags are *exactly* the four listed above. Query only documented public original BExIS paths `/api/dataset/{id}`, `/api/metadata/{id}?tag={tag}.0` and, **only after recognizable open license**, `/api/DataStatistic/{id}`. The variable-statistics endpoint may reflect latest fields; never claim the dictionary is byte-identical to the tagged original until a separate verified tagged source inspection. Use one ordinary read-only GET per endpoint, no redirect, alternate mirror, auth workaround or unbounded retry.
2. Metadata and dictionary are permitted; original tabular source **rows are not**. Inspect only source rights/schema attributes `VariableName, VariableDescription, DataTypeName, Unit`. The statistical endpoint may carry `uniqueValues`, min/max and counts: **never export, print, derive effects from, or retain them in output**. Do not GET any `/api/data/{id}` row file in this stage.
3. Return per-ID publisher access/rights/tag status, response-byte SHA256, count of dictionary variables, and **only predeclared lexical family counts** for plot/log/alias/trap/time/effort naming. No raw original field names, author specimen/site/trap/tree IDs, original metadata free text, original codes, species labels, numeric wood measurements, original species/trait/capture rows or regression coefficients in any artifact/log.
4. An explicit **published author crosswalk with key definitions** is required to reconcile any of 15 original 31124 method tuples; neither field-name likeness, filename, row order, identity-like strings nor fuzzy matching can authorize remapping. A documented trap deployment/zero-capture opportunity frame is separately required before incidence or effort-normalized biological predictions. A published alias record may help physical **log** identity without helping **TrapID**.
5. If metadata/tag/rights unavailable: `SOURCE_ACCESS_OR_RIGHTS_STOP`. If metadata exists but no adequate method keys or tag alignment: `SOURCE_DICTIONARY_ONLY_HOLD`. If candidate fields are found: `SOURCE_FIELD_CANDIDATES_ONLY`. **No outcome read or effect estimation under any status.** Any future join validation needs a distinct, prospectively committed, original-author-method-only protocol.

This is a genuinely new source documentation target (not a new ecological hypothesis or confirmatory replicate), following the last six-plot host-identity positive. It does not reopen the sealed historical Chiu, Finnish, Piccini, Norwegian, mammal, BALA or GEB outcomes. No eBird, TinyFish, author contact, PR merge or main update.

### Required failure/STOP behavior

A source HTTP 401/403/404, public license absent, oversized/non-JSON response, unknown publisher rights or ambiguous lexical header count is a source **HOLD**, not a negative or positive arthropod result. The public catalogue version tag is not the BExIS internal database version. Keep individual method labels and observations in the publisher/runner context, never in the summary artifact.
