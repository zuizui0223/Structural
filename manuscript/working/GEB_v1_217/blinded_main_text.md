# Geographic source graphs predict mapped island mammal ranges without distinct source territories

**Running title:** Geographic graphs and mapped sources

## Abstract

**Aim:** Coordinate-derived island networks may be mistaken for measured dispersal routes or evidence of indispensable source populations. We asked whether geographic source graphs improve prediction of curated mammal range-map labels and whether that gain requires distinct graph-defined source territories.

**Location:** 5,401 islands worldwide, with a separate temporal test in the Azores.

**Time period:** IUCN-2017-derived mammal distributions including historical native records; Azorean monitoring, 1999–2022.

**Major taxa studied:** Island mammals and Azorean forest arthropods.

**Methods:** Within a source compilation that excluded islands with no mapped mammals, we compared geographic k-nearest-neighbour graph features with a source-aware Euclidean reference and 20 degree-/edge-length-bin-matched rewired graphs. The preregistered ultrarare layer comprised 529 species with 1–4 positive pilot cells in the curated range-derived matrix. A response-free posthoc source-influence analysis included 212 species; a separate arthropod test evaluated later contraction following loss of modelled source access.

**Results:** In blocks containing mapped-positive mammal labels, original graph C improved binary log loss relative to R3 (C−R3 = **−0.596**, 95% interval **−0.744 to −0.464**) and outperformed **20/20** rewired graphs. However, the mean rewired graph retained **90.2%** of the original point-estimate improvement. Graph-derived source turnover was lower than matched random placements (beta difference **−0.262**, 95% interval **−0.317 to −0.208**). Independent arthropod source-loss prediction was not supported.

**Main conclusions:** A geographic graph can improve within-matrix prediction of curated map-positive mammal labels without uniquely differentiated modelled source territories. The results do not identify contemporary living source populations, actual dispersal, colonization, demographic redundancy or conservation priority.

## 1. Introduction

### 1.1 Isolation depends on where sources are

Classical island biogeography links isolation to colonization from a source region, most often a mainland. Later work showed that immigration can also reduce local extinction through the rescue effect (Brown & Kodric-Brown 1977), and that islands within an archipelago can function as sources, stepping stones or alternative colonization targets rather than as passive points between a mainland and a focal island (Sillero et al. 2018; Wang et al. 2023).

This makes island isolation inherently relational. Mainland distance, surrounding land area and generic network position describe important properties of the landscape, but they do not specify whether a neighbouring island actually contains the focal species. Global comparisons accordingly recover several distinct isolation dimensions rather than one universal distance metric (Weigelt & Kreft 2013; Carter et al. 2020), while surrounding habitat amount can alter effective isolation by changing the pool of potential immigrants (Fahrig 2013). Functional island-biogeographic frameworks likewise emphasize that dispersal and establishment processes can change the meaning of isolation among taxa (Schrader et al. 2021).

For a particular species, two islands with the same mainland distance can therefore have different source environments. One may lie near several occupied islands; the other may be surrounded by islands on which that species is absent. The relevant source landscape is partly a property of the species, not only of the focal island.

### 1.2 The same archipelago need not mean the same thing to every species

Species-pool theory emphasizes that regional availability constrains local assembly (Cornell & Harrison 2014), and island-flora work has explicitly shown that the identity of source pools matters for insular composition (König et al. 2021). Spatial metapopulation theory likewise allows connectivity to depend on which patches are occupied, and empirical work shows that connectivity can change as occupied populations change even when the physical patch network does not (Hanski & Ovaskainen 2000; Drake et al. 2022). Occupancy-dependent connectivity is therefore not itself a new idea.

Our narrower question is when the **exact arrangement of occupied source islands** carries information after simpler explanations have already been supplied. A nearby occupied island can matter simply because it is nearby; a species occupying many islands can appear well connected simply because its source pool is large. To isolate anything more specific, source-network information must be tested after island area, external isolation, regional prevalence, occupancy breadth and direct source proximity have already been represented.

That is the purpose of our strongest reference, R3. Candidate C adds only graph-path relationships to occupied source islands beyond this source-aware reference.

### 1.3 Network-level topology and source-node irreplaceability are different questions

Landscape-network conservation often uses topology to identify patches, corridors or stepping stones whose loss would disproportionately reduce connectivity (Baranyi et al. 2011; Conlisk et al. 2021). This makes an intuitive translation tempting: if a geographic graph improves ecological prediction, some occupied source nodes should be uniquely important. Yet a graph built from island coordinates is not an empirically observed dispersal network.

But network-level information and node-level irreplaceability are not logically equivalent. Several sources can jointly define a distinctive network configuration while remaining locally substitutable because their influence fields overlap. Conversely, sources can occupy distinct territories even if the exact adjacency adds little predictive information beyond ordinary source distance.

This distinction becomes especially important for species occupying few islands. Sparse source sets make the identity of occupied islands visible, but scarcity alone does not tell us whether those sources partition target space into unique territories or redundantly co-cover the same islands. We therefore separate two questions: **does exact source topology predict occurrence, and are the sources that compose that topology themselves spatially irreplaceable?**

