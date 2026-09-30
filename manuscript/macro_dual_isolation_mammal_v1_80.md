# Island isolation is not one-dimensional

## Source-network information is widespread but attenuates with external isolation

**Draft status:** macroecology manuscript skeleton v1.80. The global mammal analysis is the empirical core. GIFT is retained only as a transparent fresh-attempt boundary and possible nonconfirmatory cross-taxon sensitivity. This draft must not be read as two-taxon confirmation.

## Abstract

Island isolation is usually represented by target-level geography: distance to mainland, surrounding landmass, stepping stones, or generic network position. Yet a focal species experiences an additional axis of isolation—the configuration of islands that are actually occupied by potential insular sources. We asked whether this species-conditioned internal source continuity retained held-out occurrence information after strong controls for environment, island area, current and historical external isolation, generic island-network context, global occupancy breadth, regional prevalence, and direct/diffuse occupied-source proximity. We analysed a global native-mammal incidence system after response-independent exclusion of a contaminated 15-island block and 176 islands overlapping an earlier stress-test dataset, leaving 5,401 islands. Models were trained on 1,275 pilot islands and evaluated on 4,126 held-out islands in 168 spatial blocks across 12 bioregions; the pilot fixed a 79-species universe. Adding graph-path occupied-source continuity to the strongest reference reduced block-weighted held-out log loss (C−R3 = −0.001814; 95% block-bootstrap interval −0.002817 to −0.000997). The direction was negative in 108/168 blocks and in the equal-block mean of 10/12 bioregions. Contrary to an earlier source-pool-handoff hypothesis, the additional gain weakened as current external isolation increased (block-level Spearman rho = +0.287; within-bioregion-centered rho = +0.228, where positive values mean a less-negative C−R3). An independent 318-island mammal stress test showed the same qualitative direction: source-continuity gains were smaller in the extreme-isolation tail. We therefore propose a source-network attenuation hypothesis: internal source topology is informative while occupied insular sources remain sufficiently structured to distinguish targets, but its incremental value declines when extreme external isolation depletes or homogenises that source network. The global mammal analysis is explicitly nonconfirmatory, and a pristine global plant attempt terminated before ecological scoring; the result is therefore presented as a broad macroecological pattern and a falsifiable hypothesis, not as cross-taxon confirmation.

**Keywords:** island biogeography; isolation; source pool; connectivity; species occurrence; spatial validation; mammals; macroecology

## 1. Introduction

### 1.1 Isolation is not one ecological quantity

Island biogeography has long treated isolation as a central determinant of colonisation, persistence and richness, but modern work has shown that isolation itself is multidimensional. Mainland distance, surrounding land area, stepping-stone structure and generic network position can capture different aspects of an island's geographic setting. These are properties of the island system, not of any one species.

A focal species, however, does not encounter every island as an equivalent source. Its effective insular source environment depends on which islands are occupied, how those occupied islands are distributed, and how they are connected through the surrounding archipelago. Two islands with the same mainland distance and generic network position can therefore differ sharply in their relationship to the occupied source network of a particular species.

This motivates a distinction between **external isolation** and **internal source isolation**. External isolation describes response-independent separation from major landmasses and the generic island network. Internal source isolation describes the focal island's relationship to the training-only occupied insular source pool of the focal species.

### 1.2 The key adequacy question

The central question is not whether graph metrics can predict occurrence in isolation. The stronger question is whether species-conditioned source topology retains information **after** a deliberately rich reference has already represented conventional island state and simpler occupied-source context.

Our strongest reference, R3, therefore includes local climate/topography, island area, current and historical external isolation, generic island-network context, global occupancy breadth, species-by-bioregion prevalence, nearest occupied-source distance and diffuse occupied-source pressure. Candidate C adds only graph-path occupied-source continuity beyond that reference.

If C improves held-out prediction, the result cannot be attributed simply to larger islands, closer mainland proximity, more nearby islands, broader species distributions, regional identity, or the mere presence of occupied sources. It would instead indicate that the **configuration** of the occupied source network contains nonredundant occurrence information.

### 1.3 Competing ecological predictions

An earlier working hypothesis predicted a source-pool handoff: internal source information should become more important as external mainland isolation becomes extreme. An independent 318-island mammal stress test did not support that prediction. C improved held-out prediction descriptively in both isolation regimes, but the gain was smaller, not larger, in the extreme tail.

The present global analysis therefore addresses two questions. First, is the internal source-network increment detectable at global scale after a stronger R3 reference? Second, if it is, is that increment concentrated at extreme external isolation or does it change in another direction?

## 2. Methods

### 2.1 Global mammal system and evidence boundary

