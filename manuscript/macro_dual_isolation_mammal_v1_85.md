# Island isolation is not one-dimensional

## Source-network information is widespread, asymmetric, and attenuates with isolation and species breadth

**Draft status:** mammal-centered macroecology manuscript v1.85. The empirical core is the global 5,401-island mammal analysis. All global mammal and GIFT ecological directions are explicitly nonconfirmatory. The valid fresh boreal result is non-support. This draft must not be read as fresh global or two-taxon confirmation.

## Abstract

Island isolation is commonly represented by target-level geography such as mainland distance, surrounding landmass, stepping stones, or generic network position. A focal species, however, experiences another axis of isolation defined by the islands that are actually occupied by potential insular sources. We asked whether this species-conditioned source topology retained held-out occurrence information after strong controls for environment, island area, current and historical external isolation, generic island-network context, global occupancy breadth, regional prevalence, and direct/diffuse occupied-source proximity. We analysed native-mammal occurrence across 5,401 islands, using 1,275 pilot islands to fix a 79-species universe and 4,126 held-out islands in 168 spatial blocks for evaluation. Adding graph-path occupied-source continuity to the strongest reference reduced block-weighted held-out log loss by 3.77% (C−R3 = −0.001814; 95% block-bootstrap interval −0.002817 to −0.000997). The direction was negative in 108/168 blocks, 10/12 bioregions, and 64/79 focal species. The gain weakened with greater current external isolation (block Spearman rho = +0.287; within-bioregion rho = +0.228) and broader species occupancy (rho = +0.276). Prediction-behaviour diagnostics revealed a strong asymmetry. Across the naturally sparse held-out surface (1.72% presences), C improved log loss for true absences (Δ = −0.00580) but worsened it for realized presences (Δ = +0.11644); a class-balanced diagnostic therefore favoured R3. Yet C improved ROC-AUC from 0.9095 to 0.9185, showing that the result was not only a global probability shift. The gain was also much stronger where occupied graph-reachable pilot sources existed (C−R3 = −0.01411) than in graph-source-empty cells (−0.00080), ruling out the empty-source sentinel as the driver. We interpret the pattern as asymmetric occupancy-constraint information: source topology chiefly reduces overprediction of unlikely island–species combinations, and that information weakens when source networks become externally depleted, broadly saturated, or empty. The analysis is nonconfirmatory and does not establish realized dispersal pathways or causal rescue.

**Keywords:** island biogeography; isolation; source pool; connectivity; occupancy; source network; spatial validation; mammals; macroecology

## 1. Introduction

### 1.1 Isolation is not one ecological quantity

Isolation is a central axis of island biogeography, but it is not uniquely represented by mainland distance. Alternative metrics capture surrounding landmass, stepping stones, currents, climatic similarity, or generic island-network structure (Weigelt & Kreft 2013). Functional island-biogeographic frameworks likewise distinguish remote dispersal from intra-archipelago movement and nearby source pools (Schrader et al. 2021).

These variables characterize the geography surrounding an island. A focal species, however, does not experience every island as an equivalent biological source. Its effective insular source environment depends on which islands are occupied and how those occupied islands are arranged. Two target islands with similar mainland distance and generic network position may therefore differ in their relationship to the occupied source network of a particular species.

This motivates a distinction between **external isolation** and **internal source isolation**. External isolation describes response-independent separation from major landmasses and generic island structure. Internal source isolation describes the focal island's relationship to the training-only occupied insular source pool of the focal species.

### 1.2 The adequacy question

The stronger test is not whether graph metrics correlate with occurrence. It is whether source topology adds information after simpler explanations are already represented.

Our strongest reference, R3, therefore includes climate and topography, island area, current and historical external isolation, generic island-network context, global occupancy breadth, species-by-bioregion prevalence, nearest occupied-source Euclidean distance, and diffuse occupied-source pressure. Candidate C adds only graph-path occupied-source continuity beyond R3.

This design asks whether the **configuration** of occupied sources contains information that is not reducible to target geography, regional identity, species prevalence, or direct source proximity.

### 1.3 Competing interpretations: opportunity versus constraint

