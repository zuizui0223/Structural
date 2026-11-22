# Sweden 2026 independent forest beetle source-only metadata: original CI SUCCESS (2026-11-22)

## Original source identity: actually verified, no biology

[Publisher-only GitHub Actions CI #45032047366](https://github.com/zuizui0223/Structural/actions/runs/45032047366) **SUCCESS**, aggregate-only artifact #14758710527, digest SHA256 c49dd730efb712627a00380c2663103d02446e1348d892501e812cbf19864ec5. This job read only official original publisher REST metadata, did NOT download README, specimen files, source habitat measurements or workbook values and produced **0 ecological effects**.

**Frostgård et al. 2026, Dryad DOI 10.5061/dryad.gqnk98t49:** official public version published 2026-08-05, license CC0-1.0, original three files exactly:
- ModelData.csv, 16,978 bytes, original publisher SHA256 f8197bbb165be0c192f50b47e05d1c052534ffbe9b16a3078598775b050fecc4, original publisher file ID 4898751
- Speciesdata.csv, 177,785 bytes, original publisher SHA256 f538bd94ba476afabe183165950a0be4a710e820e01d6903765539dbe25ead8d, original file ID 4898752
- README.md, 4,705 bytes, original publisher SHA256 8c2ca30286df4ec4c0cd9c2e7c56e5aabc8184662027090d61c5a97c76db603d, original file ID 4898760

The author-described original method has 60 birches + 60 pines on tree-level traps, paired 2+2 per physical plot and only three distinct prescribed-burn stands/years. Exact 30 plot IDs, tree/trap zero source opportunities, taxon names and effort have **not yet been verified by opening source files**. Authors already analyzed birch vs pine richness/assemblage differences (prior art); do not call this a new ecological discovery.

**Distinct Ramberg et al. 2026, Zenodo DOI 10.5281/zenodo.23021809:** official record 23021809, released 2026-09-28, access=open, license CC-BY-4.0, exactly one source file Beetles_data.xlsx, 56,235 bytes, published MD5 42b6ba1d401cf77fc70efcfa91bf7adf. The author paper DOI 10.1007/s10841-026-00832-6 reports five paired location groups / ten cutting stands / 150 **spruce** stumps; these remain published study design counts, not new original row-level validation. This design cannot test host tree species contrast since stumps are all spruce; potential landscape-vs-local spatial context only, and that central finding was already published.

## Next distinct **source-only** gate
- For Frostgård, request one exact official Dryad README file GET by the publisher-authenticated 4898760 file ID, verify SHA/size if available; **any 401/403 becomes final publisher FILE ACCESS STOP for this pass**, without mirror/URL-variant retry. Do not open species CSV or model CSV until author README source method eligibility is established.
- For Ramberg 2026, open only the official Zenodo-signed file link for the one publicly licensed 56,235-byte workbook, verify published MD5, then inspect OpenXML central directory and workbook.xml SHEET TITLES ONLY. Read zero original worksheet cells or species/stand/stump values in that first step; a public file manifest is not a source-key crosswalk.
- Both sources must separately prove original physical plot/site/trap/stand IDs and sampled-zero opportunities before a *new* region/plot-heldout predictive question is frozen or fit.

Do not retry earlier 2025 Ramberg Dryad README HTTP401, do not reopen Ecuador 59-plot outcomes, Finland/Chiu/Carpathian/BETA-FOR/NEON/BALA/GEB/mammal heldout scorers. No eBird/TinyFish. This is a new source-only development lane within unmerged Draft PR #469; no new biological p values or causal claims.
