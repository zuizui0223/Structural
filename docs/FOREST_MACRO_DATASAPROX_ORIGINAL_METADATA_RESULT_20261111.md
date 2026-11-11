# DATASAPROX original source: actual sampling hierarchy, vertical support and scientific HOLD (2026-11-11)

## Decision: real metadata audit completed; forest-vertical biological response NOT admitted

Publisher-original DATASAPROX v1.6 (IPT, CC-BY-4.0) was downloaded in GitHub Actions and **675,525 original Occurrence-core rows** were streamed using only metadata-whitelisted fields. There was **no species, taxon-incidence, abundance, movement or ecological-effect scoring**. The previously created schema-only gate is now supplemented by actual source-native event-ID, original plot, height-stratum, month, trap-model, bait, colour, treatment and sample-duration diagnostics. The frozen **same-treatment response gate remains a scientific STOP**. A separate, explicitly exploratory post-QA eligibility screen quantifies why.

- Canonical CI: [#43035358400](https://github.com/zuizui0223/Structural/actions/runs/43035358400), **SUCCESS**, 11 synthetic source-blind tests passed; artifact ID **13862373043**, digest SHA256 `78a17e5137d8d0d3bed1b043e04b7f48067f6450c009c4bc5af1e93d27e38e14`.
- Exactly downloaded publisher original archive SHA256 **`4163a2f8f72d756e74f64319b8e199b284ecc6414196147e4465d342d7dcb6d0`**. Original release https://ipt.gbif.fr/archive.do?r=datasaprox&v=1.6 . Source UUID `d050a143-2e62-4908-9d9e-a7f541eab94d`.
- Source-wide published totals (**not vertical denominator**): 675,525 occurrence records, 66,202 field samples, 8,969 coordinates, 2,039 beetle species, 21 providers and 485 projects. Those published denominators are not 66,202 independent paired plots. This metadata audit identified **65,642 nonempty producer×datasetName×eventID source keys with occurrence rows**, which must not be assumed to include zero-capture source samples.
- Code: `analysis/forest_macro_global/datasaprox_source_metadata_gate.py`; tests: `analysis/forest_macro_global/test_datasaprox_source_metadata_gate.py`; CI: `.github/workflows/forest-macro-datasaprox-original-schema.yml`. The Draft PR is #469, not merged.

## Source data identity and collision audit

| Metadata property | Real-source result |
| --- | ---: |
| Original occurrence rows metadata-streamed | 675,525 |
| Distinct original source event keys among observed rows | 65,642 |
| Conflicting source event keys | **1,133** |
| Rows disagreeing with their key's first seen sampling descriptor | **6,395** |
| Disagreements in stratum (after corrected source codebook) | 873 |
| Disagreements in colour | 5,301 |
| Disagreements in duration / treatment / trap model | 349 / 444 / 156 |
| Original distinct source event keys retained after excluding **all** 1,133 conflict keys | **64,509** |

These disagreement categories overlap; their sum is not a count of affected rows. The initial exploratory parser recognized only some height labels; the source-only codebook audit discovered nine original literal labels: lower, upper, canopy, supra canopy, infra canopy, upper canopy, understorey, lower canopy, intermediate. The corrected parser assigns 358 retained keys to upper and 305 to lower; 63,846 remain unclassified. Across the full observed event-key universe, only 751 source keys declared any nonempty stratum at all (before conflict exclusions). Thus 99% of the source's field samples cannot be turned into height-specific traps through inference.

**Important correction to the first CI:** earlier diagnostic runs reported 1,063 contradictory keys / 5,968 rows and 0 same-plot pairs. Those results were computed with an incomplete source stratum dictionary and are **superseded** by the source-verified nine-label v0.2 parser. Do not use the earlier denominator or claim a 0 plot population-wide vertical sample.

The raw strict event-key conflict remains `STOP_CONFLICTING_AUTHOR_EVENT_METADATA`. The 64,509-key subset is a separate post-schema metadata QA diagnostic, **not** an approved new primary cohort.

## Progressive source-defined matching without species responses

Use source producer×project identity plus original `ID_plot`. Every stage counts nonindependent source-coded groups; plots and projects are deduplicated separately. Stratum must be explicitly recorded, not inferred from coordinates.

| Gate | Paired groups | Source project×plot keys | Distinct source projects |
| --- | ---: | ---: | ---: |
| Same original source project and plot, irrespective of season/method | 49 | 49 | 5 |
| Plus year/month and exact original trap model/type | 159 | 46 | 4 |
| Plus identical original `ID_condition` treatment code | **2** | **2** | **2** |
| Plus identical bait/colour and comparable original 7–35-day effort (≤7-day difference) | **1** | **1** | **1** |

Of 159 project×plot×month×method comparisons, **157 had disjoint nonempty `ID_condition` codes between upper and lower**, and **2 had no declared treatment code in either layer**. Thus no universally same-treatment multi-project forest macroecological response can be scored from the present rules. This is a source-method estimability finding, **not a null ecological result**.

### Source-only alternative diagnostic: same methods/effort, condition role unresolved

When `ID_condition` alone is *temporarily not conditioned on* for a method-compatibility diagnostic (while all original plot, period, trap model/type, bait/colour and effort criteria remain), the input contains:

- **87 nonindependent paired project×plot×period units**
- **45 distinct source project×plot keys**
- **three source project identities**
- Anonymized original project support: project 1 **24 physical plots / 24 periods** (one source treatment code unique to each layer); project 2 **20 plots / 62 periods** (two source treatment codes per layer, non-overlapping upper versus lower); project 3 **1 plot / 1 period** (both layers have empty treatment codes).

This **does not pass the originally frozen same-treatment evidence gate**. Source-provided `ID_condition` is defined as *treatments of the sampling design*, not confirmed merely to encode sampling height. If it labels separate experimental treatments, the attractive 45-plot number is height×treatment confounding. If some codes encode height directly, that must be demonstrated from the **original source projects' methods documentation** before constructing a legitimate height-only contrast. Distinct `datasetName` keys are not yet verified independent forest networks or regions. The three projects are not three independent biomes, and the third supplies only one physical plot.

The source data paper explicitly warns that individual original projects may focus on restricted beetle taxonomic subsets and provides a project-level partial-versus-complete community summary (Table 7). A community response cannot be promoted until those three candidate source projects' taxonomic scopes, sampling efforts, field hierarchies and actual trap protocols are crosswalked. **Original species/taxon response remains unopened.**

## Required next independent original-method gate (no outcome fishing)

1. Source-publication crosswalk for the two substantial matched projects (24 and 20 plots) and the one-plot third project: verify whether original `ID_condition` reflects *height only* or independent experimental treatment.
2. Compare source author-defined independent physical forests, plot nesting, repeated seasons, species identification/taxonomic coverage and documented trap effort; each project may require its own source-defined sample grain. Do **not** treat 87 pair-periods as 87 independent forests.
3. If and only if height contrasts are identifiable, register a **new exploratory** project-conditional species-composition test under the validated protocol; keep the strict original STOP and prior source-open/QA history visible, do not re-label it preregistered or globally confirmed.
4. Otherwise declare DATASAPROX vertical response **not identifiable** and leave the existing Thai two-forest field result and Brisbane one-region 10-site result as local observations, not global confirmation.

The BALA original time-series response workflows, the island-mammal holdout and the GEB SCIENTIFIC HOLD are unchanged. No eBird, no TinyFish. No protected mammal source scores reopened and no PR merge or manuscript submission.

## External original documentation

- Bosc et al. (2026), `DATASAPROX: standardised dataset from protocolled sampling of saproxylic beetles in continental France and Corsica`, *Biodiversity Data Journal* 14, DOI **10.3897/BDJ.14.e187021**. Original publicly indexed full paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC12993481/ .
- Original public IPT resource: https://ipt.gbif.fr/resource?r=datasaprox ; original v1.6 archive https://ipt.gbif.fr/archive.do?r=datasaprox&v=1.6 .