Connectivity is often narrated as colonization opportunity: greater source access should raise the chance of occurrence. Patch-occupancy models similarly represent colonization as depending on surrounding occupied habitat or source patches (Hanski 1994). But source-network topology could also act as **constraint information**. If an island–species combination has nearby sources in Euclidean space but those sources occupy a poorly connected insular network, topology may help identify combinations where occurrence is unlikely.

These alternatives make the behaviour of C important. A source-opportunity signature would improve probability assigned to true presences. A constraint signature could instead reduce false or overconfident occurrence predictions, particularly on the overwhelmingly absent portion of a naturally sparse island × species surface.

### 1.4 From handoff to a source-network contrast window

An earlier working hypothesis predicted a source-pool handoff: internal source information should become increasingly important as external mainland isolation becomes extreme. An independent 318-island mammal stress test did not support that prediction. Source continuity improved held-out prediction descriptively, but the gain was smaller rather than larger in the extreme-isolation tail.

The present global analysis therefore asks four linked questions:

1. Does graph-path source continuity retain held-out information beyond R3?
2. Is that increment geographically and taxonomically broad?
3. Does the increment strengthen or weaken with external isolation and species occupancy breadth?
4. Does the increment primarily improve realized-presence prediction, or does it operate as occupancy-constraint information?

## 2. Methods

### 2.1 Global mammal system and evidence boundary

The source system contained native mammal presence–absence records for 5,592 islands. Before the final macroanalysis, one 15-island spatial block containing a previously exposed occurrence row was quarantined. A response-independent identity audit then matched 176 islands to an earlier 318-island mammal stress-test system; all matched islands were removed from training, targets, source pools, and occupancy-breadth denominators. The final population contained 5,401 islands.

The global mammal analysis is treated throughout as a **separate nonconfirmatory exploratory macro lineage**. A prior one-shot protocol terminated after species-header access because the physical response schema had been misinterpreted; no pilot occurrence value was decoded. A later response-free schema audit established that the file contains 5,394 species headers and a headerless row-routing field. A separately defined exploratory lineage then used this corrected physical schema while retaining the previously frozen population, spatial split, species threshold, and R0–R3–C method.

### 2.2 Spatial split and species universe

The 5,401 islands inherited a response-independent spatial partition based on bioregion × 10-degree blocks. The final split contained 1,275 pilot islands in 50 blocks and 4,126 held-out islands in 168 blocks across 12 bioregions.

The pilot response fixed the focal species universe before held-out response access. A species was retained if it occurred on at least 13 pilot islands and was absent from at least 13 pilot islands. This yielded 79 focal mammal species.

### 2.3 Reference hierarchy

R0 represented response-independent environmental state using bioregion plus standardized climate and topographic variables.

R1 added log island area, current external isolation, and past isolation.

R2 added generic island-network context using nearest-island distance and response-independent neighbour pressure.

R3 added four training-only species-conditioned controls: Jeffreys-smoothed global occupancy breadth, Jeffreys-smoothed species × bioregion prevalence, nearest occupied-source Euclidean distance, and diffuse occupied-source pressure.

Candidate C added two graph-path source terms beyond R3: graph-path nearest occupied-source distance and graph-path diffuse occupied-source pressure.

All source-derived features for pilot training rows excluded the complete focal validation block. Held-out predictions used only the complete frozen pilot source pool; no held-out occurrence entered any source feature.

### 2.4 Empty-source semantics

The source-feature numerics were frozen before pilot-result inspection. When no Euclidean occupied source existed, nearest-source distance was assigned a response-independent distance sentinel beyond the maximum possible great-circle distance and pressure was set to zero. For the graph terms, a response-independent bound beyond any finite path in the frozen regional graph was used when no occupied graph-reachable source existed; graph pressure was again zero.

No separate post hoc empty-source indicator was introduced. These rules were fixed before held-out response access.

### 2.5 Model fitting and held-out scoring

All tiers used deterministic pooled ridge logistic regression with lambda = 1, no response-based hyperparameter tuning, and fixed numerical tolerances.

The primary contrast was binary log-loss difference C−R3. Negative values favour C.

