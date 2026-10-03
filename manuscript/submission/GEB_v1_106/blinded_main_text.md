# Island isolation is not one-dimensional: source-network information differs across species occupancy regimes

**Running title:** Source networks across occupancy


## Abstract

**Aim:** Island isolation is usually described by target-level geography, yet a focal species also experiences the configuration of islands that are actually occupied by potential sources. We asked whether this species-conditioned source topology retains held-out occurrence information beyond conventional island isolation and simpler source context, and whether the same signal generalizes to a prospectively sealed layer of rarer species.

**Innovation:** In an exploratory layer of 79 mammal species across 5,401 islands, adding graph-path occupied-source continuity to a strong source-aware reference reduced block-weighted held-out log loss by 3.77% (C−R3 = −0.001814; 95% interval −0.002817 to −0.000997), mainly through improved absence prediction. Before opening any additional held-out response, we preregistered a second layer of 96 species with only 5–12 pilot presences and froze R3, actual-C, and 20 degree- and edge-length-matched rewired-C prediction surfaces for 4,126 held-out islands.

**Main conclusions:** The sealed rarer-species layer did not replicate the overall gain (C−R3 = −0.000442; 95% interval −0.001098 to +0.000204). Its prediction asymmetry reversed: presence log loss improved strongly whereas absence log loss did not. Actual graph topology was indistinguishable from matched rewired graphs. Source-network information is therefore not uniformly informative across the occupancy regimes tested; its predictive role changes with species occupancy. The rare-species failure provides prospective boundary evidence consistent with, but not proof of, a source-network contrast window.

**Keywords:** island biogeography; isolation; source pool; connectivity; occupancy; source network; preregistration; mammals; macroecology

## 1. Introduction

### 1.1 Isolation is not one ecological quantity

Isolation is a central axis of island biogeography, but it is not uniquely represented by mainland distance. Global comparisons show that surrounding land area, stepping stones, large source islands, climatic similarity and other metrics capture distinct aspects of isolation (Weigelt & Kreft 2013). Across 16 commonly used metrics, Carter et al. (2020) recovered three major dimensions corresponding to mainland distance, stepping stones and insular-network position. Graph-theoretic work within archipelagos likewise shows that stepping-stone islands can alter structural connectivity (Sillero et al. 2018), while nearby islands can function not only as sources but also as alternative colonization targets (Wang et al. 2023). The novelty of the present study is therefore not the claim that island isolation is multidimensional or that networks matter.

These metrics still characterize the geography surrounding an island rather than the realized source environment of a focal species. Species-pool theory emphasizes that the set of potential colonists depends on spatial scale and regional availability (Cornell & Harrison 2014), and island studies increasingly model source regions explicitly rather than assuming a single undifferentiated mainland pool (König et al. 2021). A focal species, however, does not experience every potential source region or island as occupied. Its effective insular source environment depends on which islands are actually occupied and how those occupied islands are arranged. Two target islands with similar mainland distance and generic network position may therefore differ in their relationship to the occupied source network of a particular species.

This motivates a distinction between **external isolation** and **internal source isolation**. External isolation describes response-independent separation from major landmasses and generic island structure. Internal source isolation describes the focal island's relationship to the training-only occupied insular source pool of the focal species.

### 1.2 The adequacy question

The stronger test is not whether graph metrics correlate with occurrence. Patch-occupancy and habitat-network models already show that surrounding occupancy, weighted connectivity and network topology can predict patch occurrence (Hanski 1994; Berlow et al. 2013; Ortiz-Rodríguez et al. 2019), and graph-based connectivity can be checked against independent ecological and genetic evidence (Daniel et al. 2023). The unresolved question here is whether the topology of the **realized occupied source network** contributes information after simpler source and island-state explanations are already represented.

Our strongest reference, R3, therefore includes climate and topography, island area, current and historical external isolation, generic island-network context, global occupancy breadth, species-by-bioregion prevalence, nearest occupied-source Euclidean distance, and diffuse occupied-source pressure. Candidate C adds only graph-path occupied-source continuity beyond R3.