### 1.4 A sequential sealed-response test

Our analysis developed in three disjoint mammal species layers within the same 5,401-island system.

First, an exploratory layer of 79 species with at least 13 pilot presences showed a broad natural-prevalence improvement when graph-path source terms were added to R3. The gain was driven mainly by improved absence prediction.

Second, because held-out responses for all nonfocal species remained unread, we prospectively defined a disjoint 96-species layer with 5–12 pilot presences. That layer did not replicate the overall gain; instead, presence prediction improved while absence prediction did not, and the actual graph was indistinguishable from degree- and edge-length-matched rewired nulls.

That unexpected reversal generated a new prediction. Before opening any further held-out values, we preregistered a third layer containing species with only 1–4 pilot presences. The primary prediction was now explicitly **presence opportunity**: if the 5–12 reversal marked a change in the role of source information rather than noise, graph-path source information should improve mapped-positive-cell prediction still more clearly in the sparsest layer. We also froze a topology-specificity test against 20 matched rewired graphs.

This sequential design lets us distinguish exploratory discovery, prospective non-replication and prospective replication while keeping the geographic system fixed.

### 1.5 From topology specificity to source redundancy and temporal consequence

The ultrarare held-out result created a mechanistic question that can be tested without reopening occurrence responses. If topology specificity arises because the few occupied sources divide the archipelago into distinct influence territories, source identity should turn over strongly across target islands. If instead the sources jointly cover similar target space, aggregate source importance could be balanced even while individual sources remain structurally redundant.

We therefore decomposed source influence across held-out island geometry using an alpha–gamma–beta effective-number partition and compared observed 2–4-source configurations with source-count- and bioregion-matched random placements. This diagnostic was frozen as response-free and could not alter the held-out occurrence evidence class.

A second, stronger question concerns time. Even a structurally distinctive or irreplaceable source need not have a demonstrated demographic consequence when lost. We therefore retain the independent three-wave BALA source-loss test as a separate endpoint: static network information, source-node structure and later contraction are tested rather than assumed to be interchangeable.

## 2. Methods

### 2.1 Global island mammal system

The source database contained a curated binary island–mammal range matrix for 5,592 islands (Barreto et al. 2021). Crucially, its compilers excluded islands with **zero mammals mapped by IUCN**, as well as islands with uncertain species assignments or unavailable environmental/realm metadata. The sampled island set was therefore selected partly by the mammal response, not simply by physical geography. Labels were assembled principally by intersecting IUCN-2017 mammal range polygons with GADM island polygons and manually curating them. Historical positive records for some native mammals extinct after human impacts were restored from other references. A positive cell is consequently not necessarily a field detection or currently extant population. Before the final analysis, one 15-island spatial block containing a previously exposed occurrence row was quarantined. A response-independent identity audit then removed 176 islands overlapping an earlier 318-island mammal stress-test system.

The final population contained **5,401 islands**. A response-independent partition assigned **1,275 islands** to a pilot set and **4,126 islands** to held-out evaluation. The held-out islands formed **168 bioregion × 10-degree spatial blocks** across 12 bioregions.

All three mammal layers used the same **already-selected** island population, pilot/held-out split and geographic covariates; those coordinates were not derived from focal held-out labels, but the upstream island selection did depend on mapped mammal occurrence. For these mammal analyses, 'presence', 'absence', and 'pilot occupied source' mean 1/0 cells in the curated range map rather than independent field confirmation. Both pilot and held-out labels share the same geographic map-generation process.

### 2.2 Reference hierarchy

R0 represented environmental state using bioregion, climate and topographic variables.

R1 added log island area, current external isolation and past isolation.

R2 added generic island-network context using nearest-island distance and response-independent neighbour pressure.

R3 added four training-only species-conditioned controls:

- global occupancy breadth;
- species × bioregion prevalence;
- nearest occupied-source Euclidean distance;
- diffuse occupied-source pressure.

Candidate C added two graph-path source terms beyond R3:

- graph-path nearest occupied-source distance;
- graph-path diffuse occupied-source pressure.

For pilot model fitting, every species-conditioned source feature excluded the complete focal validation block. Held-out predictions used only pilot islands as possible occupied sources. No held-out occurrence entered any source feature.

### 2.3 Models and scoring

All model tiers used deterministic pooled ridge logistic regression with lambda = 1 and no response-based hyperparameter tuning.

The general contrast was C−R3 binary log loss. Negative values favour the graph-path candidate.

For natural-prevalence analyses, C−R3 was first averaged within frozen held-out spatial blocks and then equally across blocks. Uncertainty used deterministic 10,000-replicate block bootstraps.

Presence-specific analyses used only blocks containing at least one mapped-positive cell. Absence-specific analyses retained all estimable held-out blocks.

### 2.4 Exploratory higher-occupancy layer

