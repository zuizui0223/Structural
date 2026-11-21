# SLU Sweden6 climate 12-field original header positional diagnosis — response SEALED (2026-11-19)

## Observed source stops, distinct from ecological outcomes

- Original species 6-field header gate [Actions #44454005463](https://github.com/zuizui0223/Structural/actions/runs/44454005463) reached `SLU_ORIGINAL_EXACT_DECLARED_6_FIELD_HEADER_NOT_UNIQUE`. This is preserved.
- Independent original species first-line [Actions #44454288129](https://github.com/zuizui0223/Structural/actions/runs/44454288129) established original 7 semicolon fields `Block;Plot;Log;Sampling_date;Species;Number;STI`, pinned source file SHA256 `a67a905ee05e3994f3e85bc29f8b68fbb314677d6e5a6cc4cd479b2b9d87ec9a`, original 157911B; original species rows=0 read.
- Corrected source audit [Actions #44456134855](https://github.com/zuizui0223/Structural/actions/runs/44456134855), artifact #14497274963 (ZIP SHA256 `77b49f332acea22ff240bb5e1ec8cf06315ec8114f84c6e74d87ff987d1ad27f`) had technical synthetic assertion fixed before real original input. It reached **`SLU_2025_CLIMATE_AUTHOR_ID_SHADE_HEADER_DRIFT`**, because original 12-column climate header's first three names were not exactly the guessed `Block,Plot,Shade` order. No original climate value/CTI/richness, beetle count, STI or row was opened. The previous STOP stays STOP.

Original paper [Goßmann et al. 2024 DOI 10.1111/ddi.13836](https://onlinelibrary.wiley.com/doi/full/10.1111/ddi.13836) independently establishes **six geographical regions, 29 experimental plots (five regions×5 + one region×4), 435 spruce logs (15 per plot)** and three **horizontal forest edge shade conditions**, not a three-dimensional canopy height series. The SLU source README states 88 climate summary rows; 29×3 original shade combinations should equal 87, requiring a separate **row identity/duplicate audit** before any model.

## Exactly one diagnostic

1. Original official publisher climate file only: `https://earchive.slu.se/bitstreams/cac76f42-041f-489a-a568-7d92c0c7941d/download`; permit only identical official host/signed redirect rules of prior SLU source gate, max 1MiB. Do not retry species or README in this diagnostic.
2. Inspect only the FIRST physical CSV header line. Record official file size/SHA256, header-line byte length/SHA256, and exact **12 source first-header field names** with delimiter from fixed `comma, semicolon, tab` alternatives if exactly one 12-field grammar passes; all names must be nonempty distinct UTF8 max128 length, no control characters. **Never open or interpret second/original data rows.**
3. From these source *field names only*, report candidate original `Block`, `Plot`, `Shade` positions by literal exact names and uniqueness, plus lexical numeric/effect field-name tags to distinguish whether actual field identity is possible. Do not pick positional inputs based on available data, supposed good effects or source row count. If physical key names missing/ambiguous, STOP and require original README author schema.
4. The earlier corrected source attempt is NOT rescored or retroactively marked PASS. This is an additional **header-order diagnostic only**; source numerical climate, species, date, plot IDs and sample rows remain unread. No ecological effect or site denominator may be claimed from header names.

Science status `SOURCE_SWEDEN6_CLIMATE_ORIGINAL_12_FIELD_HEADER_DIAGNOSIS_ONLY` if a unique 12-field safe first header is observed; `SOURCE_SWEDEN6_CLIMATE_HEADER_AMBIGUITY_STOP` otherwise. All earlier Structural biological scores untouched, eBird/TinyFish off, draft PR #469 unmerged, main unchanged.