This design asks whether the **configuration of training-only occupied sources** contains held-out information that is not reducible to target geography, generic network position, regional identity, species prevalence, or direct/diffuse source proximity. That conditional increment—not graph theory, connectivity modelling, or the species-pool concept themselves—is the intended conceptual contribution.

### 1.3 Competing interpretations: opportunity versus constraint

Connectivity is often narrated as colonization opportunity: greater source access should raise the chance of occurrence. Patch-occupancy models similarly represent colonization as depending on surrounding occupied habitat or source patches (Hanski 1994). But source-network topology could also act as **constraint information**. If an island–species combination has nearby sources in Euclidean space but those sources occupy a poorly connected insular network, topology may help identify combinations where occurrence is unlikely.

These alternatives make the behaviour of C important. A source-opportunity signature would improve probability assigned to true presences. A constraint signature could instead reduce false or overconfident occurrence predictions, particularly on the overwhelmingly absent portion of a naturally sparse island × species surface.

### 1.4 From exploratory signal to sealed species-layer validation

An earlier working hypothesis predicted a source-pool handoff: internal source information should become increasingly important as external mainland isolation becomes extreme. An independent 318-island mammal stress test did not support that prediction. The global analysis then revealed a different pattern in a 79-species exploratory layer: graph-path source continuity improved natural-prevalence held-out log loss, but the gain weakened with external isolation and species breadth and was driven mainly by true absences.

Crucially, the held-out response for the other mammal species had not been decoded. We therefore used that remaining sealed response for a prospective second-layer test rather than continuing to mine the original 79 species.

Before opening any new held-out values, we fixed a disjoint second layer comprising species with 5–12 pilot presences, preregistered four directional predictions, and froze all R3, actual-C and rewired-C held-out predictions. This design asks whether the original signal generalizes to rarer species and whether any gain depends on the realized graph topology rather than a degree- and distance-matched network surrogate. Because this prospective second layer provides the strongest protection against result-dependent interpretation, we present it immediately after the exploratory primary and before the post-hoc diagnostics.

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

### 2.6 Prospective sealed rare-species layer

The original held-out analysis decoded only the 79 focal species selected from the pilot. Held-out values for the remaining 5,315 mammal species remained semantically sealed.

We prospectively defined a disjoint second layer using pilot information only: species with 5–12 pilot presences and at least 13 pilot absences. This yielded 96 species. The 4,126 held-out islands therefore contained 396,096 previously unread island × species targets.

Before any second-layer held-out target was decoded, we froze four predictions.

**P1, overall replication:** equal-block C−R3 should be negative, with a 95% block-bootstrap upper bound below zero.

**P2, prediction asymmetry:** absence-cell C−R3 should be negative, whereas presence-cell C−R3 should not improve.

**P3, source support:** the C−R3 gain should be stronger in graph-source-nonempty than graph-source-empty cells.

**P4, topology specificity:** actual C should outperform the mean of 20 deterministic rewired-C models.

For P4, rewiring was performed independently within each bioregion using undirected degree-preserving double-edge swaps. Each accepted replacement edge was constrained to remain in the same original edge-length quintile, preserving both degree sequence and edge-length-bin counts. All 20 null graphs completed their preregistered swap targets, remained connected, and were generated without held-out response.

R3, actual C, all 20 rewired-C models, the graph-empty mask, and all 4,126 × 96 held-out probabilities were frozen before response access. The second-layer response was then decoded once and P1–P4 were scored immediately without refitting, threshold changes, null replacement or reruns.

### 2.7 Post-hoc nonrescuing attenuation diagnostics

After the exploratory primary was frozen, we quantified geographic breadth and related block-level C−R3 to response-independent current isolation, past isolation, and log area. We report equal-block and within-bioregion-centered Spearman correlations.

A second post-hoc diagnostic averaged held-out C−R3 for each of the 79 fixed species and related the species-level increment to pilot occupancy prevalence. No species, block, or bioregion was removed.

### 2.8 Post-hoc prediction-behaviour diagnostics

After the primary was frozen, we decomposed the same frozen prediction and target surfaces without refitting.

We report:

- R3 and C log loss on true-presence and true-absence cells separately;
- a class-balanced equal-block diagnostic, defined as the equal average of presence-cell and absence-cell block deltas for blocks containing at least one presence;
- ROC-AUC and average precision for R3 and C;
- C−R3 in graph-source-empty versus graph-source-nonempty held-out cells;
- the association between block graph-empty fraction and block C−R3.