The first layer was selected from pilot data using at least 13 pilot presences and at least 13 pilot absences. This yielded **79 species** and **325,954 held-out island × species cells**.

Its C−R3 result and all subsequent class-specific and occupancy-breadth diagnostics are treated as nonconfirmatory exploratory evidence.

### 2.5 Preregistered 5–12-presence layer

The original held-out workflow decoded only the 79 focal species. Held-out values for all other mammal species remained unread.

We therefore prospectively defined a disjoint second layer using pilot information only: species with **5–12 pilot presences** and at least 13 pilot absences. This yielded **96 species** and **396,096 previously unread held-out cells**.

Before any second-layer held-out response was decoded, we froze R3, actual C, all held-out predictions, a graph-empty mask, and **20 deterministic rewired-C models**.

The preregistered primary asked whether overall natural-prevalence C−R3 was negative. Secondary predictions tested the original absence-focused signature, stronger gain where a graph-reachable source existed, and topology specificity relative to the rewired ensemble.

### 2.6 Preregistered ultrarare 1–4-presence layer

The reversal observed in the 5–12-presence layer generated a new hypothesis: for still rarer species, source connectivity may act primarily as **presence opportunity** rather than absence constraint.

Before opening any additional held-out responses, we fixed a third disjoint layer using **1–4 pilot presences**, at least 13 pilot absences, and exclusion of zero-pilot-presence species. This yielded **529 species**.

The held-out surface contained **2,182,654 island × species cells**. All actual-C predictions, graph-empty indicators and response-independent block isolation values were frozen before held-out response access.

The preregistered primary was the equal-block mean presence-cell C−R3 across held-out blocks containing at least one mapped-positive cell. Support required a negative point estimate and a block-bootstrap 95% upper bound below zero.

Secondary predictions were:

1. absence-cell C−R3 should be nonnegative;
2. among mapped-positive cells, graph-source-nonempty cells should show a more negative C−R3 than graph-empty cells;
3. presence benefit should attenuate with increasing external isolation;
4. the original geometry-derived topology should outperform its matched rewired counterparts on the presence metric.

The held-out ultrarare response was decoded once. No non-ultrarare held-out occurrence, pilot occurrence or excluded-island occurrence was decoded during that execution, and reruns were forbidden.

### 2.7 Geographic graph construction and matched rewired nulls

The source graph was **constructed from island centroid coordinates, not observed inter-island dispersal**. Those coordinates came from the **5,401 selected mammal-database islands**, not an independent list of all land masses. Islands with zero mapped mammals had already been excluded at source, so graph edges were geometry-derived *conditional on a response-selected node set*. Within each of 12 bioregions, pairwise centroid distances were calculated using the haversine metric. We symmetrized k-nearest-neighbor edges and selected the smallest region-specific k for which that region's graph was connected. The frozen graph comprised 5,401 nodes and 73,162 undirected edges, with region-specific k values from 4 to 49. Its links consequently represent a geographic modeling rule, not observed movement, currents, resistance or established stepping-stone pathways. The frozen model label *actual C* means this original constructed graph, not measured dispersal.

For topology-specificity tests, we generated 20 deterministic null graphs independently within each bioregion.

Rewiring used undirected degree-preserving double-edge swaps. Replacement edges were constrained to the same original edge-length quintile, preserving both degree sequence and edge-length-bin counts. Self-edges and duplicate edges were forbidden, and each final regional graph was required to remain connected.

The null ensemble preserved the number of islands, coordinates, degree sequence, counts of edges within each original length quintile, R3 variables and Euclidean occupied-source context. Only graph adjacency changed. **It did not preserve the local kNN construction rule, edge orientations, node-conditional neighborhood distances or shortest-path detours relative to straight-line distance.** Therefore, comparing the original graph with these surrogates isolates a particular sensitivity to geographic graph construction; it does not identify independently observed dispersal topology. Graph-based connectivity requires independent validation (Daniel et al. 2023).

For the 5–12 and 1–4 prospective layers, all null graphs and null predictions were frozen before held-out response access.

A later audit applied the same fixed null ensemble to the already-open exploratory 79-species layer. That audit is explicitly post hoc.

### 2.8 Response-free source-influence turnover

We analysed the 212 ultrarare species with 2–4 occupied pilot sources using only the frozen pilot occurrence state, the island graph and held-out island geometry. No held-out occurrence value was read.

For held-out target island t and occupied source s, graph access was (a_{ts}=\exp(-d_{ts}/\lambda_b)), where (d_{ts}) is frozen graph-path distance and (\lambda_b) is the frozen bioregion edge scale. For targets with positive total access, source shares were (p_{ts}=a_{ts}/\sum_s a_{ts}).

We calculated three effective-source quantities. Local alpha was the inverse of the target-mean Simpson concentration, (1/E_t[\sum_s p_{ts}^2]). Gamma was the inverse Simpson effective number of the source shares averaged across targets, (1/\sum_s(E_t[p_{ts}])^2). Their multiplicative ratio, beta = gamma/alpha, measured turnover in source identity across target space. Beta approaches one when targets see similar relative source composition and rises when different targets depend on different source subsets. We also recorded the mean target-level dominant-source share.

