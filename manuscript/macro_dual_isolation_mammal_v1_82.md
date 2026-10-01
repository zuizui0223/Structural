# Island isolation is not one-dimensional

## Source-network information weakens with external isolation and species breadth

**Draft status:** mammal-centered macroecology manuscript v1.82. The empirical core is the global 5,401-island mammal analysis. The GIFT result is retained only as endpoint-limited nonconfirmatory cross-taxon context. No wording in this draft should be read as fresh global or two-taxon confirmation.

## Abstract

Island isolation is usually represented by target-level geography: distance to mainland, surrounding landmass, stepping stones, or generic network position. A focal species, however, experiences an additional axis of isolation defined by the islands that are actually occupied by potential insular sources. We asked whether this species-conditioned source topology retained held-out occurrence information after strong controls for environment, island area, current and historical external isolation, generic island-network context, global occupancy breadth, regional prevalence, and direct/diffuse occupied-source proximity. We analysed native-mammal occurrence across 5,401 islands after response-independent exclusion of a contaminated 15-island block and 176 islands overlapping an earlier stress-test dataset. Models were trained on 1,275 pilot islands and evaluated on 4,126 held-out islands in 168 spatial blocks across 12 bioregions; the pilot fixed a 79-species universe. Adding graph-path occupied-source continuity to the strongest reference reduced block-weighted held-out log loss (C−R3 = −0.001814; 95% block-bootstrap interval −0.002817 to −0.000997). The direction was negative in 108/168 blocks, 10/12 bioregions, and 64/79 focal species. Unexpectedly, the graph-path increment weakened along two distinct axes: greater current external isolation was associated with less-negative block-level C−R3 (Spearman rho = +0.287; within-bioregion-centered rho = +0.228), and broader pilot occupancy was associated with less-negative species-level C−R3 (rho = +0.276). An independent 318-island mammal stress test showed the same qualitative external-isolation attenuation direction. A pristine GIFT plant test terminated before fresh ecological scoring; a separately labelled endpoint-available subset retained only 118 of 404 confirmatory islands but showed the same C−R3 sign. We therefore propose a source-network contrast-window hypothesis: internal source topology is most informative while occupied source networks retain enough structural heterogeneity to distinguish targets, but becomes increasingly redundant when source networks are depleted by strong external isolation or saturated by broad species occupancy. The global mammal analysis is explicitly nonconfirmatory, so this result is presented as a broad macroecological pattern and a falsifiable hypothesis rather than as confirmed cross-taxon generality.

**Keywords:** island biogeography; isolation; source pool; connectivity; occupancy breadth; species occurrence; mammals; macroecology

## 1. Introduction

### 1.1 Isolation is not one ecological quantity

Island biogeography has long treated isolation as a central determinant of colonisation, persistence, and richness. Yet isolation is inherently multidimensional. Mainland distance, surrounding land area, stepping-stone structure, and generic network position capture different aspects of an island's geographic setting. These variables describe the island system itself rather than the realized source environment of any focal species.

A focal species does not experience every island as an equivalent source. Its effective insular source environment depends on which islands are occupied, how those occupied islands are distributed, and how they are connected through the broader archipelago. Two islands with identical mainland distance and similar generic network position may therefore differ strongly in their relationship to the occupied source network of a particular species.

This distinction motivates two ecological axes. **External isolation** describes response-independent separation from major landmasses and generic island structure. **Internal source isolation** describes the focal island's relationship to the training-only occupied insular source pool of the focal species.

### 1.2 The adequacy question

The central question is not whether graph metrics predict occurrence. The stronger question is whether species-conditioned source topology retains information after a deliberately rich reference has already represented conventional island state and simpler occupied-source context.

Our strongest reference, R3, includes climate and topography, island area, current and historical external isolation, generic island-network context, global occupancy breadth, species-by-bioregion prevalence, nearest occupied-source Euclidean distance, and diffuse occupied-source pressure. Candidate C adds only graph-path occupied-source continuity beyond that reference.

If C improves held-out prediction, the result cannot be explained simply by larger islands, closer mainland proximity, more nearby islands, broader species distributions, regional identity, or the mere existence of occupied sources. Instead, it would imply that the **configuration** of the occupied source network contains nonredundant occurrence information.

### 1.3 From handoff to source-network contrast

An earlier working hypothesis predicted a source-pool handoff: internal source information should become increasingly important as mainland isolation becomes extreme. An independent 318-island mammal stress test did not support that prediction. Source continuity improved prediction descriptively in both isolation regimes, but the gain was smaller rather than larger in the extreme-isolation tail.

The present analysis therefore asks three questions. First, does graph-path source continuity retain nonredundant held-out information at global scale beyond R3? Second, is that information geographically broad or concentrated in a small set of regions? Third, what ecological conditions attenuate or preserve that information?

