# Kriegel 2023 European 8-country beetles: original publisher manifest verified, biological source file HTTP 401 (2026-11-17)

## Completed strict source-only field-access result

After the original code-only Dryad version-ID parsing fix, [original source-only GitHub Actions run #44078786160](https://github.com/zuizui0223/Structural/actions/runs/44078786160) completed SUCCESS (metadata/known-truth script execution). Biological eligibility, however, is **SOURCE ACCESS STOP**. The official [Dryad 10.5061/dryad.brv15dvch](https://doi.org/10.5061/dryad.brv15dvch) publisher REST API returned the exact dataset identity, public visibility, CC0 license and published version ID **227862** / versionNumber **5**. The official published version has exactly **eight** listed files with SHA-256:
- Analyses.html 1,485,325 bytes, digest `28ae359f9e0cd6704b6050757d5944b305fa045dd665cc135cca9c886671a105`
- Analyses.rmd 12,298 bytes, digest `20c2d810364c0db1cc70e1dd324522816e41824f268b9d3d7b1ba2edac4cfad9`
- README.md 2,848 bytes, digest `c46c51f334e978a2eff358f0e4d765ffd76d0d526908ea3c1cab76b456b12ebc`
- data_legend.csv 2,680 bytes, digest `5b165a3b4bffdfa3f5a9accb9a2c780a477f227b99c353a284304ba328c3e1c4`
- saproxylic_beetles_europe.csv 1,987,506 bytes, digest `56bddde039e6c3d84e29c52940f47677649e3640c2dfd9f5568d008f0e585c34`
- trait_legend.csv 1,484 bytes, digest `7a0f1ad711255168266b55a10d96f7a476e69c2a520da87d58720d3cb3c2bc8b`
- traits.csv 27,611 bytes, digest `45595e0ffa8ab776a103d0f90efd1ca579e72a6be9bd8b1660e9648206fff9b5`
- traits_corrected.csv 37,337 bytes, digest `037f2fc2d9c4adaad28cb30ba2fc7f7feee9421220bef6e1d02a2b6caea7ddb1`

**Official first-line-only GET of the published biological original `saproxylic_beetles_europe.csv`: HTTP 401.** The source method/guild headers, site/wood-object joins and codebook values were therefore **NOT read**. Zero new original species, traits, abundances, study IDs, geographic source observations or model effects were scored. Artifact #14325907708, GitHub Actions ZIP SHA256 `6c25b45cc06ae3929d3aa8aa8af117c4b101c17702321e79d74ad4f33e44db07`.

The initial source-only run [#44078575945](https://github.com/zuizui0223/Structural/actions/runs/44078575945) stopped at a **code error** `SOURCE_STOP_PUBLISHER_LATEST_VERSION_ID`: it expected `version.id` instead of using the numeric version ID from the exact publisher `stash:version` link. That was corrected before any original file read, in [documented fix](FOREST_BEETLE_KRIEGEL_DRYAD_VERSION_ID_SOURCE_FIX_20261117.md), and the corrected source-only diagnostic above ran once. No further alternate source URL, mirror, credential or access bypass tried.

### Science and transferability
Kriegel et al. (2023), Ecology Letters DOI [10.1111/ele.14227](https://doi.org/10.1111/ele.14227) reported **21 field source datasets from 8 European countries** with 332,557 beetle individuals, 901 species and 49 tree species, including strong published substrate-vs-ambient energy guild sorting. Those are **PRIOR ART**, not a newly produced Structural positive. A different leave-original-source-out *predictability* endpoint is scientifically relevant but **not yet estimable with verified source biological values**. The 21 source study datasets may also overlap previous European papers and are not assumed independent.

**Decision:** close this specific blocked official Dryad file route; do not treat 401 as ecological null, nor claim source manifest availability means an eligible biological cohort. Advance to independently published Zenodo original forest surveys with source site, field effort and trait/functional grouping instead. Original Piccini floor p=.09375, Finnish VD10 +.00024237, three-country trait-label +.091059, PREDICTS, NEON, Thai and BALA/GEB holds unchanged; no eBird/TinyFish. PR #469 Draft/unmerged.
