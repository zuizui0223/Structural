# Structural BALA v1.318–v1.319 — Long-term site turnover does not imply spatial homogenization

**29 October 2026 · Original seven-island spatial beta analysis completed. Original biology sealed immediately after the one-shot execution. Source-free arithmetic audited separately.**

## Main result: two distinct dimensions of biological community reorganization

Earlier [BALA v1.316–v1.317](BALA_SEVEN_ISLAND_DETECTION_CONTROL_EXCESS_V1_317.md) found that **same-transect temporal species-identity dissimilarity** exceeded original within-campaign sample-split heterogeneity in both spiders and beetles across **all seven islands** (Pitfall Sørensen excess +0.1908 spiders, +0.2212 beetles). However, that result said NOTHING about whether the forests *within each island* became more alike or more distinct from one another.

**v1.318 directly measures a different quantity:** for every pair of original physical forest transects in the SAME island, compute contemporaneous Simpson species-replacement beta in B1 (1997–2004) and B3 (2019–2022), and compare B3-minus-B1 among the same physical site pairs. These source site pairs are dependent, not independent n. Positive Δ means **greater within-island spatial differentiation**; negative Δ means **biotic spatial homogenization**, conditional on original taxon detections, not proof of actual demographic colonization.

All original v1.313 response-opaque **29 forest transects**, exact original **4,620 equal-sampling Event core IDs** (source SHA256 `39db7c6db04e022b495e233506e9c9774d8e1cf9e2e1c35830bbe6aadce9d6ac`), original Pitfall method, B1/B3 periods and original seven island codes were held fixed. An original 2024 DwCA ZIP SHA256 `4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2` authenticated the one-time response reuse. This is a **separately frozen, post-outcome-exposure observational analysis**, NOT an untouched prospective holdout or new independent dataset.

### Primary spatial-beta result

| Island-equal Pitfall spatial beta, B3 minus B1 | Spiders (Araneae) | Beetles (Coleoptera) |
|---|---:|---:|
| Original independent physical forest sites | **29** | **28** |
| Dependent within-island site pairs | 56 | 49 |
| **Δ Simpson spatial species replacement** | **+0.0224** | **−0.1753** |
| **Δ Sørensen spatial dissimilarity** | **+0.0487** | **−0.1238** |
| Islands with Simpson spatial differentiation | 4/7 | 3/7 |
| Islands with Simpson spatial homogenization | 3/7 | 4/7 |
| Predeclared 9-source-salt ×2 half-effort Simpson sensitivity preserving overall sign | **13/18** | **18/18** |
| Predeclared complementary-half Sørensen sensitivity preserving sign | 17/18 | **18/18** |

**Interpretation:** Beetles showed an island-equal mean shift towards *greater similarity among sampled forests* under the original Pitfall source. The mean shift stayed negative under all 18 source-response-blind half-Event effort partitions. The Spider island-equal Simpson shift was very small and variable (13/18 half-splits positive, five negative); do NOT treat it as a robust new spatial differentiation law.

The seven islands were NOT unidirectional: Beetle Simpson β increased on **Faial, Pico and São Miguel**, and decreased on **Flores, São Jorge, Santa Maria and Terceira**. Spider spatial β increased on **Faial, Flores, São Miguel and Santa Maria**, and decreased on **Pico, São Jorge and Terceira**. Islands with opposite Spider/Beetle spatial Simpson signs were **Flores, Pico, Santa Maria (3/7)**.

### Original island-specific field contrasts

| Island | Spider site n | Spider Δ Simpson | Beetle site n | Beetle Δ Simpson |
|---|---:|---:|---:|---:|
| Faial | 3 | +0.0738 | 3 | +0.1778 |
| Flores | 4 | +0.1597 | 4 | **−0.5603** |
| Pico | 4 | −0.0463 | 4 | +0.0972 |
| São Jorge | 4 | −0.1417 | 4 | **−0.4167** |
| São Miguel | 4 | +0.2028 | 4 | +0.0050 |
| Santa Maria | 2 | +0.0833 | 2 | **−0.4015** |
| Terceira | 8 | **−0.1748** | 7 | **−0.1286** |

The Santa Maria estimate is based on only **one dependent site pair**, so it must not be presented as a high-precision island-wide shift. Across the 7 island sample frames, the effect is heterogeneous; no 7/7 spatial direction claim is justified.

## The non-obvious ecological result: Beetle homogenization can coexist with *increasing* local richness

The frozen original v1.318 source aggregate includes the original source **mean species detected per same physical forest transect** and **within-island pooled detected taxa (source-observed γ, not an exhaustive island species list)** in B1 and B3.

Three of the **four** islands showing *Beetle Simpson spatial homogenization* did so **while their mean local Beetle richness increased**:

| Island | Beetle spatial Δ Simpson | B1 mean taxa/forest transect | B3 mean taxa/forest transect | Observed island source γ B1 → B3 |
|---|---:|---:|---:|---:|
| **Flores** | **−0.5603** | **5.00** | **8.25** | 14 → 16 |
| **São Jorge** | **−0.4167** | **3.00** | **3.75** | 9 → 8 |
| **Santa Maria** | **−0.4015** | **13.50** | **16.50** | 22 → 24 |
| **Terceira** | **−0.1286** | **5.57** | **5.43** | 21 → 21 |

Thus increased α richness is **not sufficient evidence that within-island forest community individuality is being maintained**. A richer site can become more compositionally similar to other richer sites if taxa overlap more. This is not evidence that any specific widespread Beetle species spread or that invasions caused the change; species-level causal attribution and environmental drivers were NOT evaluated.

A complementary weaker pattern occurs in Spiders: **Faial, Flores and Santa Maria** show spatial differentiation while mean local detected richness falls. This reinforces that net richness, within-site temporal turnover and between-site spatial similarity are **three different quantities**.

**Metric caution:** Faial has a positive spatial Simpson replacement Δ for both guilds but a negative spatial Sørensen total Δ. Therefore the sign of a spatial-biodiversity trend can depend on whether one measures species *replacement* or *total pairwise non-similarity*. Avoid calling homogenization from one metric without naming it.

## Original observation, independent validation and detection limits

The BALA field data provide an original taxon-source observation, but the model was designed *after* v1.314/v1.316 had opened this same source. **This is an exploratory new estimand on already exposed published data.** The matched Pitfall Event count controls source sampling opportunity. Nine hash-defined split partitions are based on the same original events and do not estimate occupancy detection probabilities; the 18 half-splits are NOT independent biological experiments.

Canopy beating produced **Spider Simpson spatial Δ −0.0579** while Pitfall Spider Δ was +0.0224; the difference is observational and may reflect different sampling microhabitats and arthropod guild representation. Canopy Beetle failed the fixed source site-pair eligibility (**22 source sites**) and remains **scientifically STOPPED**. No method-wide or forest-region-wide universal guild pattern is claimed.

This study cannot identify actual immigration, local species extinction, an invasive species mechanism, habitat or fragmentation causal driver, reserve management performance, or cross-archipelago generality. There was no spatially independent geographic holdout and no fragment randomization. Original 2026 BALA abundance/biomass/richness stability is **prior published work**, not newly verified with independent observations.

## Executed, reproducible scientific evidence

- Original field-source **v1.318** [GitHub Actions #40806865705](https://github.com/zuizui0223/Structural/actions/runs/40806865705) — **SUCCESS**, 4 synthetic tests. Original Event=10,379, Occurrence=63,904, source matched 29 physical sites and 4,620 originally frozen Event sampling units. Original ZIP artifact **#12867999807**, digest SHA256 `8baad51d7d9162f915c9040e54dc622dc30ae55933b69c11fc187fd5474f6138`, original full result JSON SHA256 `f4e61ddbbd255d3a35a46fb0254273889516984b82479b3949e5edd79853af02`.
- **Immediately sealed v1.318 one-shot original source scorer**: `.github/workflows/bala-spatial-beta-original-one-shot-v1_318.yml` is read-only with no push or PR automatic scoring. Earlier original source v1.314 and v1.316 scorers also remain SEALED.
- Source-free permanent numerical aggregate: `development/bala_spatial_original_result_freeze_v1_318.json` (no original site IDs or species names).
- Separate source-free **v1.319** [GitHub Actions #40807508361](https://github.com/zuizui0223/Structural/actions/runs/40807508361) — **SUCCESS**, 4 tests, original biological source Event/Occurrence rows reopened **0**, source-free artifact **#12868328388**. All 7 source island signs, 56/49 dependent site pairs, original source SHA, 18 half-split sign intervals, 3 homogenization-with-rising-richness islands, metric disagreements and canopy Beetle STOP are inspected for exact agreement.
- Original source and prior source study: [BALA published data DOI 10.15468/rpdkx9](https://doi.org/10.15468/rpdkx9), [Pozsgai et al. 2024 Scientific Data](https://doi.org/10.1038/s41597-024-03174-7), [Pozsgai et al. 2026 Scientific Reports](https://doi.org/10.1038/s41598-026-57146-5).

**Science conclusion for Structural:** Within seven island forest sampling contexts, arthropod species identities restructured over decades, but this did NOT correspond to one universal spatial homogenization direction. Beetle assemblages became on average more spatially similar and that tendency persisted across fixed sampling half-splits, **including several islands where local Beetle taxon richness increased**. Spiders displayed more mixed spatial changes. The measured quantities are observational species-detection community patterns, not demographic rescue or causal drivers.

**Status:** The BALA original-source spatial beta branch is **scientifically closed at v1.319**; no further outcome-selected reanalysis of the same 29 original transects. Progress toward broad island ecology requires genuinely independent sites/other archipelago with predesignated repeated plots and detection/fragment metadata. GEB original mapped-mammal **scientific HOLD**, zero pristine confirmatory admissions, original protected mammal/BioTIME/RLS/S2–S4 unopened, eBird unused.
