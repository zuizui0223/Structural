# BETA-FOR 2025: strictly source-metadata 594 sampling opportunity audit (first original row opening)

**2026-11-20 response-blind prefreeze.** Every earlier publisher/source header gate remains immutable. This is a NEW design-only protocol, not permission to inspect `com_singletons.csv`, species lists, OTU counts, trait or biodiversity outcome columns.

## Fixed original evidence and paper-defined expectations

- Immutable publisher record 15371332; version-specific DOI 10.5281/zenodo.15371332; published status CC BY-SA 4.0; six previously SHA/MD5-checked original files; `metadata.version` absent, not conflicting with original record release. 
- v2 CI #44729512107 author-authenticated the single `BETAFOR_information.csv` original **46,965 bytes** (MD5 `873f5d424904d1eed00e079b945dd5dc`) and eight semicolon header columns, source response rows untouched.
- v3 CI #44729825869 verified exact *nonbiological* author field names and roles by position: `patch;sample;firstday;lastday;meanday;treatment;X;Y` (positions 1–8). `firstday/lastday/meanday` are named time columns but their actual numeric/date formats remain unverified. `X/Y` field names are NOT enough to infer coordinate projection or precision.
- Published Rothacher et al. 2025 original methods DOI 10.1111/1365-2664.70086: **11 forests, six geographic regions, 9 patches per forest, six collection rounds per patch**, nominal **99 physical patches ×6=594** source sampling opportunities. The author paper assigns one untreated `CC` and eight different manipulations in a 9-patch layout per forest.
- Independent BETA-FOR site codebook in original published programme: exactly `B04 B05 B06 B07` (Bavarian Forest), `U01 U02 U03` (Sailershausen/University Forest), `P08` (Passau), `H09` (Hunsrück), `S10` (Saarland), `L11` (Lübeck). This is **11 forest sites in six region groups** but whether their prefixes are encoded in original `patch` strings is STILL unproven. No source-code row matching from arbitrary aliases allowed.

## Exactly ONE allowed publisher member and exact columns

Download through an original author-publisher supplied Zenodo 15371332 file link only the frozen `BETAFOR_information.csv` member. Reverify full MD5 and exact size first. Read its *eight source metadata fields* in all data rows, using `;` CSV parsing. The fields are original author **method/sample descriptors**, not species/OTU responses.

- No other original six file member downloaded, including `com_singletons.csv`, `OTUArtenlisteGesamt.csv`, `.fasta`, tree or calibration points.
- No original plot IDs, source coordinates, sample labels, dates, treatment label strings, biological raw records or individual-row values may be committed, printed or uploaded. Only counts, boolean/percentage source-frame checks and anonymized cell counts; no location tables.
- No imputation of missing observations to zero; no behavior/suitability/causal effects.

## Frozen source-only validation gates (do not tune on observed rows)

1. Parse exact eight-column original semicolon CSV with one original first header; reject additional fields, duplicate `(patch,sample)` keys, empty patch/sample/treatment, or original physical CSV grammar drift. Report only total parsed rows, distinct patches, distinct patch×sample pairs, missing field counts, and counts of repeated samples/patch.
2. **Expected nominal original design:** 594 parsed author sampling rows, 99 unique physical `patch` codes, six distinct `sample` codes *within every patch*, stable exactly one `treatment` code within patch, and **nine unique manipulation categories including control per original source forest** if site code mapping can be established. A count discrepancy is an informative **SOURCE_OPPORTUNITY_STOP**, not automatic biological attrition or a reason to drop rows.
3. Site-prefix ID gate pre-frozen *before values*: source patch codes must begin with EXACTLY one of the eleven published uppercase site tokens `B04 B05 B06 B07 U01 U02 U03 P08 H09 S10 L11`, followed by at least one legal alphanumeric/`_-` suffix; no alternative suffix, substring or inferred site grouping after this one-shot gate. If the source uses another code style, record `SITE_PREFIX_ID_UNVERIFIED` and preserve all row/source counts; do not rescue by guessing.
4. If gate 3 qualifies: require 11 published site tokens, 9 unique source patch IDs per forest, six published region groups, and within each site exactly nine distinct original treatment strings across nine patches (do not export strings). Site/year confounding (2022 vs 2023) remains acknowledged; site token ≠ independent region.
5. Report nonblank `firstday`, `lastday`, `meanday` counts and ASCII date representation format categories ONLY, without claiming year/date order before independently verified author format. Do not infer actual `X,Y` projection; optionally check numeric parseability and within-patch coordinate consistency without export. Missing times or coordinates are separate diagnostics, not biological nulls.
6. No biological endpoints are estimated. A pure method qualification requires count+ID+treatment gates; unresolved date semantics or trap exposure keep subsequent biological-opportunity admission CLOSED. Even if all pass, explicit OTU/source sample ID crosswalk and technical sampling efficiency remain future stages requiring distinct precommits.

## Ecological hypothesis is LATER, not tested here

Published original canopy-gap + deadwood experiment already supports positive insect Hill diversities (up to 47% after coverage standardization): PRIOR ART. A genuinely different test would examine whether patch treatment **increases local alpha while changing between-patch Simpson replacement / within-forest beta / forest gamma**, and whether that relationship repeats in leave-one-*region*-out prediction. This cannot be claimed from the current method table. Forest sites (n=11) nested within 6 geographic regions are the macrogeographic units; 594 collection records are NOT independent forests. The 234-patch parent BETA-FOR sample is not an independent experimental cohort.

Stop if original file integrity or source design differs; keep historical source STOPs, all prior published/null results and PR #469 draft/main unchanged, eBird/TinyFish unused.