For each species, 1,000 random source configurations preserved both nominal source count and the exact number of sources in each bioregion. The frozen primary descriptive contrast was observed beta minus the species-specific null mean; uncertainty used a 10,000-replicate species bootstrap. This post-hoc response-free diagnostic could clarify mechanism but not upgrade the prospective held-out result.

### 2.9 Broader context and evidence boundaries

An earlier independent 318-island mammal stress test examined whether internal source information became stronger at extreme mainland isolation. That prediction was not supported.

A fresh 19-island boreal beetle system tested overall internal-source nonredundancy and also returned a non-supportive primary.

A separate GIFT plant system, using the Global Inventory of Floras and Traits framework (Denelle et al. 2023), reached a pristine global design but its fresh confirmatory execution terminated after response access began because one frozen checklist returned zero species rows. No fresh plant ecological primary was scored.

These systems constrain generality but are not pooled with the mammal occupancy-layer estimands.

### 2.10 Independent three-wave BALA source-loss test

The BALA database contains standardized arthropod sampling across the Azores over three major survey phases (Pozsgai et al. 2024). Structural first reconstructed the repeated pitfall-sampling denominator from Event metadata alone and froze a deterministic taxon partition before occurrence semantics were opened. A disjoint burned-pilot taxon set was used only to test estimability and produced no leverage effect estimate.

For confirmation, BALA1 was t0, BALA2 was t1 and BALA3 was t2. Eligible taxa had at least two occupied islands at BALA1, exactly one BALA1 source island absent at BALA2, and at least one BALA2 occupied island. The lost source itself was never scored as its own downstream target. This produced 20 confirmatory taxa and 64 target taxon–island rows before any BALA3 outcome was opened.

For each BALA2-surviving target island i, the preregistered exposure E_i was the fraction of its BALA1 graph-kernel source access contributed by the one source population lost before BALA2. The graph and exponential distance kernel were frozen from response-independent island geometry; the target island was excluded from its own source set.

Reference R2 included island fixed effects, BALA1 other-source count, BALA2 surviving-other-source count, nearest surviving-source Euclidean distance, diffuse surviving-source pressure, whether the target was occupied at BALA1, and response-independent BALA3 pitfall effort. Candidate C added only standardized E_i.

Validation was leave-one-confirmatory-taxon-out. Continuous variables were standardized using only the training-taxon complement. The primary was the equal-weight mean across estimable heldout taxa of within-taxon binary log-loss difference C−R2. Support required a negative point estimate and a 10,000-replicate taxon-bootstrap 95% upper bound below zero.

Only after all t0/t1 features, folds and standardization constants were frozen was the BALA3 surface opened once for eligible taxa. The endpoint was subsequent loss of observed occurrence in the standardized pitfall network, not whole-island extinction.

## 3. Results

### 3.1 Exploratory higher-occupancy species showed a broad natural-prevalence gain

The exploratory 79-species layer contained **325,954 held-out cells**, of which 5,620 were presences (1.72%).

Block-weighted C−R3 was **−0.001814**, with a 95% block-bootstrap interval of **−0.002817 to −0.000997**. The direction favoured C in **108/168 blocks**, **10/12 bioregions** and **64/79 species**.

The gain was strongly asymmetric. Absence-cell C−R3 was **−0.00580**, whereas presence-cell C−R3 was **+0.11644**. A class-balanced equal-block diagnostic favoured R3.

Thus the exploratory improvement primarily reduced overprediction of absences rather than improving mapped-positive-cell probabilities.

### 3.2 The 5–12-presence layer did not replicate the overall gain

The preregistered 96-species layer contained **396,096 held-out cells** and 1,233 mapped-positive cells.

Overall C−R3 was **−0.000442**, with a 95% interval of **−0.001098 to +0.000204**. The preregistered support criterion therefore failed.

The original prediction asymmetry also reversed. Absence-cell C−R3 was **+0.000430**, whereas presence-cell C−R3 was **−0.27744**.

The graph-source-support contrast had the predicted point direction but crossed zero. The original geographic kNN topology also showed no advantage over the 20 matched null graphs: actual C minus mean rewired C was **+1.56 × 10⁻⁶** with a 95% interval of **−2.12 × 10⁻⁴ to +2.04 × 10⁻⁴**, and the actual graph was better than 11/20 nulls.

This layer is therefore a prospective species-layer non-replication of the original overall effect, accompanied by a reversal toward presence improvement.

### 3.3 Ultrarare species prospectively reproduced a presence-opportunity signature

The preregistered ultrarare layer contained **529 species** and **2,182,654 held-out cells**. Only **2,347 cells** were presences, giving a held-out prevalence of **0.108%**. Mapped-positive cells occurred in 110 held-out blocks.

The preregistered primary was strongly supported. Presence-cell C−R3 was **−0.5963**, with a 95% block-bootstrap interval of **−0.7439 to −0.4645**.