The source system contained native mammal presence–absence records for 5,592 islands. Before the final macroanalysis, one 15-island spatial block containing a previously exposed occurrence row was quarantined. A response-independent identity audit then matched 176 additional islands to an earlier 318-island mammal stress-test system; all matched islands were excluded from training, targets, source pools and occupancy-breadth denominators. The final population was therefore 5,401 islands.

The global mammal analysis is treated as a **separate nonconfirmatory exploratory macro lineage**. This classification is retained throughout the manuscript. A prior one-shot pilot protocol terminated after species-header access because the physical response schema had been misinterpreted; no pilot occurrence value had been decoded. A later response-free schema audit established that the file contains 5,394 species headers and a headerless routing field in each data row. The exploratory lineage then used this corrected physical schema while retaining the previously frozen population, spatial split, species threshold and R0–R3–C model method.

### 2.2 Spatial split and species universe

The 5,401 islands inherited a response-independent spatial partition based on bioregion × 10-degree blocks. The final split contained 1,275 pilot islands in 50 blocks and 4,126 held-out islands in 168 blocks across 12 bioregions.

The pilot response fixed the focal species universe before held-out response access. A species was retained if it was present on at least 13 pilot islands and absent on at least 13 pilot islands. This yielded 79 focal mammal species.

### 2.3 Reference hierarchy

R0 represented response-independent environmental state using bioregion plus standardised climate and topographic variables.

R1 added log island area, current external isolation and past isolation.

R2 added generic island-network context: nearest-island distance and response-independent neighbour pressure.

R3 added four training-only species-conditioned controls: Jeffreys-smoothed global occupancy breadth, Jeffreys-smoothed species × bioregion prevalence, nearest occupied-source Euclidean distance and diffuse occupied-source pressure.

Candidate C added only two graph-path source terms beyond R3: graph-path nearest occupied-source distance and graph-path diffuse occupied-source pressure.

All source-derived features were recomputed without the complete held-out validation block. Confirmatory rows used only the complete frozen pilot source pool; no held-out occurrence entered a source feature.

### 2.4 Model fitting and held-out prediction

All tiers used the same deterministic pooled ridge logistic regression framework with lambda = 1, no response-based hyperparameter tuning and fixed numerical tolerances. The full R0–R3–C method was frozen before the exploratory pilot response was opened.

The primary contrast was binary log-loss difference C−R3. Negative values favour the graph-path source-continuity candidate.

For each of the 168 held-out spatial blocks, we averaged C−R3 across all eligible island × species cells within that block. The global point estimate was the equal-weight mean of the 168 block means. Uncertainty used 10,000 deterministic block-bootstrap replicates.

### 2.5 Post-hoc nonrescuing diagnostics

After the exploratory primary was frozen, we examined only two descriptive properties of the frozen block scores.

First, geographic breadth was quantified by the number of blocks with C−R3 < 0 and the number of bioregions with a negative equal-block mean.

Second, we linked each block score to the response-independent block mean of current isolation, past isolation and log area. We report equal-block Spearman correlations and within-bioregion-centered Spearman correlations. These diagnostics are explicitly post-hoc and cannot alter the primary status.

### 2.6 Independent 318-island mammal context

An earlier independent mammal stress test used 244 held-out islands and 233 fixed species. Its predeclared primary asked whether the C−R3 gain was larger in the extreme mainland-isolation tail. That contrast failed in the predicted direction, but the frozen descriptive C−R3 values provide an independent qualitative check on whether external isolation amplifies or attenuates source-network information.

## 3. Results

### 3.1 Internal source topology retained global held-out information

Across 325,954 held-out island × species cells, the equal-block global C−R3 estimate was **−0.001814**. The 95% block-bootstrap interval was **−0.002817 to −0.000997**.

Thus the graph-path source terms retained incremental predictive information after R3 had already represented environment, area, current and historical external isolation, generic island-network structure, occupancy breadth, species-by-bioregion prevalence and direct/diffuse occupied-source context.

### 3.2 The direction was geographically broad

C−R3 was negative in **108 of 168 blocks (64.3%)**. Ten of the twelve bioregions had a negative equal-block mean. The two positive-mean bioregions were Neartic and Oceanina.

The strongest negative mean effects occurred in Sino-Japanese, Oriental, Eurasian and Afrotropical blocks, but the overall result did not depend on a single region.

### 3.3 Greater external isolation weakened the source-network increment

Current external isolation was positively associated with C−R3 across blocks (Spearman rho = **+0.287**). The association remained positive after centering both variables within bioregion (rho = **+0.228**).

Because negative C−R3 favours C, this positive association means that the graph-path source-continuity advantage became **weaker** as external isolation increased.

