# BETA-FOR 2025 original eight-header field-role codebook: source-only diagnostic prefreeze (2026-11-20)

## Why this diagnostic is needed

The immutable new v2 source run [#44729512107](https://github.com/zuizui0223/Structural/actions/runs/44729512107) **successfully checked** the original BETA-FOR Zenodo version-specific record ID/DOI, published CC-BY-SA, six original MD5s, and the original **46,965-byte** `BETAFOR_information.csv` member MD5 `873f5d424904d1eed00e079b945dd5dc`. The previously generic allowlist recognized only **source header position 1 `patch` and position 6 `treatment`** of **eight semicolon-delimited fields**. No role for forest/region or time/effort was recognized. The v2 result is permanently `SOURCE_METHOD_HEADER_HOLD_INCOMPLETE_GENERIC_ROLE_SUPPORT`. Source table biological/numeric rows: **0 opened**. No ecological null or positive inferred.

**This new v3 is a DIAGNOSIS of the source column codebook, NOT a retest/rescue of any biological endpoint.** It does not revise the old v1/version STOP, the v2 header HOLD or any prior ecological result.

## Source-locked diagnostic (freeze before opening)

Using exactly the same source-pinned Zenodo v1 data record (record 15371332) with `metadata.version` missing/null and full six-file MD5 and original file-size protection, and exactly one re-GET of the author **information CSV only**, allow the following additional method-level extraction:

1. Verify original source full file MD5 and fixed first-header semicolon field count **exactly 8**. No OTU files or secondary author code/data GET. Parse only the first physical header line; every subsequent information-file byte remains opaque after file hash verification.
2. A source header name can be recorded ONLY if it passes a strict, predeclared **ASCII metadata field name** grammar `^[A-Za-z][A-Za-z0-9_ .-]{0,44}$` after stripping whitespace, no duplicate after casefold, no empty/quoted-formula header; reject otherwise without printing the content. These are **column names not source plot/sample/taxon data**.
3. Report a fixed eight-element position/name sequence **only if ALL eight original header fields pass** the grammar. Alongside it, output syntax-only role hints from tokens matching source-described `region/site/forest`, `plot/patch`, `treatment`, `year/date/period`, `trap/effort/duration`, and `sample ID`. This exploratory role dictionary is NOT accepted as an author-authorized join and must not be used to score a response.
4. Original paper (Rothacher et al. 2025 DOI 10.1111/1365-2664.70086) explicitly reports 11 forest sites/6 German regions/99 experimental patches and 6 collection periods (594 samples). Confirming field names cannot independently confirm those source **row counts**. Any region identifier inferred from string format is **not yet valid** without original source README/Rscript/author codebook.
5. Reject any first-header name that fails safe grammar. No data rows, source location values, raw patch tokens, collection dates, sample IDs, species/OTUs, abundance or derived biodiversity metrics are opened or exported. New biodiversity models = 0.
6. After this diagnostic, a **separately committed** source-only physical `Forest × Patch × Treatment × SamplingPeriod` row-key protocol may be proposed only if original author code/method validates the meaning of the fields. No opportunistic replacement of field identifiers or 99/594 assumptions.

**Interpretation ceiling:** v3 can resolve the concrete reason for v2's source-header role HOLD (missing synonyms/semantics). It cannot turn the author 47% biodiversity gain into a Structural independent finding nor show the new alpha/beta response. Prior PREDICTS/BALA/Finland/Slovakia/Sweden/NEON/mammal outcomes remain unchanged. PR #469 Draft, main unmerged, no eBird or TinyFish.