The complementary absence prediction also behaved as preregistered. Absence-cell C−R3 was **+0.000236**, with a 95% interval of **+0.000077 to +0.000418**.

Thus, in the ultrarare layer, source-network information did not improve the overwhelmingly absent background. It specifically improved probability assigned to the small set of mapped-positive cells.

### 3.4 The ultrarare signal depended on source support and the original geographic kNN graph

Among mapped-positive cells, the graph-source-support prediction was supported.

The within-block difference between graph-nonempty and graph-empty presence effects was **−0.6705**, with a 95% interval of **−0.8009 to −0.5427** across 41 paired blocks.

Pooled presence-cell C−R3 was **−0.6948** when a graph-reachable occupied source existed and **−0.2033** when it did not.

The topology-specificity test was also supported. Actual C minus mean rewired C on the presence metric was **−0.0585**, with a 95% interval of **−0.0993 to −0.0163**. The actual graph outperformed **all 20** degree- and edge-length-matched null graphs.

The preregistered external-isolation attenuation prediction was not supported: Spearman rho was **−0.160**, with a bootstrap interval spanning zero.

### 3.5 Original geographic topology was not uniquely informative in the higher-occupancy exploratory layer

Applying the same matched-null framework post hoc to the original 79 species produced the opposite result.

Across all cells, actual C minus mean rewired C was **+0.000225**, with a 95% interval of **+0.000124 to +0.000330**. The actual graph was better than **0/20** matched nulls.

For presences, the corresponding contrast was positive but uncertain, and the actual graph was better than only 2/20 nulls.

Therefore the original natural-prevalence C−R3 gain should not be interpreted as evidence that the geography-derived kNN adjacency captured a uniquely observed ecological network. Its predictive value is better described as information in a network-transformed occupied-source context.

### 3.6 The broad near-ubiquitous layer was not estimable

A prospectively frozen broad-species rule required only 1–12 pilot absences. No species satisfied that rule. The layer terminated before held-out response access, and the threshold was not widened.

The broad end of the occupancy gradient therefore remains prospectively untested in this dataset.

### 3.7 Other systems limit generality

The earlier 318-island mammal test found descriptive source-information gains but did not support stronger effects at extreme isolation.

The fresh boreal beetle primary did not support a universal graph-path increment beyond its strong source-aware reference.

The GIFT fresh plant lane terminated without an ecological primary score. A strongly filtered exploratory subset showed the same overall sign as the original mammal analysis, but is not a plant replication.

### 3.8 Topology specificity did not arise from irreplaceable source territories

The response-free source-turnover test rejected the distributed-irreplaceability interpretation.

Across the 212 species with 2–4 occupied pilot sources, median local alpha effective source number was **1.439**, median target-surface gamma was **1.983**, and median beta source turnover was **1.132**.

Compared with source-count- and bioregion-matched random placements, observed beta turnover was markedly **lower**: mean actual−null beta = **−0.2620**, with a 95% species-bootstrap interval of **−0.3167 to −0.2076**. Only **48/212** species exceeded their null mean and only **2/212** exceeded the species-specific null 97.5th percentile; **34/212** fell below the null 2.5th percentile.

The components showed why. Observed local alpha exceeded the null by **+0.3939**, target-surface gamma by **+0.1344**, and mean target dominant-source share was **0.1390 lower** than the null. Thus map-positive pilot sources were more evenly represented overall but also co-contributed to the same target islands more strongly than random placements. They did not divide target space into unusually distinct source territories.

### 3.9 Independent temporal source-loss leverage did not improve heldout prediction

All 20 preregistered confirmatory taxa remained estimable after BALA3 access, contributing 64 target rows: **20 later contractions** and **44 persistences**.

The primary source-loss leverage prediction was not supported. Adding target-specific lost-access fraction E_i to R2 gave C−R2 = **+0.000674**, with a 95% taxon-bootstrap interval of **−0.02130 to +0.02558**. The point estimate was slightly adverse and the interval spanned zero.

Descriptive secondary summaries pointed in the hypothesized direction at the row level: mean E_i was **0.466** for later contractions and **0.287** for persistences, and the full-data standardized E_i coefficient was **+0.279**. However, these summaries were explicitly nonrescuing. Event-level effective-source-number decrement was not positively associated with contraction fraction (Spearman rho = **−0.180**).

Thus the independent three-wave test did not show that loss of a higher-leverage source adds generalizable predictive information beyond source count, remaining-source geometry, island identity and survey effort.

## 4. Discussion