Within each of 168 held-out spatial blocks, we averaged C−R3 over the frozen island × species cells. The global point estimate was the equal-weight mean of block means. Uncertainty used 10,000 deterministic block-bootstrap replicates.

Because binary log loss is a proper probabilistic score evaluated over the observed island × species surface, the primary retains the empirical prevalence of occurrence rather than artificially balancing classes.

### 2.6 Post-hoc nonrescuing attenuation diagnostics

After the exploratory primary was frozen, we quantified geographic breadth and related block-level C−R3 to response-independent current isolation, past isolation, and log area. We report equal-block and within-bioregion-centered Spearman correlations.

A second post-hoc diagnostic averaged held-out C−R3 for each of the 79 fixed species and related the species-level increment to pilot occupancy prevalence. No species, block, or bioregion was removed.

### 2.7 Post-hoc prediction-behaviour diagnostics

After the primary was frozen, we decomposed the same frozen prediction and target surfaces without refitting.

We report:

- R3 and C log loss on true-presence and true-absence cells separately;
- a class-balanced equal-block diagnostic, defined as the equal average of presence-cell and absence-cell block deltas for blocks containing at least one presence;
- ROC-AUC and average precision for R3 and C;
- C−R3 in graph-source-empty versus graph-source-nonempty held-out cells;
- the association between block graph-empty fraction and block C−R3.

These diagnostics cannot alter the primary status. The class-balanced score addresses a different predictive question and is not a replacement estimand.

### 2.8 Independent and cross-taxon context

An earlier 318-island mammal stress test is used only for the direction of external-isolation attenuation. Its terminal rules prohibit rerunning the held-out primary to seek additional class-specific support.

A separate GIFT plant system reached a pristine 503-island design but its fresh confirmatory lane terminated after response access began because one frozen checklist returned zero species rows. No fresh ecological score was produced. A separately labelled endpoint-available continuation is used only as descriptive cross-taxon context.

## 3. Results

### 3.1 Graph-path source topology improved natural-prevalence held-out log loss

Across 325,954 held-out island × species cells, only 5,620 were presences (1.724%). The equal-block C−R3 estimate was **−0.001814**, with 95% block-bootstrap interval **−0.002817 to −0.000997**.

Block-weighted R3 log loss was 0.04811 and C log loss was 0.04629, a **3.77% relative reduction**. The cell-weighted reduction was 5.87%.

C−R3 was negative in **108/168 blocks**, in the equal-block mean of **10/12 bioregions**, and in **64/79 focal species**.

### 3.2 The source-network increment weakened with external isolation and species breadth

Current external isolation was positively associated with block C−R3 (Spearman rho = **+0.287**), and the association remained positive after within-bioregion centering (rho = **+0.228**). Because negative C−R3 favours C, this means the graph-path increment weakened as external isolation increased.

Pilot occupancy prevalence was likewise positively associated with species-level C−R3 (rho = **+0.276**). The broadest occupancy group had the weakest mean increment (−0.00146) and a median effect near zero (−0.00014).

Together, the place- and species-level diagnostics indicate that source topology becomes increasingly redundant when source networks are externally depleted or broadly saturated.

### 3.3 The natural-prevalence gain was strongly asymmetric between absences and presences

The primary improvement did **not** reflect uniformly better prediction of both outcome classes.

For the 320,334 true-absence cells, mean log loss fell from 0.02869 under R3 to 0.02288 under C, giving C−R3 = **−0.00580**. C had lower absence-cell loss in 130 of 168 blocks.

For the 5,620 realized presences, mean log loss rose from 2.01278 to 2.12922, giving C−R3 = **+0.11644**. Among the 124 blocks containing at least one presence, C had lower presence-cell loss in only 40.

A post-hoc class-balanced block diagnostic was therefore positive (**+0.04941**), favouring R3. Thus the frozen primary should be interpreted as improved probability prediction under the natural 1.72% prevalence surface, not as improved sensitivity to presences.

### 3.4 Ranking improved despite the presence-calibration trade-off

C was not merely an intercept-like downward shift in occurrence probability. ROC-AUC increased from **0.90947** under R3 to **0.91851** under C.

