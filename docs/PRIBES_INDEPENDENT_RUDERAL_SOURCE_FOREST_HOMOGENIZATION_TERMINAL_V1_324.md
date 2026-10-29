# Structural PRIBES v1.320–v1.324 — Independent disturbed-habitat source-pool hypothesis NOT supported as an island-forest homogenization explanation

**29 October 2026 · Public independent field-source analysis, original scored once and sealed. Six island contexts, 72 independent PRIBES ruderal sites, one fixed BALA forest spatial-beta response per island.**

## The ecological question

The [BALA long-term original seven-island forest study](https://github.com/zuizui0223/Structural/blob/science/bala-multi-island-composition-v1-310/docs/BALA_SEVEN_ISLAND_SPATIAL_HOMOGENIZATION_RICHNESS_DECOUPLING_V1_319.md) found that observed forest Beetle communities became spatially more similar on average over decades (island-equal B3 minus B1 Simpson spatial beta **−0.1753**), even as mean locally detected Beetle richness rose on Flores, São Jorge, and Santa Maria. The previous same-data analyses did NOT identify any incoming taxa, specific dispersal, environmental cause or source–sink dynamics.

**An independently sampled source-side prediction:** if a geographically widespread pool of introduced Beetle taxa in nearby human-modified habitats drives the forest homogenization, islands with stronger within-island sharing of introduced Beetles among disturbed source habitats should tend to have stronger historical forest Beetle spatial homogenization.

To test a narrow observable implication, we used the **independent** published PRIBES disturbed coastal/ruderal survey (original data DOI [10.15468/xch3zq](https://doi.org/10.15468/xch3zq), [2026 data article](https://doi.org/10.3897/BDJ.14.e188056)), not a reanalysis of sealed BALA species identities. PRIBES samples ruderal vegetation by one-hour vegetation beating; BALA forest communities were sampled by Pitfall. **Methods, habitat and years differ.** This is an island-level contextual association test, not measured movement or a causal source flux.

## Original source gates before species data

- Original PRIBES v1.3 ZIP SHA256 `9b4eb77c15de7a900c391a17e781a99521f00d9b2fe433807607ebe462235b6e`, with **80 original Event** and **2,836 original Occurrence** rows. v1.320 [meta-only run #40814509433](https://github.com/zuizui0223/Structural/actions/runs/40814509433) PASS; taxon/site body rows opened **zero**, Event and Occurrence contain source locationID, habitat, sampling method/effort, order, taxonRank and establishmentMeans.
- v1.321 strict whole-80-Event equal-effort original gate [run #40814895699](https://github.com/zuizui0223/Structural/actions/runs/40814895699) **scientific TERMINAL**: one original Event lacks interpretable sampling effort; some original Events are 30 minutes, versus published standard one-hour protocol. This cannot be labeled a fully equal-effort original survey.
- A **different response-blind v1.322 subset** was fixed explicitly *after Event metadata exposure but BEFORE any taxonomic original response*: only exactly **one-hour vegetation-beating Events**, source-coreID-first per unique exact original island+locationID key. This restricted six-island source survey to **72 independent physical sites**. Source [run #40815472790](https://github.com/zuizui0223/Structural/actions/runs/40815472790) **SUCCESS**, four tests, source site-inclusion SHA256 `4258962fe50796bde5a11a60f9f98736d6c8a8e59db8cca3b3ddcc0d6276b14c`. Three original source Events were not eligible for the one-hour frame (one unknown effort in Faial and two non-one-hour Events in Terceira). Earlier all-Event v1.321 remains TERMINAL, not rescued.
- Six overlapping island codes, fixed before species access: **Faial, Flores, Pico, Terceira, São Miguel, Santa Maria**. PRIBES includes Corvo, but this is not among the original repeatedly sampled seven BALA forest islands; BALA includes São Jorge, which PRIBES did not sample. Original BALA source species/Events were **not** reopened.

## Source-observed independent island comparison

The v1.323 protocol, fixed before PRIBES first occurrence-body access, limited source taxa to author `scientificName` at species/subspecies rank with exact author-derived `establishmentMeans` introduced/native/endemic. Unknown status was NOT imputed, and source morphospecies without resolved ranks were NOT called alien. The source selected sites were determined entirely by Event metadata; taxon names could not choose sites.

**One-shot original PRIBES [GitHub Actions #40816387637](https://github.com/zuizui0223/Structural/actions/runs/40816387637) SUCCESS**, with four source-free synthetic tests PASS. The original 2,836 Occurrence rows all linked to original Events; among the selected six-island source cohorts, Spider+Beetle detected source rows were 1,294, of which 1,226 were eligible named species/subspecies. Exact statuses classified 701 introduced, 331 native, 157 endemic source records; **37/1,226 (3.02%)** had unresolved status and were excluded under the predeclared 20% ceiling. Zero within-island conflicting named-taxon origin classifications.

### Six-site-group original observations

Higher Jaccard means more widespread *shared* named taxa among the original one-hour PRIBES disturbance-habitat sites (among site pairs with nonempty taxon detections). This is not a measure of numbers of beetle dispersers entering forests.

| Island | PRIBES 1-hour sites | Year | Disturbance-site introduced Beetle Jaccard | Disturbance-site native/endemic Beetle Jaccard | BALA forest Beetle spatial Simpson Δ (B3−B1) |
|---|---:|---:|---:|---:|---:|
| Faial | 9 | 2021 | 0.2505 | 0.3102 | +0.1778 |
| Flores | 6 | 2020 | 0.1601 | 0.3378 | **−0.5603** |
| Pico | 11 | 2020 | 0.1321 | 0.2143 | +0.0972 |
| Terceira | 15 | 2025 | 0.1798 | 0.3811 | −0.1286 |
| São Miguel | 24 | 2025 | 0.1060 | 0.2302 | +0.0050 |
| Santa Maria | 7 | 2019 | 0.3556 | 0.1667 | **−0.4015** |

The original source had at least **five sites with introduced Beetle detections** per island (range **5–21**), and the original source distinct named introduced Beetle taxa covered **8–20 taxa per island**. Source side pairwise Jaccard is an average of dependent pairs. The cross-source sample size is **six islands**, not 72 replicate BALA forest trajectories.

### Prespecified cross-island test and controls

Fixed biological response: **negative BALA forest Beetle spatial Simpson Δ** (larger number = stronger forest homogenization). Fixed main predictor: PRIBES introduced Beetle within-island source-site similarity. Average-tied-rank Spearman across exactly six overlapping island contexts and **all 6! = 720 exact permutations of the original BALA island outcome labels**:

| Predeclared source-side predictor | Source vs forest homogenization Spearman ρ | Exact one-sided island-label permutation p |
|---|---:|---:|
| **Introduced Coleoptera** (primary) | **+0.142857** | **0.401389** |
| Native + endemic Coleoptera (negative control) | **+0.142857** | **0.401389** |
| Introduced Araneae (secondary) | +0.085714 | 0.459722 |

**The specific introduced-Beetle source-pool hypothesis is NOT SUPPORTED**: the positive correlation is weak, its exact permutation tail is large, and the native/endemic negative control has the **same** rank correlation. A shared native control slope also argues against labelling the weak association an invasive-specific mechanism.

Survey-calendar confound: the originally sampled PRIBES year differs among islands (2019–2025), with Spearman(source introduced Beetle similarity, source year) **−0.441** and Spearman(BALA forest homogenization, PRIBES year) **−0.353**. Each source island was surveyed in a different calendar window; temporal variation and island geography cannot be separated with six observations. No six-island regression adjustment could establish causal evidence.

These results are consistent with earlier 2026 author research suggesting that exotic arthropod functional assembly is often near null expectations, but **our predictor, response and field-source comparison are different**; see [Oyarzabal et al. 2026 Diversity and Distributions](https://doi.org/10.1111/ddi.70265). We are not claiming their original interpretation as a new Structural result.

## What is learned, and what is not

**Source-backed empirical advance:** human-modified ruderal vegetation in all six island contexts contains identified introduced Beetle taxa, but their *within-island spatial sharing* is heterogeneous and has no meaningful monotonic island-level association with the previously observed forest-Beetle homogenization. This rejects the **simple, coarse external-source-pool proxy** as a current explanation of the original BALA forest pattern.

**Not rejected:** true movement, arriving immigrants, disturbance-dependent establishment inside forests, environmental filtering, direct biotic competition, or taxon-specific source–sink effects. The PRIBES study samples canopy/foliage by beating versus BALA ground Pitfall; species often differ in guild and capture, sites are not physically paired, sampling years are unequal, forest response is historic. A negative island-level correlation cannot refute a spatially explicit mechanistic process.

**Next genuine mechanism requirement:** within-island *paired* forest fragment and external source-habitat surveys (georeferenced, matched years, same Beetle guild and effort, detection repetitions), with an independent fragment-quality/landscape buffer covariate. Repeated forest occupancy and nearest source identities must be measured; do not infer them from this six-island aggregate.

## Execution, audit and scientific firewall

- Original source-taxonomy one-shot run **#40816387637**, artifact #12872113954; artifact ZIP SHA256 `c078230ab06ccb9c75caaddcecf8fa8af64147a508e6f22320fda9d01e53d2be`; original result JSON SHA256 `d4ef1bbc23a2f44560a42e1e66a3041697e43f6077a4e0d233e2757a2261765e`.
- After successful original scoring, the original taxon workflow `.github/workflows/pribes-original-six-island-beetle-source-one-shot-v1_323.yml` was **SEALED** as a no-source-read receipt. No subsequent original taxon replay authorized.
- Permanent original-aggregate numerical freeze `development/pribes_ruderal_external_source_result_freeze_v1_323.json`.
- Independent **v1.324 source-free** original-evidence audit: `scripts/pribes_six_island_sourcefree_audit_v1_324.py`, `tests/test_pribes_six_island_sourcefree_audit_v1_324.py` and `development/pribes_external_source_sourcefree_audit_protocol_v1_324.json`; original raw BALA/PRIBES Event/Occurrence rows opened in v1.324 **zero**. Four exact tests PASS.
- Original all-Event PRIBES v1.321 terminal, v1.322 reduced post-Event-QA one-hour cohort exploratory, BALA original v1.314/v1.316/v1.318 biological scorers SEALED, GEB mapped-mammal scientific HOLD, 0 new pristine confirmatory systems, eBird unused, protected mammal/BioTIME/RLS/Macaronesia S2–S4 records untouched.

**Final decision:** close the crude cross-island ruderal-exotic pool explanation as **unsupported**, without post-outcome tuning or implying absent ecological invasion mechanisms. Progress on causal island forest homogenization depends on truly independent site-matched habitat/fragment data, not more permutations of this same six-island panel.