**Measured-response boundary.** The mammal endpoint is a curated IUCN-derived positive label, not an independent survey of currently occupied island populations. The predictor and response both inherit geographic structure: graph edges use island centroids, while labels use range-polygon overlap. A map-to-map prediction can be real and reproducible without identifying biological stepping stones or actual migration. Moreover, the source compilation excluded islands with no IUCN-mapped mammals; the kNN graph therefore omits those land masses both as prediction targets and as potential geographic intermediate nodes. Prospective held-out species scoring prevents fitting to test labels but cannot undo this upstream response-dependent island selection. The size and direction of its inferential effects have not been estimated. A separate unpaired geography-frame comparison found median island areas of **6.40 km²** among these 5,401 modelled islands versus **4.08 km²** in a 17,883-island geography compilation (Weigelt et al. 2013). Numeric IDs differed. Strict matching found 3,878 candidate island pairs; 21.3% had an additional nearest Weigelt namepoint without a compatible original centroid. These do not prove mammal-zero islands or dispersal corridors. Spatial covariance from map construction and environmental suitability remains a competing explanation.

**Archived gain accounting.** The original ultrarare mapped-positive C−R3 log-loss contrast was −0.59626; the mean rewired C−R3 was −0.53773; their difference was −0.05853. Thus, 90.18% of the original point-estimate gain remained under the mean rewired graph, while 9.82% was original-kNN-specific relative to that null family. These are posthoc arithmetic fractions of loss differences, not causal mechanisms or uncertainty intervals. Degree-/edge-length-bin matching does not preserve local kNN neighbourhoods, edge orientation, or detour structure.


**Interpretive ceiling of the graph contrast.** The preregistered 20-graph result supports the original geographic kNN representation over its degree-/edge-length-bin-matched rewired surrogates for the ultrarare held-out presence endpoint. Because the original links were derived from island coordinates, not movement observations, this superiority may partly reflect the geographic locality and shorter detours preserved by the kNN construction but not required in its rewired competitors. Euclidean source distance and diffuse source pressure were controlled in R3, but that control does not make the graph edges independently observed ecological pathways. The effect is **geography-derived incremental prediction**, not evidence of measured dispersal routes.


### 4.1 Geographic prediction versus source-node irreplaceability

The preregistered ultrarare kNN graph outperformed its 20 rewired surrogates for within-map positive-label prediction beyond R3. This establishes predictive sensitivity to a geographic construction, not measured animal movement.

The response-free source analysis instead found lower source turnover, greater target co-coverage and weaker single-source dominance than matched random placements. Thus **map-positive pilot sources did not form unusually distinct target territories under this graph operator**. Neither result measures whether living populations can rescue one another.

### 4.2 Aggregate balance is not spatial complementarity

The new decomposition also corrects our interpretation of the earlier response-free source-leverage diagnostic.

That analysis summed each source's graph-access kernel over all target islands before calculating an inverse-Simpson effective source number. Mapped-positive pilot source sets had an aggregate effective source count **0.282** above matched random placement on average (95% interval **0.205–0.362**). We previously described this shorthand as greater spatial complementarity.

That wording was too strong.

Aggregate balance cannot distinguish two spatial organizations. Different sources can dominate different target regions, producing true target-space partitioning, or they can contribute similar total mass because they co-cover the same regions with comparable weights. The v1.181 alpha–gamma–beta partition distinguishes these cases, and the data support the second.

The map-positive ultrarare sources therefore combine **balanced aggregate contribution with greater-than-random local co-coverage and lower-than-random source turnover**. We call this *balanced structural redundancy*, with “redundancy” restricted to the frozen graph-access operator. It is not evidence that real dispersers are interchangeable or that populations are demographically redundant.

### 4.3 Collective geographic source configuration

A configuration of map-positive pilot islands can predict other range-map cells even when their graph-access fields overlap. Rewiring changes geographic paths without independently measuring movement. The spatial diagnostic disfavors distinct modelled source territories but cannot distinguish historical range structure, mapping dependence, habitat filtering and biological dispersal as causes.

### 4.4 Occupancy determines where the collective-topology signal appears

The adjacent occupancy layers constrain the result further.

The preregistered 5–12-presence layer improved mapped-positive-cell prediction but showed no advantage of the actual graph over matched rewired topologies. The higher-occupancy exploratory layer showed an absence-focused source-context gain, and the original geometry-derived topology was slightly worse than the matched null ensemble.

Therefore collective topology specificity is not a generic property of the 5,401-island graph. It appeared only in the sparsest prospectively tested occupancy layer.

This is not a monotonic rarity law: the ≥13-source layer was exploratory and the near-ubiquitous prospective layer was empty. The graph advantage arose in the predeclared group with 1–4 **map-positive** pilot islands.

### 4.5 Two limits on conservation translation

First, graph-based held-out prediction does not establish which living source populations are irreplaceable; the node analysis measures modelled geographic influence only.

Second, in the independent BALA system, lost-source graph leverage did not add predictive value for later contraction beyond surviving-source context and observation effort. This is a different taxonomic and temporal endpoint, not a direct replication of mammal geometry.

Together they separate (1) mapped-label prediction, (2) graph-defined source influence, and (3) future biological consequences. None justifies source-population management ranking without independent validation.

### 4.6 Relevance to island biogeography

