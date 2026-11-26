# England NFI 2023–2026 original canopy/subcanopy archive — verified metadata-only result (2026-11-18)

## Scientific result boundary

**Source archive and both CSV first headers PASS; organismal/vertical ecology has NOT been scored.** This newly admitted England-wide external survey is an original geography/method candidate, **not** a new independent positive finding about forest niche separation, tree resource filtering or climatic refugia.

## Exactly what happened

[Original publisher archive + first-header GitHub Actions #44305867348](https://github.com/zuizui0223/Structural/actions/runs/44305867348) succeeded under the [prespecified zero-response source-gate](FOREST_NFI_ENGLAND_2026_CANOPY_SUBCANOPY_ORIGINAL_SOURCE_GATE_PRESPEC_20261118.md). Archival manifest: artifact **#14428830300**, ZIP size **1,408 bytes**, SHA256 **d91ec624766d3ae027e91a9e5d6dea1868215c542bd638501d9b7fdd6ec3f487**. The archived JSON was independently inspected against its artifact checksum.

Official original record: UK Forestry Commission NFI Canopy & Subcanopy Arthropod Communities, UUID **2b8a8f17-3745-43d1-bb32-0d509230f158**, public NCEA registry revised **2026-09-08**; original **2023–2026** data ZIP distributed under the governmental dataset link (not the cached 2023–24 ZIP). The official archive downloaded once via HTTPS at **486,883 bytes**, SHA256 **ce3a21377238cc87bde7683917f59a771d20f8e24e81ddf47915362b92281ff4**.

The ZIP contains **exactly two original .csv files** (the ZIP central directory reports total **3,808,611 uncompressed bytes**, member-compressed sum **486,327 bytes**). Both first lines passed UTF-8-delimited first-header parsing:
- Original table A: **328 header columns**, includes taxonomic/OTU header family but no verified original plot/sample/method/time author-field family.
- Original table B: **24 header columns**, has original source field-name families compatible with candidate sample/plot keys, delocalization, layer/trap method, tree/forest type, time and taxon metadata. **Exact author column spellings and corresponding field semantics have not yet been frozen**. A pattern match is not evidence of a unique physical plot ID.
- **0 original CSV data rows, 0 OTU/species detection values, 0 sample/physical-site or de-localisation identifiers and 0 geographic coordinates were accessed**. Source member filenames and unneeded OTU header text were not exported.

The original dataset catalogue explicitly specifies **Lindgren canopy versus Malaise subcanopy** traps and reports metabarcoding **read counts**, not individual abundance. Therefore the method and vertical layer are not experimentally separable, and without author-defined physical plot/method effort the data cannot be scored as same-method vertical niche effects. Masked delocalisation grids must not be counted as independent physical forest plots.

## Next frozen source step

A separate [24-field author-header-only contract](FOREST_NFI_ENGLAND_2026_24COL_AUTHOR_FIELD_HEADERS_PRESPEC_20261118.md) and executable workflow [forest-macro-england-nfi2026-author24-header-only.yml](../.github/workflows/forest-macro-england-nfi2026-author24-header-only.yml) were committed **before accessing any sampling metadata value**. Their only job is to verify the exact same 486,883-byte SHA-pinned source and archive the **24 original column names, zero CSV sample body rows**. A subsequent, separately fixed metadata-only test may distinguish physical site vs pseudogeography, paired method opportunities, field season and tree species. If these fail, scientific STOP; do not invent NFI forest sample sizes or switch to a second archive.

Prior Finnish, Carpathian116, PREDICTS, Thai, NEON, BALA and GEB biological results remain unchanged; no old sealed outcomes, eBird or TinyFish; PR #469 Draft/unmerged and main unchanged.