Average precision, however, declined slightly from **0.35612** to **0.35016**. The candidate therefore improved overall ranking while trading away some precision–recall performance and true-presence probability calibration.

### 3.5 Empty-source sentinel rows did not generate the primary gain

Graph-source-empty cells were common: **255,071 of 325,954 cells (78.25%)** lacked an occupied pilot source in the target bioregion.

If the primary gain were a sentinel artifact, the strongest improvement should occur in these empty cells. The opposite pattern occurred. Mean C−R3 was only **−0.00080** in graph-empty cells but **−0.01411** in the 70,883 graph-source-nonempty cells.

At block scale, graph-empty fraction was positively associated with C−R3 (rho = **+0.283**): blocks dominated by empty source support showed a weaker, not stronger, C advantage. Across equal-rank block quartiles, mean C−R3 weakened from −0.00307 in the lowest-empty quartile to −0.00038 in the highest-empty quartile.

The source-network signal is therefore concentrated where occupied source structure actually exists.

### 3.6 Independent mammal and plant context

The earlier 318-island mammal stress test showed the same qualitative external-isolation attenuation direction: C−R3 was −0.05593 in the extreme-isolation tail and −0.10138 outside it, with extreme-minus-non-extreme = +0.04545.

The GIFT fresh lane remained terminal and unscored. In a strongly filtered endpoint-available continuation, 118 of 404 confirmatory islands in 18 of 59 archipelagos remained. The original frozen plant prediction surface yielded C−R3 = −0.04749 (95% bootstrap interval −0.11333 to −0.00432). This is descriptive concordance only because endpoint attrition was severe.

## 4. Discussion

### 4.1 Source topology contains nonredundant island-biogeographic information

The global mammal analysis separates three concepts that are often conflated: target-level external isolation, direct proximity to occupied sources, and the topology of the occupied source network.

Even after R3 represented the first two plus species breadth and regional prevalence, graph-path source information changed held-out probability predictions and reduced natural-prevalence log loss across much of the global island system.

This is an informational result, not evidence that the graph paths are realized dispersal routes.

### 4.2 The information is asymmetric: source topology behaves more like a constraint than a rescue signal

The most important qualification is the outcome asymmetry.

C did not improve probability assigned to realized presences. Instead, its natural-prevalence gain arose mainly from lowering loss on true absences. In ecological terms, the extra topology appears to help identify island × species combinations where occurrence is implausible despite the simpler information already encoded by Euclidean source distance, source pressure, regional prevalence, and environmental state.

We therefore describe the result as **occupancy-constraint information**, not source rescue.

This interpretation remains predictive rather than causal. Individual graph coefficients are correlated with the R3 source variables and should not be read as direct ecological effects. Nor can the present analysis distinguish dispersal limitation from unrepresented historical or biotic processes that covary with source topology.

### 4.3 Why class imbalance does not disappear—and why it matters

The held-out surface is naturally sparse: only 1.72% of island × species cells are presences. Binary log loss evaluated at natural prevalence answers a legitimate macroecological probability question: how well do the models assign occurrence probabilities across the actual island × species surface?

Under that question C improves performance.

A class-balanced question is different. When presence and absence contributions are given equal weight post hoc, R3 performs better. Average precision also declines slightly under C. These results prevent a stronger claim that graph topology improves detection of presences.

The manuscript therefore makes two separate statements:

1. C improves probability prediction across the naturally prevalent occupancy surface.
2. C does not improve balanced presence prediction, and its true-presence log loss is worse.

Keeping both statements is essential to the claim boundary.

### 4.4 The result is not an empty-source encoding artifact

Most held-out cells had no occupied pilot source in the target bioregion, making the frozen empty-source rule a legitimate concern. But the gain was almost an order of magnitude larger when a graph-reachable occupied source existed, and high-empty blocks had weaker C effects.

This directly opposes the artifact explanation that sentinel values alone create the result.

It also reinforces the source-network contrast idea: topology can only be informative when a source network exists to contain topological variation.

### 4.5 A source-network contrast window

The attenuation diagnostics now have a clearer interpretation.

