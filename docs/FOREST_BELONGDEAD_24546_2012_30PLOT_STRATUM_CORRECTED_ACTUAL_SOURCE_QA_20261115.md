# BELongDead × 2012 ambient deadwood: unit-safe original resource source QA completed (2026-11-15)

## Result and current scientific decision

**The BExIS 24546 original 2012 deadwood inventory has a verified, reproducible, source-original 30/30 physical-plot join to independently published experimental BELongDead beetles BExIS 31123.** Across those exact 30 field plots, the original inventory contains **1,385 wood-item records**, with 13 distinct source `spec1` tree-code categories; `spec2` coniferous/deciduous can be read for **1,381 / 1,385 items** (644 Conif, 737 Decid, 4 missing), with all 1,385 source items assigned an author-defined 1–5 decay class. No source 31123 beetle species/capture outcome values have been read to estimate any ecological effect.

**Newly corrected source quality result:** a precommitted first QA stopped on **574 source records** outside source `DWV` author-description's `T/L/T7/S` unit categories. A separately precommitted categorical source-only check found the original data **use `L7`, not `T7`**, and author `stratum` source field explicitly describes `L7` as downed deadwood 7–25cm, whereas the `DWV` *unit* author text separately spells `T7` for transect-level volume per hectare. This is an **unresolved original publisher codebook discrepancy**, not permission to silently relabel L7 as T7 nor assign its volume unit. Corrected unit-aware source QA preserved **all 574 L7 items** for taxon and decay metadata, but **did not sum or convert the L7 DWV quantities**.

### Actual unit-separated source observations, corrected CI

| Actual original `stratum` code | Publisher's source substrate meaning | 2012 wood items in 30 experimental plots | Physical plots with source item rows | Original numeric DWV finite | DWV unit/status |
| --- | --- | ---: | ---: | ---: | --- |
| **T** | Standing wood >25cm | **59** | **17** | **59/59** | **m³ per source item** |
| **L** | Downed wood >25cm | **286** | **26** | **286/286** | **m³ per source item** |
| **L7** | Downed wood 7–25cm | **574** | **30** | **574/574** | **UNVERIFIED: author's DWV description says `T7`, not `L7`** |
| **S** | Stumps >7cm | **466** | **28** | **466/466** | **m³/ha in author's transect measurement description** |
| **Total** | *Mixed survey methods/physical units* | **1,385** | **30 unique** | **1,385/1,385** | **DO NOT TOTAL ACROSS STRATA** |

No `T7` source records were found. No unexpected stratum categories remain **after fixing the original actual-source category enumeration without seeing any beetle outcomes**. `Vharv` is separately harvested/stump-derived wood volume reported in m³/ha, NOT another piece of ambient `DWV` to add.

The completed original-source QA also yielded anonymous descriptive distributions of **per-plot observed item sum only within validated units and plots with observed items** (NOT a complete 30-plot population mean, and NOT a measured 30-plot all-strata total):
- **T:** 17 plots with observed source items; median sum of observed items **2.107538 m³**.
- **L:** 26 plots with observed source items; median sum **3.079716 m³**.
- **S:** 28 plots with observed source items; median sum **6.119688 m³/ha**.
- **L7:** 30 plots with item rows, 574 finite values, but **NO source plot volume sum** due to unresolved denominator. Numeric finiteness does NOT resolve source unit.
- A forest plot with no source rows for an individual stratum has **NOT** been inferred to have zero resource. The 2012 snapshot and source sampling-method coverage cannot be assumed continuous over the original beetle 2010–2017 capture years.

The original `spec1` author field description lists taxonomic tree-code categories, whereas `spec2` is explicitly `Conif/Decid` classification (NOT an extra independent tree piece). There are 13 distinct original ambient `spec1` categories **and** 13 offered BELongDead experimental `TreeSpecies` labels, but mere equality of their category counts does **NOT** establish a one-to-one taxon dictionary. No experimental host/ambient source woody taxon identity mapping has been inferred from those counts.

## Audit evidence, reproducibility and chronology

