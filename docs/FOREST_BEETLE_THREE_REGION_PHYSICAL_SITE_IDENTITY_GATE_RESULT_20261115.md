# 2026-11-15 source-only physical-site identity audit of the three-country saproxylic beetle matrices

## Executive decision — header Q/A PASSED; author site crosswalk still scientifically STOPPED

The previously completed **retrospective sample-column** `Host_tree` three-country conditional-null score **D=+0.091059, p=0.000333** remains unchanged. It is NOT a test with 1,622 independent physical forest sites. An author-source field crosswalk for true physical-site-year clustering has **not** been demonstrated, therefore no new host-guild biological scoring or physical-site p-value was performed.

**Actual GitHub CI successful source-only lexical audit:** [#43676631039](https://github.com/zuizui0223/Structural/actions/runs/43676631039), artifact **14146718144**, ZIP SHA256 `8b00d127e61d97f106f5c8997a187c9c4f35edda17b2d8770cb511fffa60c040`. The first CI [#43676546805](https://github.com/zuizui0223/Structural/actions/runs/43676546805) retrieved all source original matrices and computed their anonymized year-token candidate counts correctly but failed at the final JSON-parse step: a code-only output writer used literal `\\n` rather than a newline. This was corrected in commit `1c3d93f297893864baa89642b28605d98f3a5541`, with all source gates, published sample counts and algorithms unchanged; corrected CI #43676631039 ended SUCCESS. It is NOT a new or rerun ecological-positive endpoint.

### Original Zenodo v1 5950610 sample column header-only physical ID candidates

| Original country | Author original physical sites | Source sampling columns | Year token syntax in ALL original columns | Candidate source label bases after removing EXACT year token | Candidate distinct bases with repeats | Extra sample events beyond candidate distinct bases | Physical identity is author-validated? |
| --- | ---: | ---: | --- | ---: | ---: | ---: | --- |
| Finland | **142** | **153** | year **prefix**, 153/153 | **143** | **10** | **10** | **NO**: 143 != 142 |
| Germany | **386** | **386** | no explicit four-digit year token | No original-year-based merge | No merge inferred | 0 by published counts | **NO mapping tested**; author's one-sample/site design only |
| Norway | **468** | **1,111** | year **suffix**, 1,111/1,111 | **468** | **237** | **643** | **NO**: count match alone insufficient |

- All three MD5s matched the frozen original [Zenodo 2022 source files](https://doi.org/10.5281/zenodo.5950610), source sampling header labels were nonempty and unique. Source rows, species identities, capture counts, Host_tree traits and biological `sqrt(JSD)` scores **were never read or rerun**.
- Norway's simple suffix stripping agrees exactly with authors' published 468 physical locations; 237 candidate labels represent repeated events and the maximum is six sampling columns per candidate base. This is strong source-pattern support but remains a **candidate** until authors' site/year/project field definition is verified. A shared abbreviated label could conflate plots from different source projects; the author source hierarchy is necessary.
- Finland's simple prefix stripping yields 143 unique bases and 10 repeated candidate labels; published field design has 142 physical locations and 11 repeated events. The discrepancy is **one unresolved physical-site alias/mapping**, not a reason to merge two apparently similar plot codes or pick a favorable ecological outcome. The exact cause cannot be distinguished from the field label alone.
- Germany's 386 unique source sampling columns agree with its published 386 one-time field sites, but sampling areas come from multiple source studies, not 386 independent experimental replicates.

### Independent author 2021 Dryad methods file access check: genuine metadata transport STOP

The [original 2022 Zenodo archive](https://zenodo.org/records/5950610) points to an associated [Dryad 2021 author archive](https://doi.org/10.5061/dryad.tmpg4f50b) for trap effort, dates, geographic site covariates and original field metadata, rather than containing all those values itself. We attempted exactly one ordinary public GET per original referenced file, without authentication bypass, user token, guesswork or taxon outcome access.

| Original Dryad author file | Public source file-stream HTTP result |
| --- | --- |
| `README_data.txt` | **403** |
| `DATA_Finland.csv` | **403** |
| `DATA_Germany.csv` | **403** |
| `DATA_Norway.csv` | **403** |

The [source access verification CI #43676744447](https://github.com/zuizui0223/Structural/actions/runs/43676744447) finished **SUCCESS** because it correctly documented the access stop without asserting any ecological result; artifact **14146672963**, ZIP SHA256 `d443bd72d74e3baa2341d8d542893d48abe0a4ae1a53fff295593cb3e50a77e9`. Four HTTP 403 results are the reason that the needed original-site crosswalk was NOT performed. Repeatedly requesting variants of the same blocked endpoint without a new authorization/source does not improve the science.

## Next gate, not an automatic rescore

**Need exactly the authors' original physical-site × survey-year identity** from legitimate 2021 Dryad `README_data.txt` + original country `DATA_*.csv` (or equivalently the authors' verified physical site–year crosswalk). Verify full coverage and collision-free project-specific site keys; reproduce Finland 142, Norway 468 and Germany 386 *by author definitions*, not by arbitrary string matching. Until that evidence exists: retain original sample-column D/p as conditional *trait-label randomization* only, and physical-site sensitivity as **NOT ESTIMABLE FROM VERIFIED CROSSWALK**.

Once verified, the [new before-crosswalk plan](FOREST_BEETLE_THREE_REGION_PHYSICAL_SITE_ID_SOURCE_AUDIT_PRESPEC_20261115.md) specifies one separately labelled **post-result** incidence-OR per physical site and within-country 2,999 trait-label shuffle sensitivity. It must report positives, negatives, stops and denominator changes regardless of results; no claim of new independent confirmatory ecology. No false multi-biome/site independence and no source trees/forest canopy/biomass/thermal mechanisms claimed.

**No biological scores changed:** previously frozen PREDICTS forest-formation contrast +0.0942, NEON static CHM vs beetle spatial β +0.0349 p=.1759, the existing 2026-11-15 original guild result +0.091059 conditional p=.000333, old BALA outcomes and mapped-mammal GEB scientific HOLD. eBird/TinyFish not used; PR #469 remains Draft/unmerged.