These diagnostics cannot alter the primary status. The class-balanced score addresses a different predictive question and is not a replacement estimand.

### 2.9 Independent and cross-taxon context

An earlier 318-island mammal stress test is used only for the direction of external-isolation attenuation. Its terminal rules prohibit rerunning the held-out primary to seek additional class-specific support.

A separate GIFT plant system, using the Global Inventory of Floras and Traits framework (Denelle et al. 2023), reached a pristine 503-island design but its fresh confirmatory lane terminated after response access began because one frozen checklist returned zero species rows. No fresh ecological score was produced. A separately labelled endpoint-available continuation is used only as descriptive cross-taxon context.

## 3. Results

### 3.1 Graph-path source topology improved natural-prevalence held-out log loss

Across 325,954 held-out island × species cells, only 5,620 were presences (1.724%). The equal-block C−R3 estimate was **−0.001814**, with 95% block-bootstrap interval **−0.002817 to −0.000997**.

Block-weighted R3 log loss was 0.04811 and C log loss was 0.04629, a **3.77% relative reduction**. The cell-weighted reduction was 5.87%.

C−R3 was negative in **108/168 blocks**, in the equal-block mean of **10/12 bioregions**, and in **64/79 focal species** (Figure 1).

### 3.2 A preregistered rarer-species layer does not replicate the exploratory source-network signal

The sealed second layer contained 96 species with 5–12 pilot presences and 396,096 held-out island × species cells. Only 1,233 held-out cells were presences (0.311%).

The preregistered primary did not pass its support criterion. C−R3 was **−0.000442**, with 95% block-bootstrap interval **−0.001098 to +0.000204**. The point direction was slightly negative, but the interval included zero.

The preregistered prediction-asymmetry signature also failed and reversed direction. For absences, C−R3 was **+0.000430** (95% interval −0.000060 to +0.000928). For presences, C−R3 was **−0.27744** (95% interval −0.39652 to −0.15878). The class-balanced equal-block diagnostic was **−0.13841**. Thus, unlike the original layer, the rarer layer showed strong improvement in realized-presence prediction and no supported improvement in absences.

The source-support contrast had the expected point direction but was not supported: nonempty-minus-empty C−R3 = **−0.00603**, with 95% interval **−0.01626 to +0.00118** across 166 paired blocks.

Finally, actual graph topology did not outperform the preregistered rewired nulls. Actual C minus mean rewired C was **+1.56 × 10⁻⁶**, with 95% interval **−2.12 × 10⁻⁴ to +2.04 × 10⁻⁴**. The actual graph was better than 11 of 20 null graphs on block-weighted C−R3, essentially chance relative to the fixed null ensemble.

The second layer therefore constitutes a **prospective species-layer non-replication within the same geographic system**, not geographically independent confirmation (Figure 2).

### 3.3 Exploratory attenuation with external isolation and species breadth

Current external isolation was positively associated with block C−R3 (Spearman rho = **+0.287**), and the association remained positive after within-bioregion centering (rho = **+0.228**). Because negative C−R3 favours C, this means the graph-path increment weakened as external isolation increased (Figure 3).

Pilot occupancy prevalence was likewise positively associated with species-level C−R3 (rho = **+0.276**). The broadest occupancy group had the weakest mean increment (−0.00146) and a median effect near zero (−0.00014; Figure 4).

Together, the place- and species-level diagnostics indicate that source topology becomes increasingly redundant when source networks are externally depleted or broadly saturated.

### 3.4 The exploratory gain was strongly asymmetric between absences and presences

The primary improvement did **not** reflect uniformly better prediction of both outcome classes.

For the 320,334 true-absence cells, mean log loss fell from 0.02869 under R3 to 0.02288 under C, giving C−R3 = **−0.00580**. C had lower absence-cell loss in 130 of 168 blocks.

For the 5,620 realized presences, mean log loss rose from 2.01278 to 2.12922, giving C−R3 = **+0.11644**. Among the 124 blocks containing at least one presence, C had lower presence-cell loss in only 40.

