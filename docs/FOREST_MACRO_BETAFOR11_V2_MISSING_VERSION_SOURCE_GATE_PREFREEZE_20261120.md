# BETA-FOR 2025: new v2 original-publisher admission when REST metadata.version is absent

**Precommitted on 2026-11-20 BEFORE any original `BETAFOR_information.csv` member GET or header read.** This is a technical publisher/source-method gate, **not** a new insect response analysis, an ecological inference, or a rescue of any biological null.

## Historical evidence that must not change

- v1 original publisher intake [#44547066063](https://github.com/zuizui0223/Structural/actions/runs/44547066063) is terminal `SOURCE_METADATA_HOLD_PUBLISHER_VERSION_NOT_V1`, because v1 required the exact JSON string `metadata.version == "v1"`.
- The independent **source-only** fixed-DOI/6-MD5/CC-BY-SA verification [#44547066044](https://github.com/zuizui0223/Structural/actions/runs/44547066044) succeeded with official REST **metadata.version literal None**, but deliberately left version resolution diagnostic. It read **zero** original file members.
- v1 first-header attempt [#44547066100](https://github.com/zuizui0223/Structural/actions/runs/44547066100) stopped at that same version gate; no original information CSV/header, source sampling rows, OTUs or biological effects were opened.
- Do not edit, rerun with relaxed settings, overwrite or reclassify any historical v1 files or results. v2 has its OWN future frozen source gate.

## Permitted independently fixed v2 admission

One and only one official record request `https://zenodo.org/api/records/15371332` (no search/latest/random sibling, no redirects off-host). Source metadata must simultaneously pass:

1. `id=15371332`, version-specific DOI `10.5281/zenodo.15371332`, `status=published`, public publisher license ID `cc-by-sa-4.0`. The original [public record](https://zenodo.org/records/15371332) identifies a first published version; **we do NOT substitute a mutable concept DOI or the current latest record**.
2. Entire exact original **six-name original publisher file list** AND each MD5 (and positive integer file size) match the already frozen v1 `FILES` dictionary. No different source files, checksum mismatches, new/removed publisher file, or attempted biological-file content GET.
3. REST `metadata.version` is **missing or JSON null only**. A nonempty unexpected version literal (including `v2`, `1`, `draft` or `v1`) is a different source state and **scientific STOP** for this precise v2 route. Absence does not independently prove release version; exact record ID, published versioned DOI and original six MD5s identify the source. No change to the old v1 requirement.
4. Only if 1–3 PASS: fetch exactly the original `BETAFOR_information.csv` from the **publisher-supplied** same-record HTTPS URL; permit only exact `zenodo.org` original record-member `/api/records/15371332/files/BETAFOR_information.csv/content` or validated `/api/files/<UUID>/BETAFOR_information.csv`, no cross-origin redirect or URL-supplied credentials. Require original publisher `size` and exact file MD5, then inspect **FIRST physical CSV header line only** with the already frozen generic-field whitelist from the existing v1 first-header parser. No source member beyond this one. No original sample IDs, row values, taxa, site or treatment counts decoded.
5. Original first-header **role coverage** (forest/region, patch, treatment, time/effort) determines status `SOURCE_INFORMATION_GENERIC_HEADER_CANDIDATES_ONLY_NO_ROW_ADMISSION` or `SOURCE_METHOD_HEADER_HOLD_INCOMPLETE_GENERIC_ROLE_SUPPORT`. Unknown header names must NOT be disclosed or automatically synonym-matched. A header PASS is **only syntax**, never authorization for data-row reading or biological inference.
6. Fail safely on publisher network 401/403, byte mismatch, header parse failure. Such a STOP is **not** an ecological null.

## Source hierarchy and future scientific direction, no response access yet

Original Rothacher et al. 2025 Malaise programme describes six **German regions**, 11 **forests**, 99 source patches (**9 patches/forest**) and six repeat collection periods (**594 original sample opportunities**), and published treatment-associated diversity changes. Broader BETA-FOR 234 patches are the **same parent experiment** and must never count as independent replication. A method header does not source-verify 99/594.

For new *method rows*, a **separately precommitted** source-only author field-role/ID/period/effort stage is required. For future biology, predefine the local `alpha` versus spatial `beta` outcome, site/patch paired treatment-control support, sampling coverage, detector effort, prespecified holdout by forest and region, and treatment/forest interaction before any OTU response is read. Prior original authors' positive treatment effect is prior art; the meaningful **new** question is whether alpha gains accompany regional community homogenization or differentiation and whether their directions transport to unseen source forests.

**No new source member read is permitted if the new v2 script is not frozen on GitHub before workflow execution.** Original PREDICTS/BALA/Finland/Slovak/Sweden/NEON/Island cohort results and scientific holds remain unchanged. eBird/TinyFish unused; PR #469 draft, no main merge.
