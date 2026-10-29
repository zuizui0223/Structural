# BALA v1.316–v1.317: Long-term community replacement exceeds same-period sampling heterogeneity across seven islands

**Original source executed 28 October 2026; source-free numerical audit 29 October 2026. Observational taxon-detection contrasts, NOT verified biological colonization/extirpation or independently replicated across archipelagos.**

## Central ecological answer

**In the same source-identified Azorean native-forest transects, between-campaign changes in detected arthropod assemblage membership are systematically larger than differences obtained by dividing the original sampling Events into disjoint half-effort samples within each campaign.** This pattern holds for **both spiders and beetles in all seven surveyed island contexts** under the fixed ground pitfall method.

The earlier BALA v1.314 original-source result documented within-transect species replacement despite limited net species richness change. But non-detection and source trapping heterogeneity could have produced some apparent species change. The separately fixed v1.316 falsification made this alternative measurable: compare the B1 (1997–2004) and B3 (2019–2022) source communities **at the same half-sample capture opportunity** with within-campaign B1A/B1B and B3A/B3B pseudo-turnover. Each selected original Event site×period×method was assigned to two nonoverlapping halves by SHA256(source Event ID + one of nine predeclared salts), never based on species names or response direction. Nine salts are sensitivity re-partitions of the SAME biological source, not independent biological experiments.

### Source-observed pitfall comparison

| Island-equal, same-source original forest transects | Spiders / Araneae | Beetles / Coleoptera |
|---|---:|---:|
| Independently identified physical transects passing four-half support | **29** | **26** |
| Within B1/B3 period half-sample Sørensen dissimilarity | **0.2951803** | **0.4232422** |
| B1-to-B3 equal-half cross-period Sørensen dissimilarity | **0.4859558** | **0.6444510** |
| **Cross-period minus same-period Sørensen excess** | **+0.1907755** | **+0.2212088** |
| Within-period Simpson replacement | **0.1657659** | **0.2795186** |
| Across-period Simpson replacement | **0.3334160** | **0.5243621** |
| **Excess Simpson replacement** | **+0.1676501** | **+0.2448435** |
| Original islands with positive excess Sørensen/Simpson | **7/7** | **7/7** |
| Original matched source transects with positive Sørensen excess | **26/29** | **25/26** |

The original same-period half-sample mismatch itself is sizeable: the ratio *within-period mean / across-period mean* equals **0.607 for spiders** and **0.657 for beetles**. **This ratio is not a percentage of ecological change "explained by" detection bias**; the half-samples can also differ in microhabitat use, taxonomic detectability, spatial sampling and genuine within-period heterogeneity. The positive excess indicates that **those observed within-period differences alone are an incomplete description of the source's long-term species reorganization**, not that all alternative observation processes were removed.

### Island-level pattern and original source physical-site support

Every island-level original observed excess was positive in both taxonomic guilds, but the magnitude was heterogeneous.

| Original island | Spider sites positive / scored | Spider excess Sørensen | Beetle sites positive / scored | Beetle excess Sørensen |
|---|---:|---:|---:|---:|
| Faial | 3/3 | +0.2636 | 2/2 | +0.2236 |
| Flores | 3/4 | +0.1633 | 3/3 | +0.2052 |
| Pico | 4/4 | +0.2277 | 4/4 | +0.2650 |
| São Jorge | 3/4 | +0.1118 | 4/4 | +0.1709 |
| São Miguel | 4/4 | +0.3141 | 4/4 | +0.1877 |
| Santa Maria | 1/2 | +0.0791 | 2/2 | +0.2015 |
| Terceira | 8/8 | +0.1758 | 6/7 | +0.2946 |

Across the source island means, the Beetle excess Sørensen value exceeds the Spider excess in **5/7** islands. Do not infer a universal guild effect or a formal species-lifespan mechanism. Beetles had 3/29 original sites fail the separately declared four-nonempty-half support rule; the Spider source retained 29/29. These numbers are real site-level support counts, not 9×29 independent temporal tests.

The prespecified canopy-beating method provided additional descriptive Spider evidence (7 islands/29 plots, excess Sørensen **+0.111947**), but the canopy-beating Beetle endpoint **scientifically STOPPED** at only 13 source sites. The result cannot be generalized as a full two-guild/two-method effect. Site-by-species source guild variation and capture method remain relevant.

## Interpretation: new result versus 2026 BALA prior work