A post-hoc class-balanced block diagnostic was therefore positive (**+0.04941**), favouring R3. Thus the frozen primary should be interpreted as improved probability prediction under the natural 1.72% prevalence surface, not as improved sensitivity to presences (Supplementary Fig. S2).

### 3.5 Ranking improved despite the presence-calibration trade-off

C was not merely an intercept-like downward shift in occurrence probability. ROC-AUC increased from **0.90947** under R3 to **0.91851** under C.

Average precision, however, declined slightly from **0.35612** to **0.35016**. The candidate therefore improved overall ranking while trading away some precision–recall performance and true-presence probability calibration.

### 3.6 Empty-source sentinel rows did not generate the exploratory gain

Graph-source-empty cells were common: **255,071 of 325,954 cells (78.25%)** lacked an occupied pilot source in the target bioregion.

If the primary gain were a sentinel artifact, the strongest improvement should occur in these empty cells. The opposite pattern occurred. Mean C−R3 was only **−0.00080** in graph-empty cells but **−0.01411** in the 70,883 graph-source-nonempty cells.

At block scale, graph-empty fraction was positively associated with C−R3 (rho = **+0.283**): blocks dominated by empty source support showed a weaker, not stronger, C advantage. Across equal-rank block quartiles, mean C−R3 weakened from −0.00307 in the lowest-empty quartile to −0.00038 in the highest-empty quartile.

This empty-support pattern does not explain the separate external-isolation attenuation. Current isolation and graph-empty fraction were nearly uncorrelated across the 168 blocks (Spearman rho = **+0.047**). The partial Spearman association between current isolation and C−R3 after controlling graph-empty fraction was **+0.286**, essentially unchanged from the unadjusted +0.287. After within-bioregion centering, isolation and graph-empty fraction had rho = **+0.006**, and the partial isolation–C−R3 association remained **+0.228**, again effectively identical to the unadjusted +0.228. This reviewer-defense audit is post hoc and descriptive, but it shows that the two attenuation diagnostics are not simply duplicate summaries of the same block-level quantity.

The source-network signal is therefore concentrated where occupied source structure actually exists (Supplementary Fig. S2), while external isolation retains a separate descriptive association with the size of that increment.

### 3.7 Independent mammal and plant context

The earlier 318-island mammal stress test showed the same qualitative external-isolation attenuation direction: C−R3 was −0.05593 in the extreme-isolation tail and −0.10138 outside it, with extreme-minus-non-extreme = +0.04545.

The GIFT fresh lane remained terminal and unscored. In a strongly filtered endpoint-available continuation, 118 of 404 confirmatory islands in 18 of 59 archipelagos remained. The original frozen plant prediction surface yielded C−R3 = −0.04749 (95% bootstrap interval −0.11333 to −0.00432). This is descriptive concordance only because endpoint attrition was severe (Supplementary Fig. S1).

## 4. Discussion

### 4.1 Prospective rare-species validation sets a boundary on generality

The sealed second layer changes the interpretation of the original exploratory result (Figure 2).

The original 79-species layer cannot be generalized across mammal occupancy regimes. Species with only 5–12 pilot presences did not replicate the overall C−R3 gain, and the actual graph had no detectable advantage over degree- and edge-length-matched rewired graphs.

More strikingly, the predictive asymmetry reversed. In the original layer, C mainly improved absence prediction and worsened presence prediction. In the rarer layer, C strongly improved presence prediction and did not improve absences. Source-network information therefore changes not only in magnitude but also in predictive role across occupancy regimes.

This result is compatible with a **source-network contrast window**. Very sparse occupied source sets may contain too little realized topological structure for actual adjacency to matter beyond generic source scarcity and geometry. At intermediate occupancy, occupied sources may be numerous and heterogeneous enough for network configuration to constrain where occurrence is unlikely. Among the broadest species in the exploratory layer, the incremental gain again weakened, consistent with increasing redundancy as source occupancy becomes widespread.

The combined pattern is suggestive rather than a formal test of unimodality. The only prospective boundary result is the rare-species non-replication. No causal source-depletion, saturation, dispersal-path or unimodal mechanism is established.

### 4.2 What remains of the exploratory source-network signal