The third question motivates a broader conceptual possibility. Source topology may be informative only when the occupied source network retains enough heterogeneity to differentiate targets. If external isolation becomes extreme, the source pool may become too sparse. Conversely, if a species occupies many islands, the source pool may become so broad that graph topology is saturated or redundant with simpler prevalence and proximity metrics.

## 2. Methods

### 2.1 Global mammal system and evidence boundary

The source system contained native mammal presence–absence records for 5,592 islands. Before the final macroanalysis, one 15-island spatial block containing a previously exposed occurrence row was quarantined. A response-independent identity audit then matched 176 islands to an earlier 318-island mammal stress-test system; all matched islands were removed from training, targets, source pools, and occupancy-breadth denominators. The final population contained 5,401 islands.

The global mammal analysis is treated throughout as a **separate nonconfirmatory exploratory macro lineage**. A prior one-shot protocol terminated after species-header access because the physical response schema had been misinterpreted; no pilot occurrence value was decoded. A later response-free schema audit established that the file contains 5,394 species headers and a headerless row-routing field in each data record. A separately defined exploratory lineage then used this corrected schema while retaining the previously frozen island population, spatial split, species threshold, and R0–R3–C model method.

### 2.2 Spatial split and species universe

The 5,401 islands inherited a response-independent spatial partition based on bioregion × 10-degree blocks. The final split contained 1,275 pilot islands in 50 blocks and 4,126 held-out islands in 168 blocks across 12 bioregions.

The pilot response fixed the focal species universe before held-out response access. A species was retained if it occurred on at least 13 pilot islands and was absent from at least 13 pilot islands. This yielded 79 focal mammal species.

### 2.3 Reference hierarchy

R0 represented response-independent environmental state using bioregion plus standardized climate and topographic variables.

R1 added log island area, current external isolation, and past isolation.

R2 added generic island-network context using nearest-island distance and response-independent neighbor pressure.

R3 added four training-only species-conditioned controls: Jeffreys-smoothed global occupancy breadth, Jeffreys-smoothed species × bioregion prevalence, nearest occupied-source Euclidean distance, and diffuse occupied-source pressure.

Candidate C added only two graph-path terms beyond R3: graph-path nearest occupied-source distance and graph-path diffuse occupied-source pressure.

All source-derived features for pilot training rows excluded the complete focal validation block. Held-out predictions used only the complete frozen pilot source pool; no held-out occurrence entered any source feature.

### 2.4 Model fitting and held-out prediction

All tiers used the same deterministic pooled ridge logistic regression framework with lambda = 1, no response-based hyperparameter tuning, and fixed numerical tolerances. The full R0–R3–C method was frozen before the exploratory pilot response was opened.

The primary contrast was binary log-loss difference C−R3. Negative values favor the graph-path source-continuity candidate.

For each of the 168 held-out spatial blocks, we averaged C−R3 across all eligible island × species cells. The global estimate was the equal-weight mean of the 168 block means. Uncertainty used 10,000 deterministic block-bootstrap replicates.

### 2.5 Geographic attenuation diagnostics

After the exploratory primary was frozen, we examined two post-hoc, nonrescuing properties of the frozen block scores.

First, geographic breadth was quantified by the number of blocks with C−R3 < 0 and the number of bioregions with a negative equal-block mean.

Second, each block score was linked to response-independent block means of current isolation, past isolation, and log area. We report equal-block Spearman correlations and within-bioregion-centered Spearman correlations. These diagnostics cannot change the status of the primary result.

### 2.6 Species occupancy-breadth diagnostics

A second post-hoc diagnostic asked whether the C increment varied with the breadth of the focal species. For each of the 79 fixed focal species, we averaged held-out C−R3 over all 4,126 held-out islands and related that species-level effect to pilot occupancy prevalence. We report Spearman rho and rank-defined occupancy groups. No species was removed, and no trait or taxonomic subgroup search was performed.

### 2.7 Independent 318-island mammal context

An earlier independent mammal stress test used 244 held-out islands and 233 fixed species. Its predeclared primary asked whether the C−R3 gain was larger in the extreme mainland-isolation tail. That prediction was unsupported, but the frozen descriptive C−R3 values provide an independent qualitative check on the direction of external-isolation attenuation.

### 2.8 GIFT plant context

A separate GIFT system reached a pristine global design with 503 primary islands, 99 pilot islands, 404 confirmatory islands, 224 pilot-selected species, and 59 confirmatory archipelagos. Its fresh confirmatory execution terminated after response access began because one frozen checklist returned zero species rows. No fresh ecological C−R3 score was produced.

