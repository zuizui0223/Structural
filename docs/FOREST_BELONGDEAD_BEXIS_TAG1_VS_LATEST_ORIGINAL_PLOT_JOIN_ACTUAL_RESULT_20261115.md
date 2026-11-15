# BELongDead original-source reproducibility: BExIS 31123 and 24546 tagged release vs latest, real 30/30 source plots (2026-11-15)

## Result

**The original BELongDead beetle and ambient deadwood datasets are byte-identical between their publisher's original tag1 and default latest API payloads** on 2026-11-15. Their **30/30 physical plot-ID join is therefore reproduced for the exact published tag1 releases**; this validates previously reported actual-source sample hierarchy and prevents accidental mixing of source revisions. Original species counts/captures, source deadwood tree species/volumes, trait assignments, coordinates and biological effect values were **not opened, changed, reestimated or exported**.

Original version-selection failure detected in prior code: BEXIS2/Core officially documents `GET /api/Data/{id}` returns the *latest* database dataset. Only the [official `GET /api/Data/{id}/tag/{tag}`](https://github.com/BEXIS2/Core/blob/master/Console/BExIS.Web.Shell/Areas/DIM/BExIS.Modules.Dim.UI/Controllers/API/DataOutController.cs) selects the public tagged version. The previously source-verified `/api/data/{id}` data **was not a proven tag1 source at that time**. [Frozen version comparator before the new audit](FOREST_BELONGDEAD_BEXIS_ORIGINAL_TAG_VS_LATEST_PROVENANCE_PRESPEC_20261115.md).

### Actual source-only GitHub Actions evidence

One exact source version test [**Actions #43708115836 SUCCESS**](https://github.com/zuizui0223/Structural/actions/runs/43708115836), anonymous artifact **14159635833** SHA256 `cfe2a2ed7fb97b23fbe895787d63cf90840fce6aeaeb5257b56ff751fd975470`. Original BExIS 31123 and 24546 both published CC BY4 and publicly accessible in the author's original publisher. Two *different REST endpoints* were used exactly as documented; no other host or blocked endpoint.

| Source | Public tagged original REST | Tag1 original bytes | Exact original SHA256 | Equal to previously audited default/latest payload |
| --- | --- | ---: | --- | --- |
| BELongDead original saproxylic beetles | `/api/data/31123/tag/1` | **8,103,493** | `73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e` | **YES** |
| Original BE 2012 deadwood item inventory | `/api/data/24546/tag/1` | **417,351** | `5a02350e4f1e364302dea20ca25281e65f2158d318d9fbcef56be2fe6d57786a` | **YES** |

Exact source metadata (no biodiversity):
- Original BExIS31123 tag1 CSV: **59,850** source long rows, 17 original headers, **30 unique `PlotID`**, 3 Exploratories and 30 nested `Exploratory×PlotID` plot IDs, zero missing source plot IDs.
- Original BExIS24546 tag1 CSV: **7,671** item rows, 12 headers, **148 unique `plotID`**, zero missing source plot IDs.
- Exact `31123.PlotID` intersect `24546.plotID` (surrounding whitespace stripped ONLY): **30/30**. All original BE beetle experimental source plots occur in the original tagged 2012 deadwood dataset. **118** extra ambient inventory plots are not this experimental network. This is a source-name exact join, not causal or year-aligned proof.
- Original `GET /api/dataset/24546/tag/1` publisher dataset JSON returned `version=2`, `versionId=4191`, `dataStructureId=1027`, `metadataStructureId=3`. **Published tag number 1 must not be mislabeled BEXIS internal version1**, even when the public BE project catalogue cites “Version 1”. Current and tag1 content were identical on the audited date despite internal version2. Downstream methods cite the original **tag1 + SHA256**, not an assumed API default version.

## Source authors' measurement coverage versus unresolved variable codebook

The BE project's official 2024–25 infrastructure reference [forest deadwood inventory table](https://www.biodiversity-exploratories.de/wp-content/uploads/infrastructure-information-provided-by-core-projects.pdf) specifically describes dataset 24546 as **volume of large/small deadwood items by tree-species identity, origin and decay stage** (2012 inventory). This directly supports that source data *conceptually* include ambient deadwood supply type and quantity. It does **not** define the names `spec1`, `spec2`, `DWV`, `Vharv`, or the numeric unit conversion. The original public metadata `/api/metadata/24546?tag=1.0` did not provide exact field-code descriptions to the preceding fixed dictionary scan [CI #43707184031 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43707184031); no values were inferred or read for that stage.

A separately frozen **official data-variable dictionary** attempt uses exactly the public [BEXIS2/Core DataStatisticOutController GET api/DataStatistic/{id}](https://github.com/BEXIS2/Core/blob/master/Console/BExIS.Web.Shell/Areas/DIM/BExIS.Modules.Dim.UI/Controllers/API/DataStatisticOutController.cs). Its published `ApiDataStatisticModel` has original `VariableName`, `VariableDescription`, `DataTypeName`, and `Unit`. The original endpoint response also contains `uniqueValues` and min/max—**none of those original wood measurements are exported**. [Separate source dictionary prespec](FOREST_BELONGDEAD_BEXIS24546_OFFICIAL_VARIABLE_STATISTICS_CODEBOOK_PRESPEC_20261115.md); code `analysis/forest_macro_global/belongdead24546_official_variable_stats_codebook.py`, workflow `.github/workflows/forest-belongdead24546-official-variable-statistics-codebook.yml`.

## Ecological consequences, what is and isn't proven

A verified exact original **30 source forest plot** join between ambient original 2012 field deadwood inventory and experimentally offered deadwood logs is a real improvement over previous unrelated inventory BExIS3546 **0/30** and source `EP` stand basal area BExIS18270 **3/30**. Previous BE VIP–EP plot metadata BExIS1000 remained **nonpublic** and was not opened, nor must it be used if source access is unavailable.

The original 31123 BE dataset separately contains 13 experimental wood host categories, 379 original nested `TreeID` candidates and repeated 2010–2017 observations; 31124 complete-view contains 15 novel `TrapID` strings under otherwise matched original log+year parent contexts, so **all true zero-capture sampling opportunities / effort still unconfirmed**. Do not pretend 59,850 source records are independent forests or that species absent from records have verified zero captures.

**Until direct field-code semantics and individual trap/zero-capture effort are certified, no new source-pool × supplied host wood ecological interaction, species preference, p-value or CI may be estimated.** This is now an identifiable site-level *resource measurement opportunity*, not a validated organismal effect. Source original prior scientific results Finland 142-site VD10 heldout +0.00024237/p=.015 (small exploratory), Finland guild shuffle +0.035237, Burner 3-country +0.091059, PREDICTS 39-study forest altered/ref +0.0942, NEON canopy height +0.0349/p=.1759 (non-support), BALA and GEB holds all **unchanged**. eBird/TinyFish not used; Structural PR #469 remains Draft/unmerged.