The global mammal analysis separates three concepts that are often conflated: target-level external isolation, direct proximity to occupied sources, and the topology of the occupied source network.

Even after R3 represented the first two plus species breadth and regional prevalence, graph-path source information changed held-out probability predictions and reduced natural-prevalence log loss across much of the global island system.

This is an informational result, not evidence that the graph paths are realized dispersal routes.

### 4.3 The exploratory signal is asymmetric: constraint rather than rescue

The most important qualification is the outcome asymmetry.

C did not improve probability assigned to realized presences. Instead, its natural-prevalence gain arose mainly from lowering loss on true absences. In ecological terms, the extra topology appears to help identify island × species combinations where occurrence is implausible despite the simpler information already encoded by Euclidean source distance, source pressure, regional prevalence, and environmental state.

We therefore describe the result as **occupancy-constraint information**, not source rescue.

This interpretation remains predictive rather than causal. Individual graph coefficients are correlated with the R3 source variables and should not be read as direct ecological effects. Nor can the present analysis distinguish dispersal limitation from unrepresented historical or biotic processes that covary with source topology.

### 4.4 Why class imbalance does not disappear—and why it matters

The held-out surface is naturally sparse: only 1.72% of island × species cells are presences. Binary log loss evaluated at natural prevalence answers a legitimate macroecological probability question: how well do the models assign occurrence probabilities across the actual island × species surface?

Under that question C improves performance.

A class-balanced question is different. When presence and absence contributions are given equal weight post hoc, R3 performs better. Average precision also declines slightly under C. These results prevent a stronger claim that graph topology improves detection of presences.

The manuscript therefore makes two separate statements:

1. C improves probability prediction across the naturally prevalent occupancy surface.
2. C does not improve balanced presence prediction, and its true-presence log loss is worse.

Keeping both statements is essential to the claim boundary.

### 4.5 The exploratory result is not an empty-source encoding artifact

Most held-out cells had no occupied pilot source in the target bioregion, making the frozen empty-source rule a legitimate concern. But the gain was almost an order of magnitude larger when a graph-reachable occupied source existed, and high-empty blocks had weaker C effects.

This directly opposes the artifact explanation that sentinel values alone create the result.

It also reinforces the source-network contrast idea: topology can only be informative when a source network exists to contain topological variation.

### 4.6 Geographic breadth and exceptions

The negative C−R3 direction in 108 blocks, 10 bioregions, and 64 species argues against a result generated by a single archipelago or a handful of taxa.

At the same time, positive regional means, positive species-level effects in 15 species, worse presence-cell log loss, and the fresh boreal non-support all show that source topology is not universally beneficial.

These exceptions are not noise to remove; they are the boundary conditions the next independent test must explain.

### 4.7 Plant evidence remains endpoint-limited

The GIFT endpoint-available subset shows the same overall C−R3 sign using the original frozen predictions, but only 118 of 404 confirmatory islands remain after strict endpoint-quality filtering.

That result cannot establish plant generality and cannot repair the terminal fresh plant attempt. It is retained solely as descriptive concordance.

## 5. Conclusions

Occupied-source network structure is not uniformly informative across mammal species. In a large exploratory layer, graph-path source continuity improved natural-prevalence held-out log loss beyond a strong source-aware reference, with gains dominated by improved absence prediction. A prospectively defined, previously sealed 96-species layer of rarer mammals did **not** replicate that overall effect. In the rarer layer, prediction asymmetry reversed toward improved presence prediction, and the actual graph was indistinguishable from degree- and edge-length-matched rewired networks.

These results replace a simple “source topology matters” conclusion with a boundary-condition result: the predictive role of internal source networks changes with species occupancy regime. The data are consistent with a source-network contrast window in which realized topology becomes informative only when occupied sources are sufficiently numerous and heterogeneous, but formal unimodality and causal dispersal mechanisms remain untested. Because the second layer uses the same island system, it is prospective species-wise validation rather than geographically independent replication.

## References