Source-pool composition and island isolation remain fundamental ecological questions. This analysis offers a positive **map-prediction** example, not an observed immigration or rescue test. Pilot map-positive sources collectively inform a geographic model while their individual access fields overlap. Hubs, modelled stepping stones and graph-source nodes should not automatically be classified as viable dispersal populations.

### 4.7 Evidence boundaries

Several limits remain.

All mammal layers share one global island database, one island geometry, and one range-map-derived label process. Prospective sealing prevents fitting to the held-out source labels but does not produce independently surveyed occupancy, nor remove geographic autocorrelation inherited from range polygons.

“Ultrarare” refers only to 1–4 pilot map-positive island cells, not independent living population counts, global abundance or IUCN status.

The graph is a structural representation. Paths may traverse islands without focal-species occurrence, and neither the topology result nor the source-overlap result demonstrates realized animal movement.

The source-turnover analysis is post-hoc and response-free. It disfavors the proposed spatial interpretation of uniquely separated graph-source territories; it does not test demographic interchangeability or create a confirmatory biological endpoint.

Finally, structural redundancy is not demographic redundancy. We do not show that one occupied population can replace another after loss, prevent extinction, rescue a declining population or justify an intervention.

## 5. Conclusions

The strongest result is not evidence that rare island mammals disperse along a unique graph.

In the preregistered ultrarare mammal layer, the original coordinate-derived kNN graph improved held-out prediction of curated map-positive labels and outperformed its 20 matched rewires. Yet pilot map-positive sources showed **less** graph-defined target-space turnover than matched source placements, alongside greater local overlap and weaker target dominance.

The constructed geographic network was predictive **without** unusually distinct modelled source territories. That conclusion is conditional on the selected mammal-positive island universe and does not extend to excluded mammal-zero islands as prediction targets or physical graph nodes.

This separates a geographic graph's map-label predictive signal from the unmeasured conservation value of living populations. A map-positive source configuration can be predictive while its members' graph-defined access fields overlap strongly.

The independent BALA result adds a second boundary: source leverage did not improve held-out prediction of later contraction after source loss.

Together, these results argue against a common shortcut in connectivity interpretation. Predictive value of a network does not by itself identify critical source populations, and structural importance does not by itself establish future demographic consequence. Both translations require direct validation.

## References