A separately labelled nonconfirmatory continuation applied one common endpoint-availability rule to all 596 frozen confirmatory lists. No replacement lists or entities were permitted, and the original frozen R3/C prediction surface was retained without refitting. Because this continuation strongly filtered the target population, it is used only as descriptive cross-taxon context.

## 3. Results

### 3.1 Internal source topology retained global held-out information

Across 325,954 held-out island × species cells, the equal-block global C−R3 estimate was **−0.001814**. The 95% block-bootstrap interval was **−0.002817 to −0.000997**.

Graph-path source continuity therefore retained incremental predictive information after R3 had already represented environment, island area, current and historical external isolation, generic island-network structure, occupancy breadth, species-by-bioregion prevalence, and direct/diffuse occupied-source context.

### 3.2 The direction was broad across space and species

C−R3 was negative in **108 of 168 blocks (64.3%)**. Ten of the twelve bioregions had a negative equal-block mean; Neartic and Oceanina were the two positive-mean exceptions.

At the species level, **64 of 79 focal species (81.0%)** had negative mean C−R3 across held-out islands. The global signal was therefore not generated by a single region or a small minority of focal species.

### 3.3 Greater external isolation weakened the source-network increment

Current external isolation was positively associated with C−R3 across blocks (Spearman rho = **+0.287**). The association remained positive after within-bioregion centering (rho = **+0.228**).

Because negative C−R3 favors C, this positive relationship means the graph-path source-continuity advantage became weaker as external isolation increased.

Past isolation showed weaker positive associations (rho = +0.133 overall; +0.173 within bioregion). Log area also showed a positive descriptive association (rho = +0.268 overall; +0.175 within bioregion).

### 3.4 Broadly distributed species also showed weaker source-topology gains

Pilot occupancy prevalence was positively associated with species-level mean C−R3 (Spearman rho = **+0.276**). Thus, broader species tended to receive less incremental predictive benefit from graph-path source continuity.

The two narrowest-to-moderate occupancy groups had mean C−R3 of **−0.00483** and **−0.00562**, whereas the two broader groups had means of **−0.00275** and **−0.00146**. The broadest group had a median effect of only **−0.00014**, and just 10 of 19 species in that group retained a negative mean effect.

The pattern does not establish formal unimodality, but it indicates a strong loss of topological information among the broadest-distributed species.

### 3.5 The 318-island stress test pointed in the same external-isolation direction

In the earlier 318-island mammal test, mean C−R3 was **−0.05593** for extreme-isolation islands and **−0.10138** outside the extreme tail. The predeclared extreme-minus-non-extreme contrast was **+0.04545**, with 95% cluster-bootstrap interval **−0.00319 to +0.08836**.

That result did not establish a significant reversal, but its point direction is concordant with the global block diagnostic: internal source-continuity information was not amplified at the highest external isolation.

### 3.6 The endpoint-available plant subset showed the same sign but severe attrition

Of the 404 frozen GIFT confirmatory islands, only **118** retained at least one endpoint-available checklist with accepted high-confidence native rows. This left **18 of 59** confirmatory archipelagos.

Only nine excluded islands lacked any available list. A further **277** islands had returned checklist rows but zero accepted high-confidence native rows under the frozen endpoint-quality rule. Endpoint attrition was therefore substantial and not attributable solely to the original zero-row API failure.

Within the retained subset, the original frozen prediction surface yielded C−R3 = **−0.04749**, with bootstrap 95% interval **−0.11333 to −0.00432**. This sign agrees with the mammal analysis, but the severe filtering prevents interpretation as representative global plant evidence or replication.

## 4. Discussion

### 4.1 External and internal isolation are distinct axes

The global mammal result supports a useful distinction between target-level external isolation and species-conditioned internal source isolation. Even after a strong reference represented conventional island geography, regional prevalence, global occupancy breadth, and simpler occupied-source proximity, the topology of the occupied source network retained held-out occurrence information.

This does not imply that graph paths are realized dispersal routes. The result is informational: occupied source configuration contains structure not fully recoverable from target-level isolation and Euclidean source proximity alone.

### 4.2 A source-network contrast window

The original source-pool-handoff hypothesis predicted that internal source topology would become most important at extreme mainland isolation. Both mammal analyses point away from that prediction.

The new evidence suggests a broader principle: **source topology is useful only while the occupied source network retains structural contrast**.

At the sparse limit, strong external isolation can deplete or truncate the occupied source pool. Few plausible sources remain, graph paths become uniformly long or absent, and topology contributes little beyond R3.

At the saturated limit, broadly distributed species occupy many possible sources. The source network becomes dense or homogeneous, and graph-path information becomes increasingly redundant with occupancy breadth, regional prevalence, and direct/diffuse source context.