- Berlow, E. L., Knapp, R. A., Ostoja, S. M., Williams, R. J., McKenny, H., Matchett, J. R., Guo, Q., Fellers, G. M., Kleeman, P., Brooks, M. L. & Joppa, L. N. (2013). A network extension of species occupancy models in a patchy environment applied to the Yosemite toad (*Anaxyrus canorus*). *PLoS ONE* 8:e72200. https://doi.org/10.1371/journal.pone.0072200
- Carter, Z. T., Perry, G. L. W. & Russell, J. C. (2020). Determining the underlying structure of insular isolation measures. *Journal of Biogeography* 47:955–967. https://doi.org/10.1111/jbi.13778
- Cornell, H. V. & Harrison, S. P. (2014). What are species pools and when are they important? *Annual Review of Ecology, Evolution, and Systematics* 45:45–67. https://doi.org/10.1146/annurev-ecolsys-120213-091759
- Daniel, A., Savary, P., Foltête, J.-C., Khimoun, A., Faivre, B., Ollivier, A., Éraud, C., Moal, H., Vuidel, G. & Garnier, S. (2023). Validating graph-based connectivity models with independent presence–absence and genetic data sets. *Conservation Biology* 37:e14047. https://doi.org/10.1111/cobi.14047
- Denelle, P., Weigelt, P. & Kreft, H. (2023). GIFT—An R package to access the Global Inventory of Floras and Traits. *Methods in Ecology and Evolution* 14:2738–2748. https://doi.org/10.1111/2041-210X.14213
- Fahrig, L. (2013). Rethinking patch size and isolation effects: the habitat amount hypothesis. *Journal of Biogeography* 40:1649–1663. https://doi.org/10.1111/jbi.12130
- Hanski, I. (1994). Patch-occupancy dynamics in fragmented landscapes. *Trends in Ecology & Evolution* 9:131–135. https://doi.org/10.1016/0169-5347(94)90177-5
- König, C., Weigelt, P., Taylor, A., Stein, A., Dawson, W., Essl, F., Pergl, J., Pyšek, P., van Kleunen, M., Winter, M., Chatelain, C., Wieringa, J. J., Krestov, P. & Kreft, H. (2021). Source pools and disharmony of the world's island floras. *Ecography* 44:44–55. https://doi.org/10.1111/ecog.05174
- Ortiz-Rodríguez, D. O., Guisan, A., Holderegger, R. & van Strien, M. J. (2019). Predicting species occurrences with habitat network models. *Ecology and Evolution* 9:10457–10471. https://doi.org/10.1002/ece3.5567
- Schrader, J., Wright, I. J., Kreft, H. & Westoby, M. (2021). A roadmap to plant functional island biogeography. *Biological Reviews* 96:2851–2870. https://doi.org/10.1111/brv.12782
- Sillero, N., Biaggini, M. & Corti, C. (2018). Analysing the importance of stepping-stone islands in maintaining structural connectivity and endemicity. *Biological Journal of the Linnean Society* 124:113–125. https://doi.org/10.1093/biolinnean/bly033
- Wang, D., Zhao, Y., Tang, S., Liu, X., Li, W., Han, P., Zeng, D., Yang, Y., Wei, G., Kang, Y. & Si, X. (2023). Nearby large islands diminish biodiversity of the focal island by a negative target effect. *Journal of Animal Ecology* 92:492–502. https://doi.org/10.1111/1365-2656.13856
- Weigelt, P. & Kreft, H. (2013). Quantifying island isolation—insights from global patterns of insular plant species richness. *Ecography* 36:417–429. https://doi.org/10.1111/j.1600-0587.2012.07669.x

## Data and Code Availability Statement

The global island mammal occurrence data are publicly available from Dryad (DOI: 10.5061/dryad.hmgqnk9j2; version 6). Response-independent global island geography derives from the public island reference dataset archived at Figshare/UvA (DOI: 10.21942/uva.22788464.v5). The plant context uses GIFT database version 3.2.

An anonymized peer-review reproducibility ZIP containing review-neutralized analysis code, frozen focal analysis inputs and outputs, checksums, and figure-generation materials is supplied with this submission as Supporting Information. Raw biological response bytes are not redistributed; the underlying source data remain available at the public DOIs above. The public development-repository URL is intentionally omitted from the blinded manuscript. No new biological response access is required to regenerate the submission-facing results from the frozen analysis surfaces. The code and provenance bundle will be deposited in a permanent stable public archive with a DOI no later than publication.