- Barreto, E., Rangel, T. F., Pellissier, L. & Graham, C. H. (2021). Area, isolation and climate explain the diversity of mammals on islands worldwide. *Proceedings of the Royal Society B* 288:20211879. https://doi.org/10.1098/rspb.2021.1879
- Baranyi, G., Saura, S., Podani, J. & Jordán, F. (2011). Contribution of habitat patches to network connectivity: redundancy and uniqueness of topological indices. *Ecological Indicators* 11:1301–1310. https://doi.org/10.1016/j.ecolind.2011.02.003
- Berlow, E. L., Knapp, R. A., Ostoja, S. M., Williams, R. J., McKenny, H., Matchett, J. R., Guo, Q., Fellers, G. M., Kleeman, P., Brooks, M. L. & Joppa, L. N. (2013). A network extension of species occupancy models in a patchy environment applied to the Yosemite toad (*Anaxyrus canorus*). *PLoS ONE* 8:e72200. https://doi.org/10.1371/journal.pone.0072200
- Brown, J. H. & Kodric-Brown, A. (1977). Turnover Rates in Insular Biogeography: Effect of Immigration on Extinction. *Ecology* 58:445–449. https://doi.org/10.2307/1935620
- Carter, Z. T., Perry, G. L. W. & Russell, J. C. (2020). Determining the underlying structure of insular isolation measures. *Journal of Biogeography* 47:955–967. https://doi.org/10.1111/jbi.13778
- Castorani, M. C. N., Reed, D. C., Alberto, F., Bell, T. W., Simons, R. D., Cavanaugh, K. C., Siegel, D. A. & Raimondi, P. T. (2015). Connectivity structures local population dynamics: a long-term empirical test in a large metapopulation system. *Ecology* 96:3141–3152. https://doi.org/10.1890/15-0283.1
- Conlisk, E., Haeuser, E., Flint, A., Lewison, R. L. & Jennings, M. K. (2021). Pairing functional connectivity with population dynamics to prioritize corridors for Southern California spotted owls. *Diversity and Distributions* 27:844–856. https://doi.org/10.1111/ddi.13235
- Cornell, H. V. & Harrison, S. P. (2014). What are species pools and when are they important? *Annual Review of Ecology, Evolution, and Systematics* 45:45–67. https://doi.org/10.1146/annurev-ecolsys-120213-091759
- Dallas, T. A., Saastamoinen, M., Schulz, T. & Ovaskainen, O. (2020). The relative importance of local and regional processes to metapopulation dynamics. *Journal of Animal Ecology* 89:884–896. https://doi.org/10.1111/1365-2656.13141
- Daniel, A., Savary, P., Foltête, J.-C., Khimoun, A., Faivre, B., Ollivier, A., Éraud, C., Moal, H., Vuidel, G. & Garnier, S. (2023). Validating graph-based connectivity models with independent presence–absence and genetic data sets. *Conservation Biology* 37:e14047. https://doi.org/10.1111/cobi.14047
- Denelle, P., Weigelt, P. & Kreft, H. (2023). GIFT—An R package to access the Global Inventory of Floras and Traits. *Methods in Ecology and Evolution* 14:2738–2748. https://doi.org/10.1111/2041-210X.14213
- Drake, J., Lambin, X. & Sutherland, C. (2022). Spatiotemporal connectivity dynamics in spatially structured populations. *Journal of Animal Ecology* 91:2050–2060. https://doi.org/10.1111/1365-2656.13783
- Fahrig, L. (2013). Rethinking patch size and isolation effects: the habitat amount hypothesis. *Journal of Biogeography* 40:1649–1663. https://doi.org/10.1111/jbi.12130
- Hanski, I. (1994). Patch-occupancy dynamics in fragmented landscapes. *Trends in Ecology & Evolution* 9:131–135. https://doi.org/10.1016/0169-5347(94)90177-5
- Hanski, I. & Ovaskainen, O. (2000). The metapopulation capacity of a fragmented landscape. *Nature* 404:755–758. https://doi.org/10.1038/35008063
- König, C., Weigelt, P., Taylor, A., Stein, A., Dawson, W., Essl, F., Pergl, J., Pyšek, P., van Kleunen, M., Winter, M., Chatelain, C., Wieringa, J. J., Krestov, P. & Kreft, H. (2021). Source pools and disharmony of the world's island floras. *Ecography* 44:44–55. https://doi.org/10.1111/ecog.05174
- Moilanen, A. (2011). On the limitations of graph-theoretic connectivity in spatial ecology and conservation. *Journal of Applied Ecology* 48:1543–1547. https://doi.org/10.1111/j.1365-2664.2011.02062.x
- Ortiz-Rodríguez, D. O., Guisan, A., Holderegger, R. & van Strien, M. J. (2019). Predicting species occurrences with habitat network models. *Ecology and Evolution* 9:10457–10471. https://doi.org/10.1002/ece3.5567
- Poli, C., Hightower, J. & Fletcher, R. J. Jr. (2020). Validating network connectivity with observed movement in experimental landscapes undergoing habitat destruction. *Journal of Applied Ecology* 57:1426–1437. https://doi.org/10.1111/1365-2664.13624
- Pozsgai, G., Lhoumeau, S., Amorim, I. R., Boieiro, M., Cardoso, P., Costa, R., Ferreira, M. T., Leite, A., Malumbres-Olarte, J., Oyarzabal, G., Rigal, F., Ros-Prieto, A., Santos, A. M. C., Gabriel, R. & Borges, P. A. V. (2024). The BALA project: A pioneering monitoring of Azorean forest invertebrates over two decades (1999–2022). *Scientific Data* 11:368. https://doi.org/10.1038/s41597-024-03174-7
- Schrader, J., Wright, I. J., Kreft, H. & Westoby, M. (2021). A roadmap to plant functional island biogeography. *Biological Reviews* 96:2851–2870. https://doi.org/10.1111/brv.12782
- Sillero, N., Biaggini, M. & Corti, C. (2018). Analysing the importance of stepping-stone islands in maintaining structural connectivity and endemicity. *Biological Journal of the Linnean Society* 124:113–125. https://doi.org/10.1093/biolinnean/bly033
- Wang, D., Zhao, Y., Tang, S., Liu, X., Li, W., Han, P., Zeng, D., Yang, Y., Wei, G., Kang, Y. & Si, X. (2023). Nearby large islands diminish biodiversity of the focal island by a negative target effect. *Journal of Animal Ecology* 92:492–502. https://doi.org/10.1111/1365-2656.13856
- Weigelt, P., Jetz, W. & Kreft, H. (2013). Bioclimatic and physical characterization of the world's islands. *Proceedings of the National Academy of Sciences* 110:15307–15312. https://doi.org/10.1073/pnas.1306309110
- Weigelt, P. & Kreft, H. (2013). Quantifying island isolation—insights from global patterns of insular plant species richness. *Ecography* 36:417–429. https://doi.org/10.1111/j.1600-0587.2012.07669.x

## Data and Code Availability Statement

The global island mammal occurrence data are publicly available from Dryad (DOI: 10.5061/dryad.hmgqnk9j2; version 6). Response-independent global island geography derives from the public island reference dataset archived at Figshare/UvA (DOI: 10.21942/uva.22788464.v5). The plant context uses GIFT database version 3.2. The independent temporal boundary test uses the public BALA Azorean arthropod monitoring archive described by Pozsgai et al. (2024; DOI: 10.1038/s41597-024-03174-7).

Analysis scripts, preregistration contracts, frozen prediction surfaces, response-firewall receipts and figure-generation code will be supplied through an anonymized Supporting Information archive during peer review and deposited in a permanent public archive. The public development-repository URL is omitted from the blinded manuscript.
