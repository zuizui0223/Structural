# Weiss et al. 2016 original Dryad legacy XLS byte-integrity gate (2026-11-18)

## Pre-existing immutable source evidence

The already executed and successfully checked publisher-only [Actions #44243234720](https://github.com/zuizui0223/Structural/actions/runs/44243234720) froze the official Dryad metadata for the author-deposited data accompanying Weiss et al. (2016), DOI **10.5061/dryad.39k32**, public CC0, originally released **2017-02-05**. The publisher reports a *single original* `FITBeetleData_CzechRepublic_2007+2008.xls`, file ID **33652**, **232,960 bytes**, MD5 **83f740353530b8f88b05260813704eab**. The original metadata digests were:
- dataset JSON SHA256 `8c6bb9cb776dcb44fdb973a5f0c78adad917fa3ff7e12ef01bb1018a074a4442` (5,445 bytes)
- version JSON SHA256 `7a65b86800a7b719a2420cf70a49e15c5a45b55dc4ce8b559a8ffae01dcf0cfa` (5,382 bytes)
- file-list JSON SHA256 `5a15c961c67fe0b120fa46e8746fbea1516756136940257bc6d1b075f869c4f7` (1,352 bytes).

The PLOS supplement for the *same* Weiss study was separately authenticated as a 488,960-byte OLE DOC. Flattened antiword text failed to establish 512 reliable individual species↔guild row boundaries; do not force a positional parser. Earlier Franzén 2026 Dryad original `tableS1.xlsx` returned HTTP401 and is **closed**, not a retry candidate here.

## Exactly one new original-source transport and byte-integrity test

1. Issue only **one** ordinary, anonymous, read-only HTTPS GET to official `https://datadryad.org/api/v2/files/33652/download` after the above publisher metadata/rights and file ID have already been frozen. Block redirects to any host; no OAuth, alternate endpoint, mirror, API version or retry. Source failures are kept separate from ecological null.
2. If HTTP200 delivers file bytes, require exactly **232,960** bytes and MD5 **83f740353530b8f88b05260813704eab**, then inspect only the **first eight binary magic bytes** and file size; candidate legacy .xls must be OLE Compound Document signature `D0 CF 11 E0 A1 B1 1A E1`. Compute the original SHA256 from opaque bytes. Do **not** parse XLS worksheets, rows, species, family, feeding guild, sample counts, presence/abundance, or any original specimen response. No spreadsheet artifact is being created or edited; this is a binary-format provenance check only.
3. If HTTP401/403 or an unresolved redirect occurs, return a terminal `SOURCE_ORIGINAL_WEISS_DRYAD_FILE_HTTP_XXX` or `SOURCE_ORIGINAL_WEISS_DRYAD_REDIRECT_STOP`; do **not** try other Dryad file routes. A successful GitHub Actions test may legitimately record a SOURCE STOP; a green CI is not a biological confirmation.
4. Ensure synthetic test rejects HTML/PDF/OOXML, wrong digest and wrong source length, while keeping all original data opaque. On success the only next stage permitted is a **separately precommitted** safe worksheet/header + author original species-to-guild ontology check, then an independently precommitted name-only coverage audit against Gloor 116-plot beetle species header (before opening abundance values). Do not invent guild mapping from synonym similarity or family-level assumptions.
5. No Gloor species headers/abundance, original Weiss guild rows, previous Finland/Chiu/Piccini/BELongDead/PREDICTS/NEON/BALA/GEB biological response reopening, eBird, TinyFish, main merge or author correspondence. PR #469 stays Draft.

This is **the same Weiss 2016 study** in Dryad and PLOS, not independent field replication. The separate functional prediction target remains incremental out-of-stand or out-of-range heldout beetle feeding-guild composition from locally measured wood beyond a frozen reference, only if the source ontology actually qualifies.