At high external isolation, source networks become increasingly sparse and C loses information. At high species occupancy breadth, source networks become broadly saturated and C again becomes increasingly redundant. Graph-empty blocks show the same limiting behaviour.

The working principle is therefore a **source-network contrast window**: topology carries nonredundant information when occupied source networks are present and heterogeneous enough to distinguish target islands, but not when the network is depleted, empty, or nearly ubiquitous.

The current data do not establish a formal unimodal relationship. That shape is a future hypothesis.

### 4.6 Geographic breadth and exceptions

The negative C−R3 direction in 108 blocks, 10 bioregions, and 64 species argues against a result generated by a single archipelago or a handful of taxa.

At the same time, positive regional means, positive species-level effects in 15 species, worse presence-cell log loss, and the fresh boreal non-support all show that source topology is not universally beneficial.

These exceptions are not noise to remove; they are the boundary conditions the next independent test must explain.

### 4.7 Plant evidence remains endpoint-limited

The GIFT endpoint-available subset shows the same overall C−R3 sign using the original frozen predictions, but only 118 of 404 confirmatory islands remain after strict endpoint-quality filtering.

That result cannot establish plant generality and cannot repair the terminal fresh plant attempt. It is retained solely as descriptive concordance.

## 5. Evidence status and claim boundary

The manuscript distinguishes scale, direction, and evidentiary status.

- **Global 5,401-island mammals:** broad nonconfirmatory exploratory macro evidence.
- **318-island mammals:** independent design-frozen nonfresh stress context.
- **GIFT fresh lane:** terminal without ecological score.
- **GIFT endpoint-available lane:** strongly selected nonconfirmatory descriptive context.
- **Boreal beetles:** valid fresh local non-support.

Permitted central claim:

> In a global nonconfirmatory mammal macroanalysis, graph-path occupied-source topology contained information beyond a strong external-isolation and source-proximity reference. The natural-prevalence gain was geographically broad but primarily reflected better prediction of true absences, and it weakened as external isolation, species occupancy breadth, and graph-source emptiness increased.

Permitted qualification:

> The candidate did not improve true-presence log loss or a post-hoc class-balanced diagnostic, although ROC-AUC improved, so the result is better interpreted as asymmetric occupancy-constraint information than as improved presence detection.

Forbidden claims include fresh global confirmation, two-taxon replication, improved presence detection, realized graph-path dispersal, causal rescue, or universal source-network attenuation.

## 6. Future test

The next independent response-sealed system should preregister both the overall natural-prevalence C−R3 primary and the prediction-behaviour signatures needed to distinguish opportunity from constraint.

The future protocol should report, without changing the primary:

1. presence-cell and absence-cell C−R3;
2. class-balanced block score;
3. ROC-AUC and average precision;
4. graph-empty versus graph-nonempty effects;
5. attenuation with external isolation and occupancy breadth.

A repeated constraint signature would support the idea that internal source topology acts mainly by delimiting where species are unlikely to establish or persist. A repeated opportunity signature would imply a different role. Predictive signatures alone would still not establish causal dispersal pathways.

## Positioning

**Preferred title:**  
*Island isolation is not one-dimensional: source-network information is widespread but asymmetric*

**Alternative title:**  
*Source-network topology sharpens island occupancy constraints but weakens with isolation and species breadth*

The paper should remain an island-biogeography/macroecology paper, not a methods paper. Its strongest contribution is the separation of external isolation, direct occupied-source proximity, and internal source topology—and the finding that the final topological increment is broad, attenuating, and strongly asymmetric in what it predicts.

## References currently central to framing

- Hanski, I. 1994. Patch-occupancy dynamics in fragmented landscapes. *Trends in Ecology & Evolution* 9:131–135.
- König, C. et al. 2021. Source pools and disharmony of the world's island floras. *Ecography* 44:44–55.
- Schrader, J. et al. 2021. A roadmap to plant functional island biogeography. *Biological Reviews* 96:2851–2870.
- Weigelt, P. & Kreft, H. 2013. Quantifying island isolation—insights from global patterns of insular plant species richness. *Ecography* 36:417–429.