**New derived observation (within the same public BALA dataset):** site-level, long-term community identity change in arthropods is greater than the site's contemporaneous half-sample heterogeneity under a fixed equal-capture-effort comparison, recurring across seven sampled Azorean islands. It supports detecting assemblage reorganization beyond a simple sampling inconsistency and complements the earlier v1.314 result that 23/57 site×guild source comparisons exhibited balanced replacement with at most one species of net richness change.

**Already published by Pozsgai et al. (2026):** relatively stable overall arthropod abundance, biomass and richness and species-specific changes. Their conclusions are PRIOR ART, not independent confirmation or an original Structural discovery. Sources: [BALA GBIF original data DOI 10.15468/rpdkx9](https://doi.org/10.15468/rpdkx9), [Pozsgai et al. 2024 Scientific Data DOI 10.1038/s41597-024-03174-7](https://doi.org/10.1038/s41597-024-03174-7), [Pozsgai et al. 2026 Scientific Reports DOI 10.1038/s41598-026-57146-5](https://doi.org/10.1038/s41598-026-57146-5).

**Not demonstrated:** exact extinction/colonization events, demographic island rescue, changes in physical species population survival, island isolation as a driver, natural-forest management effectiveness, climate causality, or full species detection probability correction. Epochs span different years/season windows; within-period half splits are an approximation, not occupancy modelling. Taxonomic reidentification and source species-rank heterogeneity can contribute. This is one archipelago and the same original BALA observations, not a genuinely disjoint replication of the 2026 source.

## Scientific status and one-shot evidence

- Original source: University of Azores BALA original archived v1.0, exactly **10,379 Event and 63,904 Occurrence** rows, source ZIP SHA256 `4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2`.
- The **29 original transects**, seven island identity groups, **4,620 original Event keys** and exactly 1,540 selected Event sampling opportunities per campaign (ground Pitfall 781 / canopy beating 759) were frozen from response-opaque original Event code in v1.312–v1.313 **before** original v1.314 species response access. Original selected Event SHA256 `39db7c6db04e022b495e233506e9c9774d8e1cf9e2e1c35830bbe6aadce9d6ac`.
- Original v1.314 one-shot community species result: [GitHub Actions 40615946292](https://github.com/zuizui0223/Structural/actions/runs/40615946292), and v1.315 audit [40616803067](https://github.com/zuizui0223/Structural/actions/runs/40616803067). Original v1.314 biological source scorer **SEALED**.
- **v1.316 original retrospective biological falsification executed once:** [GitHub Actions #40636604430](https://github.com/zuizui0223/Structural/actions/runs/40636604430), all five synthetic tests passed, all exact source/Event/Occurrence identity and biological count checks passed, original artifact ID **12793228108** (ZIP SHA256 `b467dc1747d116a6d4f291102f2d0b405c760905c254f0e6e7dd21b76ca1d0f0`; inner JSON SHA256 `1a65cb237271560b56484e992eca76ee6bf082048c55a6f3f68eb0f5a2436871`). **Immediately thereafter, the v1.316 original-source workflow was SEALED:** no push/PR triggers and no further automatic original taxonomic re-execution.
- Permanent source-only original aggregate: `development/bala_within_campaign_detection_original_result_freeze_v1_316.json`, derived without re-opening original Event/Occurrence after v1.316.
- **v1.317 source-free consistency validation**: [GitHub Actions #40804529745](https://github.com/zuizui0223/Structural/actions/runs/40804529745) **SUCCESS (4 tests)**; verifies all source island means and numbers, 7/7 both guilds, 26/29 Spider and 25/26 Beetle site directions, and that the canopy Beetle endpoint remains STOP. Only compact frozen original numerical aggregates read, original biological rows reopened **zero**.
- Durable v1.317 analysis: `scripts/bala_between_within_sourcefree_audit_v1_317.py`, contract `development/bala_within_period_excess_sourcefree_protocol_v1_317.json`, tests `tests/test_bala_between_within_sourcefree_audit_v1_317.py`.

**Final claim:** *Long-term restructuring of observed species assemblages exceeds within-campaign half-sample heterogeneity in both spiders and beetles across each of seven sampled Azorean islands; community membership is an independently informative monitoring dimension beyond richness, but the source data do not identify biological extinction, source–sink exchange or a causal isolation mechanism.*

GEB original mapped-mammal manuscript **SCIENTIFIC HOLD** retained, zero new truly prospective confirmatory systems, eBird unused, protected original mammal/BioTIME/RLS/S2–S4 response files unopened.