The observed place-level and species-level attenuation therefore converge on a common working mechanism. Internal source topology may be most informative between these limits, where enough occupied sources remain to form alternative pathways but occupancy is not so broad that all targets experience similar source structure.

This is a future hypothesis rather than a causal conclusion. The present data do not demonstrate realized colonisation pathways, source depletion, source saturation, or a formal unimodal response.

### 4.3 Why the breadth result matters for island biogeography

Classical island isolation is usually a property of the target island. The species-breadth result shows why that is incomplete: the same island can occupy a very different effective connectivity landscape for a narrow endemic than for a widespread species.

For narrow-to-moderate species, which occupied source islands remain and how they are connected can strongly differentiate targets. For broad species, source availability is more nearly ubiquitous, and topology adds less beyond occupancy breadth and regional prevalence.

Thus the ecological meaning of island isolation depends jointly on **where the island is** and **how the focal species occupies the surrounding island system**.

### 4.4 Geographic generality and exceptions

Negative C−R3 in 108 blocks, 10 bioregions, and 64 species argues against a signal generated by one archipelago, one realm, or a handful of species. At the same time, positive regional means in Neartic and Oceanina and positive species-level effects in 15 species show that the increment is not universal.

These exceptions are important. Archipelago geometry, dispersal capacity, source saturation, historical connectivity, and source-pool turnover can all change whether graph-path structure adds information beyond Euclidean proximity.

### 4.5 Plant context is concordant but endpoint-limited

The fresh GIFT attempt cannot be treated as support because its confirmatory run terminated without an ecological score. The later endpoint-available subset does show the same C−R3 sign using the originally frozen prediction surface.

However, only 118 of 404 confirmatory islands and 18 of 59 archipelagos remained after endpoint-quality filtering. The plant result is therefore best interpreted as **descriptive concordance under strong availability selection**, not as cross-taxon generality.

This distinction strengthens rather than weakens the manuscript: it separates a potentially interesting biological pattern from the much stronger claim of replication.

### 4.6 Relationship to the fresh boreal result

The boreal island system produced a valid fresh non-support result. That local system places an explicit boundary on generality. Internal source topology is not guaranteed to improve occurrence prediction at every spatial scale or in every island system.

The global mammal result is therefore a macroecological pattern with identifiable boundary conditions, not a universal law.

## 5. Evidence status and claim boundary

The manuscript must distinguish scale from evidentiary status.

- **Global 5,401-island mammals:** large-scale, held-out, geographically and species-wise broad, nonconfirmatory exploratory evidence.
- **318-island mammals:** independent design-frozen nonfresh stress evidence.
- **GIFT fresh lane:** pristine global terminal attempt without ecological score.
- **GIFT endpoint-available lane:** strongly selected nonconfirmatory subset with the same sign.
- **Boreal beetles:** valid fresh local non-support.
- **A-Islands/Tanzania:** historical discovery and motivation only.

Permitted central claim:

> In a global mammal macroanalysis, species-conditioned graph-path source continuity retained held-out occurrence information beyond a strong reference containing external isolation, generic island structure, occupancy breadth, regional prevalence, and direct/diffuse occupied-source context. The increment was widespread but weakened both as islands became more externally isolated and as species became more broadly distributed, consistent with a source-network contrast-window hypothesis.

A permissible secondary sentence is:

> A strongly endpoint-filtered GIFT subset showed the same sign, but the plant fresh lane terminated without scoring and no cross-taxon confirmation is claimed.

Forbidden claims include fresh global confirmation, two-taxon replication, universal attenuation, representative plant support, or causal source-depletion/source-saturation mechanisms.

## 6. Future test

The revised hypothesis is frozen in `development/prospective_source_network_contrast_window_hypothesis_v1_82.json`.

A genuinely independent future system should test three predeclared components under a response-sealed, leave-block-out design:

1. an overall held-out C−R3 gain;
2. attenuation of that gain with external island isolation;
3. attenuation of that gain with species occupancy breadth.

The future test should not select isolation thresholds, occupancy thresholds, taxa, or nonlinear forms from the response. Formal unimodality should be tested only if separately powered and preregistered.

## Provisional target and positioning

The paper should be written as an island-biogeography and macroecology paper rather than as a methods paper.

**Preferred title:**  
*Island isolation is not one-dimensional: source-network information weakens with external isolation and species breadth*

**Alternative title:**  
*When does an island source network matter? Internal connectivity weakens as source pools become sparse or saturated*

The strongest journal fits remain **Global Ecology and Biogeography**, **Journal of Biogeography**, and **Ecography**. The central value is the ecological decomposition of isolation and the unexpected attenuation pattern, not a claim of confirmatory replication.