1. **Original tagged published version and exact physical source PlotID:** [GitHub Actions #43708115836 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43708115836), article-licensed public BExIS 31123 `/api/data/31123/tag/1` (8,103,493 bytes; original SHA256 `73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e`) and 24546 `/api/data/24546/tag/1` (417,351 bytes; original SHA256 `5a02350e4f1e364302dea20ca25281e65f2158d318d9fbcef56be2fe6d57786a`); each is byte-identical to the previously audited latest source. Original exact source plot-ID intersection **30 / 30**. The BExIS tagged release number 1 is distinct from the original internal version (24546 internally version=2).
2. **Source variable dictionary, units and meanings:** [CI #43708549515 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43708549515) original publisher `GET /api/DataStatistic/24546` with 12 original variable name/description/type/unit records; [CI #43709126694 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43709126694) fixed-five-field original short descriptions and mixed-unit `DWV` caveat; no original site/taxon/measurement values redistributed. Previous short-metadata length source STOP #43708799629 preceded source-only uniform clipping, not biological model choice.
3. **First prebiological item QA [#43709485162 SUCCESS of source STOP](https://github.com/zuizui0223/Structural/actions/runs/43709485162)**: source report correctly identified **574** original unexpected category values against `T/L/T7/S`, stopped unit pooling. [Separate original author source strata check #43709724559 SUCCESS](https://github.com/zuizui0223/Structural/actions/runs/43709724559) identified **L7** and recovered the publisher's explicit stratum definitions.
4. **Source-only correction prescribed before any organism response**, no alternate guild/predictor fitting; [**corrected original 30-plot BExIS24546 stratum numeric QA CI #43709866459 SUCCESS**](https://github.com/zuizui0223/Structural/actions/runs/43709866459), aggregate artifact **14159623201**, source-only artifact ZIP SHA256 **`607a6d775b5e91c93ac815311a2d69f5fa434d5760213edbeb36dfbfde285c8f`**. All **1,385 original DWV values** were source-finite. Source status `SOURCE_2012_WOOD_RESOURCE_BY_STRATUM_30PLOT_QA_COMPLETE_NO_BIOLOGY`.
5. Method/code: `analysis/forest_macro_global/belongdead24546_2012_stratum_unit_source_quality.py`, workflow `.github/workflows/forest-belongdead24546-30plot-stratum-unit-sourceonly.yml`; [original unit-gated prebiology protocol](FOREST_BELONGDEAD_24546_STRATUM_UNITS_30PLOT_RESOURCE_QA_PRESPEC_20261115.md); [independent source author 574 code diagnostic protocol](FOREST_BELONGDEAD_24546_UNEXPECTED_574_STRATUM_DIAG_PRESPEC_20261115.md); publisher codebook output `analysis/forest_macro_global/belongdead24546_author_field_descriptions.py`.

**No original 31123 beetle capture count, species, traits, host preference, temporal turnover, ecological p or causal coefficient has been opened or scored in any of these audits.** All original field data stayed in ephemeral runners; no original individual plot IDs, wood taxon code values, raw field records, coordinates or trap IDs were reexported.

## Scientific next action and explicit stopping rule

The proposed novel functional-resource question is whether local background woody substrate availability, measured at the **same physical plots**, gates the association of experimentally offered 13 types of host deadwood with local captured saproxylic beetle functional channels. That interaction cannot yet be estimated without an independently specified **original 2012 plot-level per-host resource denominator/sampling area**, a documented **L7/T7 source unit correction**, a legitimate `spec1`↔`TreeSpecies` taxon mapping and **complete capture opportunities**. The 31124 author complete-log view introduces 15 otherwise parent-matched novel `TrapID` strings, and 31123 records alone do not establish every surveyed trap×year with zero beetles.

**Do not**: infer zero ambient resource for unrecorded stratum plots, reinterpret L7 as m³/ha without authors' correction, pool item m³ with transect m³/ha, treat 2012 ambient inventory as concurrent to all 2010–2017 captures, treat 379 experimental logs as independent forests, treat captured-flight adults as direct larval wood use, assume categorical counts imply homologous tree taxa, or rerun known prior-author host preference/richness effects as independent novelty.

**Preserved prior evidence:** original Finland142 forest Host_tree label-null D=+.035237, local deadwood VD10 blocked prediction ΔHellinger²=+.00024237/conditional p=.015 (small, observational), three-country Burner event label-null D=+.091059, PREDICTS 39-study taxonomic β replacement +.0942, NEON static canopy height contrast +.0349/10m/p=.1759 non-support, BALA/GEB original holdouts unchanged. PR #469 remains **Draft/unmerged**, no eBird or TinyFish.
