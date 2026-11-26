# 12-year saproxylic beetles: verified 42 plot labels, 52 nested deadwood logs, 522 log×year source contexts vs 525 matrix source IDs (2026-11-15)

## Main result — a genuinely usable independent original hierarchical DATA source, NO ecological effect yet
The original Zenodo [10.5281/zenodo.17337484](https://doi.org/10.5281/zenodo.17337484) (2025-10-23, public **CC-BY-4.0**) was audited directly in GitHub Actions without changing old Structural biological endpoints. Original author study: Lettenmaier et al. (2025/2026), *Journal of Animal Ecology* [DOI 10.1111/1365-2656.70183](https://doi.org/10.1111/1365-2656.70183), 35,059 individuals and 297 beetle species **reported by the authors**, with standing original spruce/fir/beech deadwood host logs sampled over 12 years (their original sampling dates need effort normalization).

- [Official original Zenodo metadata and license CI #43696147420](https://github.com/zuizui0223/Structural/actions/runs/43696147420) SUCCESS: original **7 source files** and their checksums. Artifact #14154870253, zip SHA256 `259f50115d47caac90275c4ebd8102f8a47b79a9f229e3a3f67a0d62283ab7d5`.
- [Original MD5-verified CSV headers and original trait sheet CI #43696559654](https://github.com/zuizui0223/Structural/actions/runs/43696559654) SUCCESS. Original `Beetle_Community_JAE-2025-00357.csv` **298 fields, 526 physical lines including header**; `Beetle_Data_JAE-2025-00357.csv` **15 fields, 7739 physical lines including header** and author metadata fields `plot,log,year,tree`; original `Trait_Table_JAE-2025-00357.xlsx` with source `Trait_Table` sheet.
- [Full **metadata-only** nested original field grain CI #43696912095](https://github.com/zuizui0223/Structural/actions/runs/43696912095) SUCCESS; aggregate artifact #**14154582676**, zip SHA256 `b2b7760894c3093b4e9fed99ecca0374e51a8c7fd0d62ca98ad7c9ac32c22472`. This stage reads ONLY source `plot`, `log`, `year`, `tree` on original long table and the FIRST column of community CSV as a candidate sample label. It NEVER scores original capture/species abundance or trait values, no source site IDs/taxon labels/individual wood measurements exported.

## Source hierarchy observed, not presumed

| Original-author source metadata | Original observed |
| --- | ---: |
| `Beetle_Data` long table source rows | **7,738** (NOT 7,738 plots or beetle individuals) |
| Long source rows with nonmissing `plot`+`log`+`year`+`tree` | **7,738 / 7,738** |
| Distinct source `plot` tokens | **42** (NOT automatically 42 independent forest studies) |
| Source nested physical candidate `plot×log` keys | **52** |
| Distinct `plot×log×year` candidate contexts | **522** |
| Distinct candidate log keys with multiple calendar years | **52 / 52** |
| Maximum distinct observed original calendar years per nested log | **11** |
| Original `tree` groups observed in long source | **3** |
| A `plot×log` assigned inconsistent `tree` types across source years | **0** |
| A `plot×log×year` assigned inconsistent `tree` types | **0** |
| Original calendar year values present | **2013–2019, 2021–2024** (11 observed calendar labels) |
| Community original candidate first-column sample IDs | **525 distinct / 525 rows** |
| Community original nominal species-data fields excluding sample-label column | **297** |
| Trait table original header cells | **20**, with literal source `host_tree` (19th) and `body_length` (5th) |

The exact source years are not 11 independent generations or 11 independent forests. Three deadwood host tree types across 52 nested deadwood logs do not mean three independent study networks. The original paper used trap relocations along the same trunk and a one-year delayed spruce deployment; source `year` cannot be treated as identical exposure age among tree species without this original event-level temporal crosswalk.

**Critical original-source discrepancy:** the original community file has **525 candidate source IDs**, whereas the original species-long table has **522 distinct `plot×log×year` combinations**. These totals differ by **three**. It is **not** allowed to drop those three rows, invent trap zero/absence, or join original species values by row position. The original long-table occurrences may be multiple species/event lines within one log×year. Only the original authors' method code or explicitly defined mapping can verify the 525-to-522 comparison. [Outcome-blind author R code reconciliation prespec](FOREST_BEETLE_LETTENMAIER_12YEAR_MATRIX_522_525_AUTHOR_CODE_GATE_PRESPEC_20261115.md), original scripts `GAM.R` and `NMDS.R` pinned by original Zenodo checksums. A separate GitHub CI checks source-key construction, with NO new biological scores.

## Real scientific opportunity and novelty ceiling
The presence of literal `host_tree` as a published source trait column is important: unlike inferring broadleaf/conifer affinity from scientific names, a source-author trait definition exists. However **its category values, matching accuracy to beetle species and interpretation have not yet been audited**. No claim has been made that this trait is identical to the broadl/conifer/both categories in the Finnish Burner 2022 dataset.

The prior original JAE authors already tested differences among tree hosts, decay time, taxonomic and functional biodiversity; these are NOT newly discovered by Structural. A distinct ecological question may involve **whether functional resource-use channels remain stable when taxonomic communities replace across years within the same individual logs**, conditioned on host tree identity and source year/exposure age. Such a model requires a new pre-outcome specification and uncertainty clustered at original physical log/plot level, never naive 522 observations as independent forests. A result from one original German log experimental source would remain one independent study, NOT global forest macroecology/causal landscape generalization.

No ecological effect nor model test has been executed on this source. Older Finland 142-site resource-guild original spatial heldout +0.00024237/p=.015, Finnish physical-site guild null +0.035237, Burner three-country +0.091059, PREDICTS +0.0942, NEON canopy +0.0349/p=.1759 non-support, BALA and GEB holds all unchanged. PR #469 remains Draft, no eBird/TinyFish.


## 2026-11-15 後続の原本ID対応判定（初期522 vs 525の解消ではない）

著者 `GAM.R` / `NMDS.R` の一次コード監査と、生物値未読で事前固定した `plot,log,tree` の6順列を元行列IDの先頭3要素へ照合した。[Actions #43697804270](https://github.com/zuizui0223/Structural/actions/runs/43697804270) **SUCCESS（source-method計算成功）**では、最も一致する `plot–log–tree–year` ですら **359/522**、元long-only **163**、群集行列-only **166**、残り5順列は一致0。候補が元522組全部に一致するケースは**0**だった。したがって見かけの3行差だけから「3行を除けば全対応」と結論するのは誤り。生物応答スコアは未実施、著者定義IDの一対一対応は未認証であり、現時点のゲートは **SOURCE_CROSSWALK_NOT_UNIQUELY_IDENTIFIABLE_NO_SPECIES_SCORING**。

[一回限りの全6候補と残差の結果、次の科学的停止条件](FOREST_BEETLE_LETTENMAIER_12YEAR_SOURCE_CROSSWALK_HOLD_RESULT_20261115.md)を参照。前掲の初期記録（522 / 525 / trait `host_tree`）は保持しつつ、**異なる原本に対応していると確認できない限り甲虫群集と元丸太環境を結合しない**。
