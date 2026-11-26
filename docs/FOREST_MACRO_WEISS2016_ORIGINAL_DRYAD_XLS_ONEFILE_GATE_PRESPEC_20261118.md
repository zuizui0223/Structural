# Weiss2016 ORIGINAL Dryad legacy XLS source-byte gate (2026-11-18)

## Frozen and truly author-original provenance

A one-pass, original-publisher **metadata-only** [GitHub Actions #44243234720](https://github.com/zuizui0223/Structural/actions/runs/44243234720) succeeded without any XLS data-file request, reporting:

- Weiss et al. 2016 *PLOS ONE* paper DOI 10.1371/journal.pone.0149506, original **same-study** Dryad DOI `10.5061/dryad.39k32`; **CC0** archive published 2017-02-05. This is an alternative original author data format for the same Weiss Czech forest sampling, NOT a second independent study or independent validation.
- Original public file `FITBeetleData_CzechRepublic_2007+2008.xls`, publisher file ID **33652**, **232,960 bytes**, published original **MD5 83f740353530b8f88b05260813704eab**.
- Exact publisher metadata fingerprints fixed before new access: dataset JSON SHA256 **8c6bb9cb776dcb44fdb973a5f0c78adad917fa3ff7e12ef01bb1018a074a4442**, version JSON **7a65b86800a7b719a2420cf70a49e15c5a45b55dc4ce8b559a8ffae01dcf0cfa**, version-file-list JSON **5a15c961c67fe0b120fa46e8746fbea1516756136940257bc6d1b075f869c4f7**. One original file only.
- Original separate PLOS S1 DOC DOI `10.1371/journal.pone.0149506.s001` was source-verified 488,960 B SHA256 `f5c0d5e7e9e19c45f9e6e23c40c5c8cf1ddda2f4e5b4272289a328912350c3de`. Antiword width checks did **not** validate individual 512 species-to-six-guild row pairs. The six PLOS author codes `m,n,p,s,x,z` are described in paper, not independently row-counted.

## ONE precise original-file access and format test

1. Make **one anonymous official** GET to `https://datadryad.org/api/v2/files/33652/download` (no alternative URL, mirrors, credentials, HTTP redirect, CDN or retry), cap 250,000 bytes and 50 seconds.
2. Require 200 status, published byte length **232,960**, exact **MD5 83f740353530b8f88b05260813704eab**, and legacy Microsoft Excel OLE Compound Binary File magic **D0 CF 11 E0 A1 B1 1A E1**. Treat any HTTP401/403 as original file ACCESS STOP (the independent Franzén original XLSX previously returned HTTP401; do not reuse that blocked file in this test), HTML/ZIP/non-OLE as source-format STOP.
3. Store original workbook bytes privately in GitHub runner temporary memory only for length/MD5/SHA256 and magic. **Do NOT parse any XLS sheets, read any species/guild/status/abundance values, print columns or raw binary, or export the workbook**.
4. Output only one source-authentication receipt: original published DOI, exact author filename, publisher ID, bytes, source-MD5 and computed SHA256, format flag, HTTP status or SOURCE STOP classification. A successful source fingerprint allows a *separate new prespecified XLS sheet-name/first-header-only method gate*. No species↔guild mapping, Gloor species-name coverage or ecological predictive endpoint in this one-file stage.
5. Do not loosen the old Franzén Dryad file HTTP401 via source-ID substitution; this is separately authored Weiss2016 original file, not a backup mirror. No new biological effect in any case. All earlier Finland/Chiu/Piccini/BELongDead/PREDICTS/NEON/BALA/GEB scores stay frozen; Gloor original 116-plot species identities/counts unopened, no eBird/TinyFish, PR #469 Draft/main unchanged.

**Success is source-byte and file-format authenticity only**, not ontology coverage, original author-design independence, or evidence for resource–guild ecological association.