Past isolation showed weaker positive associations (rho = +0.133 overall; +0.173 within bioregion). Log area also showed a positive descriptive association (rho = +0.268 overall; +0.175 within bioregion). These post-hoc quantities are reported as context rather than as independent hypothesis tests.

### 3.4 The 318-island stress test pointed in the same attenuation direction

In the earlier 318-island mammal test, mean C−R3 was **−0.05593** for extreme-isolation islands and **−0.10138** outside the extreme tail. The predeclared extreme-minus-non-extreme contrast was **+0.04545** with 95% cluster-bootstrap interval **−0.00319 to +0.08836**.

That result did not establish a significant reversal, but its point direction is concordant with the global analysis: internal source-continuity information was not amplified at the highest external isolation.

## 4. Discussion

### 4.1 Two axes of isolation

The global mammal result supports a useful distinction between external and internal isolation. Even after the reference model represented multiple conventional dimensions of island context and simpler occupied-source information, the topology of the occupied source network retained held-out occurrence information.

This does not mean graph paths are realised dispersal routes. The result is informational: the focal species' occupied source configuration contains structure not fully recoverable from target-level isolation and Euclidean source proximity alone.

### 4.2 The surprise is attenuation, not handoff

The original source-pool-handoff idea predicted that internal source information should matter most when mainland isolation is extreme. Two mammal analyses now point in the opposite direction.

A plausible explanation is **source-network depletion**. At moderate external isolation, multiple occupied sources may remain available and differ meaningfully in their network relationship to a target. At extreme isolation, the occupied source pool may become sparse, truncated or uniformly remote. Once the source set itself is depleted, graph-path topology has less variation left to explain beyond R3.

A second possibility is increasing dominance of state filters. Extremely isolated islands may be so strongly filtered by historical connectivity, climate, area and persistence history that fine source-network structure contributes comparatively little incremental prediction.

These are mechanistic hypotheses, not conclusions. The current data do not identify realised colonisation paths or causal rescue processes.

### 4.3 Geographic generality and exceptions

The negative C−R3 direction in 108 blocks and 10 bioregions argues against a result generated by one archipelago or one biogeographic realm. At the same time, positive mean effects in Neartic and Oceanina show that the source-network increment is not universal.

This mixture is ecologically plausible: taxa, archipelago geometry, source saturation and geological history can alter whether graph-path structure adds information beyond direct source proximity.

### 4.4 Why the plant attempt does not provide confirmation

A global GIFT plant system was designed independently with 503 primary islands, 99 pilot islands, 404 confirmatory islands, 224 pilot-selected species and 59 confirmatory archipelagos. Its fresh confirmatory execution terminated after response access began because one frozen checklist returned zero species rows. No C−R3 score was produced.

The plant attempt is therefore neutral for ecological direction and cannot be counted as replication, support or non-support. A separately labelled endpoint-availability analysis can provide descriptive plant context only.

### 4.5 Relationship to the fresh boreal result

The small boreal island system produced a valid fresh non-support result. That local outcome places a useful boundary on generality: internal source topology is not guaranteed to improve prediction in every island system or spatial scale.

The global mammal result therefore suggests a macroecological pattern, not a universal law.

## 5. Evidence status and claim boundary

The manuscript must distinguish empirical scale from evidentiary status.

- Global 5,401-island mammals: large-scale, held-out, geographically broad, **nonconfirmatory exploratory**.
- 318-island mammals: independent design-frozen **nonfresh stress evidence**.
- GIFT plants: pristine global **terminal attempt without ecological score**.
- Boreal beetles: **fresh local non-support**.
- A-Islands/Tanzania: historical discovery and boundary evidence.

Permitted central claim:

> In a global mammal macroanalysis, species-conditioned graph-path source continuity retained held-out occurrence information beyond a strong reference containing external isolation, generic island structure and direct/diffuse occupied-source context. The incremental gain was geographically widespread but weakened as external isolation increased, a direction also seen in an independent 318-island mammal stress test.

Forbidden claims include fresh global confirmation, two-taxon replication, universal attenuation across taxa, or causal dispersal/rescue mechanisms.

## 6. Future test

The revised attenuation hypothesis is frozen in `development/prospective_source_network_attenuation_hypothesis_v1_80.json` for a genuinely independent future system. The future primary requires both an overall C−R3 gain and a positive isolation–C−R3 association under a response-sealed, leave-block-out design.

## Provisional target and positioning

The manuscript should be written as an island-biogeography/macroecology paper rather than as a methods paper. The strongest journal fits remain **Global Ecology and Biogeography**, **Journal of Biogeography**, and **Ecography**, with the final target depending on how strongly the discussion can connect the attenuation pattern to broader island colonisation and persistence theory without overstating evidence status.
