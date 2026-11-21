# England NFI 2026 second source gate: 24-column author field-name resolution ONLY (2026-11-18)

## Frozen antecedent

The official single **2023–2026** NFI publisher ZIP was already retrieved once in [Actions #44305867348](https://github.com/zuizui0223/Structural/actions/runs/44305867348) under the preceding [source-only protocol](FOREST_NFI_ENGLAND_2026_CANOPY_SUBCANOPY_ORIGINAL_SOURCE_GATE_PRESPEC_20261118.md). Original ZIP **486,883 bytes**, SHA256 **ce3a21377238cc87bde7683917f59a771d20f8e24e81ddf47915362b92281ff4**. Exactly **two CSV entries**, with first-line source header counts **328 fields** and **24 fields**. No original sample values, OTU abundances, coordinates, pseudo-ID values, or biological response rows have been read. The CI archived only an anonymous aggregate file: artifact #14428830300 ZIP SHA256 `d91ec624766d3ae027e91a9e5d6dea1868215c542bd638501d9b7fdd6ec3f487`.

## Why a second header-only gate

The 24-field table contains author-style fields consistent with sample/trap method, tree/forest context, delocalization and time. It **might** be the sampling metadata needed to check source sample identity and author physical-site grouping; this has NOT yet been established. The 328-field table has taxonomic/OTU columns. Only exact original author field labels can disambiguate true site/replicate `plotid` from displaced geography `delocation`; automatically counting those as physical sites would falsely enlarge a national macroecology replication.

## One exact operation before ANY source value row

1. Re-fetch **only** the identical official URL `eDNA Woodland Canopy Subcanopy Data 2023-26.zip` under the same streaming cap, assert **SHA256 ce3a2137...** and 486,883 bytes, exactly two CSV entries, unique source first-line widths 24 and 328. On mismatch or access fail: scientific/source STOP and do not switch archives.
2. Read **only the first physical header line** from the 24-field CSV (not from 328-field OTU table beyond its width), UTF-8 BOM-safe, CSV grammar verified. Export exact **24 original field names** and list of anonymous field-family counts/roles, with original member filenames and **all** data rows untouched. A header field name is source schema, not a sample ID.
3. Predefine **no** plot/key identity, layer mapping, pairing rule or design before source-author labels are seen. Do NOT classify `delocation` as plot, do NOT compute species/OTU richness, canopy-vs-subcanopy associations, or plot counts. Subsequent metadata-only value analysis requires an independently frozen, exact field-role protocol.
4. Scientific mandatory limitation: NFI canopy uses Lindgren and subcanopy Malaise; a layer contrast is not a trap-method-controlled vertical niche effect. DNA sequence read counts are not individual beetle abundances. No plot-temperature or deadwood resource measurements have been confirmed. No biological or conservation effect is estimated.
5. All old Finnish / Carpathian / PREDICTS / Thai / NEON / BALA / GEB evidence unchanged, no main merge, eBird and TinyFish excluded.

Possible result: `SOURCE_NFI_ENGLAND_2026_AUTHOR_24COL_HEADER_ONLY_PASS` or `SOURCE_NFI_ENGLAND_2026_24COL_HEADER_STOP`. An overall Actions SUCCESS is **not** evidence of organismal or ecological success.
