# When do source islands matter? Occupancy state changes what connectivity predicts

**Running title:** Occupancy-dependent source roles

## Abstract

**Aim:** We asked whether occupied-source connectivity merely changes in strength as species become sparse, or changes what it predicts: absence constraint versus presence opportunity. We then asked when exact observed island topology adds information beyond source number, direct source proximity and generic geography, and whether static source leverage predicts later contraction.

**Location:** 5,401 islands worldwide; independent temporal test in the Azores.

**Time period:** Contemporary compiled mammal distributions; Azorean BALA monitoring phases spanning 1999–2022.

**Major taxa studied:** Native mammals; Azorean forest arthropods.

**Methods:** We analysed three disjoint mammal species layers defined from pilot occupancy while preserving later held-out responses. Graph-path source information was tested beyond a source-aware reference and against 20 degree- and edge-length-matched rewired graphs. We then tested a derived source-loss prediction in an independent three-wave arthropod dataset.

**Results:** In an exploratory ≥13-presence layer, C improved absences but worsened realized presences. A preregistered 5–12-presence layer failed that constraint-signature prediction in the opposite direction: presence C−R3 was **−0.277**, absence C−R3 was **+0.000430**, and topology specificity was absent. That reversal generated a preregistered 1–4-presence hypothesis. In 529 previously unread species, presence C−R3 was **−0.596** (95% interval **−0.744 to −0.464**) and observed adjacency outperformed **20/20** matched null topologies. In BALA, lost-source leverage did not improve held-out prediction of later contraction (C−R2 = **+0.000674**, 95% interval **−0.02130 to +0.02558**).

**Main conclusions:** Source connectivity did not simply strengthen as occupancy declined; its predictive role shifted from constraint-like to opportunity-like, with exact topology specificity emerging only at the sparse extreme. Static spatial importance did not imply later demographic consequence.

**Keywords:** connectivity; island biogeography; isolation; macroecology; mammals; occupancy; rare species; source populations; stepping stones

## 1. Introduction

### 1.1 Isolation depends on where sources are

Classical island biogeography links isolation to colonization from a source region, most often a mainland. Later work showed that immigration can also reduce local extinction through the rescue effect (Brown & Kodric-Brown 1977), and that islands within an archipelago can function as sources, stepping stones or alternative colonization targets rather than as passive points between a mainland and a focal island (Sillero et al. 2018; Wang et al. 2023).

This makes island isolation inherently relational. Mainland distance, surrounding land area and generic network position describe important properties of the landscape, but they do not specify whether a neighbouring island actually contains the focal species. Global comparisons accordingly recover several distinct isolation dimensions rather than one universal distance metric (Weigelt & Kreft 2013; Carter et al. 2020), while surrounding habitat amount can alter effective isolation by changing the pool of potential immigrants (Fahrig 2013). Functional island-biogeographic frameworks likewise emphasize that dispersal and establishment processes can change the meaning of isolation among taxa (Schrader et al. 2021).

For a particular species, two islands with the same mainland distance can therefore have different source environments. One may lie near several occupied islands; the other may be surrounded by islands on which that species is absent. The relevant source landscape is partly a property of the species, not only of the focal island.

### 1.2 The same archipelago need not mean the same thing to every species

Species-pool theory emphasizes that regional availability constrains local assembly (Cornell & Harrison 2014), and island-flora work has explicitly shown that the identity of source pools matters for insular composition (König et al. 2021). Spatial metapopulation theory likewise allows connectivity to depend on which patches are occupied, and empirical work shows that connectivity can change as occupied populations change even when the physical patch network does not (Hanski & Ovaskainen 2000; Drake et al. 2022). Occupancy-dependent connectivity is therefore not itself a new idea.

Our narrower question is when the **exact arrangement of occupied source islands** carries information after simpler explanations have already been supplied. A nearby occupied island can matter simply because it is nearby; a species occupying many islands can appear well connected simply because its source pool is large. To isolate anything more specific, source-network information must be tested after island area, external isolation, regional prevalence, occupancy breadth and direct source proximity have already been represented.

That is the purpose of our strongest reference, R3. Candidate C adds only graph-path relationships to occupied source islands beyond this source-aware reference.

### 1.3 Occupancy state may change what connectivity predicts

The same connectivity representation need not carry the same information throughout a species' occupancy range. One possibility is quantitative: source information simply becomes stronger or weaker as occupancy changes. A more consequential possibility is qualitative: the same source representation changes **what it predicts**, acting mainly as a constraint on unlikely occurrences in one occupancy state and as an opportunity signal for realized presences in another. Only after that distinction is made does the additional question of exact observed topology arise.

When a species occurs on only a few islands, the remaining occupied populations are sparse. If those populations are potential sources, their exact positions in the archipelago may be especially consequential: a target island may have or lack access to one of very few remaining occupied islands.

At higher occupancy, source islands become more numerous. Connectivity may summarize a broad source environment and help constrain where a widespread species is unexpectedly absent. At lower occupancy, source information may instead identify the few targets where occurrence remains plausible. Either role could occur without the exact observed adjacency being uniquely informative; topology specificity is a stronger condition.

This distinction matters for conservation. Network-based conservation commonly asks which patches or islands maintain connectivity, but that question presumes that the role of network position is comparable across species. If occupancy state changes the meaning of source connectivity, conservation metrics should be conditional on how many source populations remain.

A second distinction is equally important: a patch can be structurally important without its loss having a demonstrated demographic consequence. Graph-theoretic connectivity alone cannot answer questions about regional persistence (Moilanen 2011), and empirical metapopulation studies show that connectivity can affect colonization, extinction and occupancy differently rather than through one universal response (Castorani et al. 2015; Dallas et al. 2020). Direct validation of connectivity metrics against realized movement or later population dynamics remains uncommon and can produce metric-specific results (Poli et al. 2020). We therefore treat present-occurrence information and later source-loss consequence as separate endpoints rather than assuming that one validates the other.

Here, “rare”, “rarer” and “ultrarare” refer only to occupancy within our frozen pilot island set, not to abundance, threat status or IUCN category.

### 1.4 A sequential sealed-response test

Our analysis developed in three disjoint mammal species layers within the same 5,401-island system.

First, an exploratory layer of 79 species with at least 13 pilot presences showed a broad natural-prevalence improvement when graph-path source terms were added to R3. The gain was driven mainly by improved absence prediction.

Second, because held-out responses for all nonfocal species remained unread, we prospectively defined a disjoint 96-species layer with 5–12 pilot presences. That layer did not replicate the overall gain; instead, presence prediction improved while absence prediction did not, and the actual graph was indistinguishable from degree- and edge-length-matched rewired nulls.

That unexpected reversal generated a new prediction. Before opening any further held-out values, we preregistered a third layer containing species with only 1–4 pilot presences. The primary prediction was now explicitly **presence opportunity**: if the 5–12 reversal marked a change in the role of source information rather than noise, graph-path source information should improve realized-presence prediction still more clearly in the sparsest layer. We also froze a topology-specificity test against 20 matched rewired graphs.

This sequential design lets us distinguish exploratory discovery, prospective non-replication and prospective replication while keeping the geographic system fixed.

### 1.5 From spatial leverage to a temporal conservation test

The ultrarare mammal result and a response-free pilot-plus-geometry diagnostic generated a sharper conservation prediction. If two species lose the same number of occupied island populations, subsequent contraction might differ according to how much of the surviving targets' pre-loss source access was carried by the population that disappeared.

That prediction cannot be tested with a single spatial snapshot. A loss event must precede a later outcome. We therefore froze an independent three-wave test in the Biodiversity of Arthropods of the Laurisilva of the Azores (BALA) monitoring programme, which repeatedly sampled standardized native-forest sites across Azorean islands (Pozsgai et al. 2024). BALA1 defined the pre-loss source state, BALA1→BALA2 defined source loss, and BALA2→BALA3 supplied the later occupancy endpoint.

This independent temporal test was designed before BALA3 confirmatory outcomes were opened and could not rescue or redefine the mammal results.

## 2. Methods

### 2.1 Global island mammal system

The source database contained native mammal presence–absence records for 5,592 islands. Before the final analysis, one 15-island spatial block containing a previously exposed occurrence row was quarantined. A response-independent identity audit then removed 176 islands overlapping an earlier 318-island mammal stress-test system.

The final population contained **5,401 islands**. A response-independent partition assigned **1,275 islands** to a pilot set and **4,126 islands** to held-out evaluation. The held-out islands formed **168 bioregion × 10-degree spatial blocks** across 12 bioregions.

All three occupancy layers used this same island population, pilot/held-out split and response-independent geography.

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

Presence-specific analyses used only blocks containing at least one realized presence. Absence-specific analyses retained all estimable held-out blocks.

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

The preregistered primary was the equal-block mean presence-cell C−R3 across held-out blocks containing at least one realized presence. Support required a negative point estimate and a block-bootstrap 95% upper bound below zero.

Secondary predictions were:

1. absence-cell C−R3 should be nonnegative;
2. among realized presences, graph-source-nonempty cells should show a more negative C−R3 than graph-empty cells;
3. presence benefit should attenuate with increasing external isolation;
4. actual topology should outperform matched rewired topologies on the presence metric.

The held-out ultrarare response was decoded once. No non-ultrarare held-out occurrence, pilot occurrence or excluded-island occurrence was decoded during that execution, and reruns were forbidden.

### 2.7 Matched rewired topology nulls

For topology-specificity tests, we generated 20 deterministic null graphs independently within each bioregion.

Rewiring used undirected degree-preserving double-edge swaps. Replacement edges were constrained to the same original edge-length quintile, preserving both degree sequence and edge-length-bin counts. Self-edges and duplicate edges were forbidden, and each final regional graph was required to remain connected.

The null ensemble therefore preserved the number of islands, coordinates, degree sequence, edge-length distribution, R3 variables and Euclidean occupied-source context. Only graph adjacency changed. This explicit null comparison is important because graph-based connectivity is a model representation that requires empirical validation rather than an assumed dispersal mechanism (Daniel et al. 2023).

For the 5–12 and 1–4 prospective layers, all null graphs and null predictions were frozen before held-out response access.

A later audit applied the same fixed null ensemble to the already-open exploratory 79-species layer. That audit is explicitly post hoc.

### 2.8 Broader context and evidence boundaries

An earlier independent 318-island mammal stress test examined whether internal source information became stronger at extreme mainland isolation. That prediction was not supported.

A fresh 19-island boreal beetle system tested overall internal-source nonredundancy and also returned a non-supportive primary.

A separate GIFT plant system, using the Global Inventory of Floras and Traits framework (Denelle et al. 2023), reached a pristine global design but its fresh confirmatory execution terminated after response access began because one frozen checklist returned zero species rows. No fresh plant ecological primary was scored.

These systems constrain generality but are not pooled with the mammal occupancy-layer estimands.

### 2.9 Independent three-wave BALA source-loss test

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

Thus the exploratory improvement primarily reduced overprediction of absences rather than improving realized-presence probabilities.

### 3.2 The 5–12-presence layer did not replicate the overall gain

The preregistered 96-species layer contained **396,096 held-out cells** and 1,233 realized presences.

Overall C−R3 was **−0.000442**, with a 95% interval of **−0.001098 to +0.000204**. The preregistered support criterion therefore failed.

The original prediction asymmetry also reversed. Absence-cell C−R3 was **+0.000430**, whereas presence-cell C−R3 was **−0.27744**.

The graph-source-support contrast had the predicted point direction but crossed zero. Actual topology also showed no advantage over the 20 matched null graphs: actual C minus mean rewired C was **+1.56 × 10⁻⁶** with a 95% interval of **−2.12 × 10⁻⁴ to +2.04 × 10⁻⁴**, and the actual graph was better than 11/20 nulls.

This layer is therefore a prospective species-layer non-replication of the original overall effect, accompanied by a reversal toward presence improvement.

### 3.3 Ultrarare species prospectively reproduced a presence-opportunity signature

The preregistered ultrarare layer contained **529 species** and **2,182,654 held-out cells**. Only **2,347 cells** were presences, giving a held-out prevalence of **0.108%**. Realized presences occurred in 110 held-out blocks.

The preregistered primary was strongly supported. Presence-cell C−R3 was **−0.5963**, with a 95% block-bootstrap interval of **−0.7439 to −0.4645**.

The complementary absence prediction also behaved as preregistered. Absence-cell C−R3 was **+0.000236**, with a 95% interval of **+0.000077 to +0.000418**.

Thus, in the ultrarare layer, source-network information did not improve the overwhelmingly absent background. It specifically improved probability assigned to the small set of realized presences.

### 3.4 The ultrarare presence signal depended on source support and actual adjacency

Among realized presences, the graph-source-support prediction was supported.

The within-block difference between graph-nonempty and graph-empty presence effects was **−0.6705**, with a 95% interval of **−0.8009 to −0.5427** across 41 paired blocks.

Pooled presence-cell C−R3 was **−0.6948** when a graph-reachable occupied source existed and **−0.2033** when it did not.

The topology-specificity test was also supported. Actual C minus mean rewired C on the presence metric was **−0.0585**, with a 95% interval of **−0.0993 to −0.0163**. The actual graph outperformed **all 20** degree- and edge-length-matched null graphs.

The preregistered external-isolation attenuation prediction was not supported: Spearman rho was **−0.160**, with a bootstrap interval spanning zero.

### 3.5 Actual topology was not uniquely informative in the higher-occupancy exploratory layer

Applying the same matched-null framework post hoc to the original 79 species produced the opposite result.

Across all cells, actual C minus mean rewired C was **+0.000225**, with a 95% interval of **+0.000124 to +0.000330**. The actual graph was better than **0/20** matched nulls.

For presences, the corresponding contrast was positive but uncertain, and the actual graph was better than only 2/20 nulls.

Therefore the original natural-prevalence C−R3 gain should not be interpreted as evidence that the exact observed island adjacency was uniquely informative. Its predictive value is better described as information in a network-transformed occupied-source context.

### 3.6 The broad near-ubiquitous layer was not estimable

A prospectively frozen broad-species rule required only 1–12 pilot absences. No species satisfied that rule. The layer terminated before held-out response access, and the threshold was not widened.

The broad end of the occupancy gradient therefore remains prospectively untested in this dataset.

### 3.7 Other systems limit generality

The earlier 318-island mammal test found descriptive source-information gains but did not support stronger effects at extreme isolation.

The fresh boreal beetle primary did not support a universal graph-path increment beyond its strong source-aware reference.

The GIFT fresh plant lane terminated without an ecological primary score. A strongly filtered exploratory subset showed the same overall sign as the original mammal analysis, but is not a plant replication.

### 3.8 Independent temporal source-loss leverage did not improve heldout prediction

All 20 preregistered confirmatory taxa remained estimable after BALA3 access, contributing 64 target rows: **20 later contractions** and **44 persistences**.

The primary source-loss leverage prediction was not supported. Adding target-specific lost-access fraction E_i to R2 gave C−R2 = **+0.000674**, with a 95% taxon-bootstrap interval of **−0.02130 to +0.02558**. The point estimate was slightly adverse and the interval spanned zero.

Descriptive secondary summaries pointed in the hypothesized direction at the row level: mean E_i was **0.466** for later contractions and **0.287** for persistences, and the full-data standardized E_i coefficient was **+0.279**. However, these summaries were explicitly nonrescuing. Event-level effective-source-number decrement was not positively associated with contraction fraction (Spearman rho = **−0.180**).

Thus the independent three-wave test did not show that loss of a higher-leverage source adds generalizable predictive information beyond source count, remaining-source geometry, island identity and survey effort.

## 4. Discussion

### 4.1 Connectivity changes role, not only strength

The most important result is not that connectivity is beneficial or harmful on average, nor that occupancy can enter connectivity calculations. The stronger empirical result is that **the predictive role of the same source representation changes across occupancy regimes**.

In the exploratory ≥13-presence layer, C improved absence prediction (C−R3 = −0.00580) but worsened realized-presence prediction (+0.11644). Before the 5–12 held-out response was opened, that class-specific constraint signature was preregistered: absences should improve and presences should not. It failed in the opposite direction. Presence C−R3 became −0.27744 while absence C−R3 became +0.000430. That unexpected reversal then generated the sealed 1–4 presence-opportunity hypothesis, which was strongly supported: presence C−R3 fell to −0.59626 while absence C−R3 remained slightly adverse at +0.000236.

A descriptive class-selectivity contrast, presence C−R3 minus absence C−R3, therefore moves from +0.12224 in the exploratory layer to −0.27787 in the 5–12 layer and −0.59649 in the 1–4 layer. We do not attach a post-hoc trend test to these three values: the ≥13 layer is exploratory and the strata were not preregistered as a continuous gradient. The point is qualitative rather than inferentially monotonic—the source representation changed from an absence-focused constraint signal to a presence-focused opportunity signal.

The fitted graph terms are concordant with this switch. In the exploratory layer, standardized graph-source distance was positive (+0.285) and graph-source pressure negative (−0.0705); both prospective lower-occupancy fits reversed those directions (distance −0.622 and −0.402; pressure +0.0127 and +0.00465 for the 5–12 and 1–4 layers, respectively). Because these terms are jointly fitted, correlated and separately standardized in each layer, their magnitudes are diagnostic rather than causal effect sizes. The held-out class-specific reversal is the stronger evidence.

Only at the sparse extreme did this opportunity signal become topology-specific: in the 1–4 layer, the actual adjacency outperformed all 20 matched rewired topologies. Thus occupancy affected both **what connectivity predicted** and, at the sparsest tested state, **whether the exact observed network mattered**.

### 4.2 For ultrarare species, the remaining source islands are not interchangeable

The topology-null result gives the ultrarare pattern a specific island-biogeographic meaning.

The null graphs preserved how many links each island had and the distribution of link distances. If the ultrarare presence benefit depended only on generic network density, degree or source-distance scale, the rewired graphs should have performed similarly to the actual graph.

They did not.

On the preregistered presence metric, the observed adjacency outperformed every one of the 20 matched nulls.

This suggests that, for species occupying very few islands, **which islands remain occupied and how those islands sit within the archipelago can matter beyond the number and distance of sources alone**.

The result is predictive, not demographic. It does not show animals moving along graph edges, nor does it demonstrate rescue or recolonization. But it narrows the ecological hypothesis considerably: the remaining occupied islands are not spatially interchangeable.

### 4.3 Scarcity explains topology exposure, but not the role inversion

A simple response-free sampling identity explains why source identity should become proportionally more visible when few sources remain. For a target with (M) possible source islands and non-negative access weights (w_j), condition on exactly (n) occupied sources. If the occupied set is an (n)-subset of the possible sources, total source access (A) has (E[A]=n\mu) and (Var(A)=n(M-n)\sigma^2/(M-1)), where (\mu) and (\sigma^2) describe the target-specific source-weight field. Hence

[
CV^2(A)=\frac{M-n}{n(M-1)}\frac{\sigma^2}{\mu^2}.
]

Whenever source positions are heterogeneous ((\sigma^2>0)), relative configuration sensitivity decreases as (n) increases. Sparse occupancy therefore does not manufacture a topology effect; it exposes spatial heterogeneity that is increasingly averaged over as more alternative sources are occupied. This identity explains why exact configuration should become easier to expose as source number falls, but it does **not** predict the class-specific reversal from absence constraint to presence opportunity. The role inversion is therefore an empirical result rather than a mathematical consequence of source scarcity. The identity also does not turn the three layers into a prospectively tested continuous rarity gradient.

### 4.4 The 5–12-presence layer reveals inversion before topology specificity

The 96-species layer is important precisely because its preregistered constraint prediction failed in the opposite class-specific direction.

That result separates two transitions that would otherwise be conflated. First, source information changed role: presence probabilities improved while absence predictions no longer did. Second, exact adjacency still remained indistinguishable from matched nulls. The subsequent 1–4 result therefore did not merely continue a smooth increase in “connectivity strength”; it added topology specificity to an opportunity-like signal that had already appeared in the 5–12 layer.

This argues against a simple linear rarity effect. A species can enter a presence-opportunity regime before the fine arrangement of its occupied sources becomes detectably informative beyond source scarcity and generic geometry.

The current evidence therefore supports **occupancy-regime dependence in function and topology specificity**, not monotonicity.

### 4.5 The exploratory higher-occupancy gain is source-context information, not proof of topology

The original 79-species result remains useful, but its interpretation changes after the matched-null audit.

Graph-path C improved natural-prevalence prediction, mainly by reducing loss on absences. Yet matched rewired graphs performed slightly better than the actual adjacency.

The exploratory result therefore cannot support a claim that the real island topology itself constrained occupancy. Instead, the graph transformation appears to provide a useful representation of occupied-source context that is not uniquely tied to the observed adjacency.

This distinction matters because “network metric improves prediction” and “the real network topology matters” are different ecological claims.

### 4.6 Spatial source leverage is not yet a validated conservation-priority metric

The mammal occupancy layers show that source-island configuration can contain species-specific occurrence information, and the response-free leverage diagnostic shows that nominal population count does not equal spatially independent source access. Among ultrarare mammal species with 2–4 occupied pilot sources, the dominant source contributed a median **66.1%** of graph-pressure leverage and the median effective-to-nominal source ratio was **0.744**. Observed source configurations were also more complementary than matched random placements.

Those facts generated a concrete management hypothesis: losing one high-leverage occupied source might have a larger future consequence than losing one low-leverage source.

The independent BALA test directly evaluated that prediction with temporal ordering. BALA1 source state was fixed before BALA1→BALA2 source loss, and leverage features were frozen before BALA3 outcomes were opened. Yet target-specific lost-source leverage did **not** improve heldout prediction of subsequent contraction beyond a strong reference.

This result fits a broader caution in connectivity ecology: structural or movement-related connectivity does not automatically imply population persistence, and different dynamic endpoints can respond differently to the same connectivity description (Moilanen 2011; Castorani et al. 2015; Dallas et al. 2020). Our contribution is to show this boundary explicitly across two evidence types: a topology-specific static occurrence signal in ultrarare mammals, followed by an independent temporal non-support result for source-loss leverage in BALA.

This distinction is important. **Spatial irreplaceability and temporal consequence are not the same quantity.** A source island can occupy a distinctive position in a static source network without its loss providing generalizable information about which surviving populations will disappear later.

The descriptive BALA difference in E_i between contraction and persistence rows is insufficient to overturn the heldout primary. It could reflect weak signal, taxon heterogeneity, imperfect occurrence as a demographic endpoint or residual ecological structure, but none of those explanations was preregistered as a rescue route.

The strongest conservation statement is therefore deliberately limited:

> connectivity assessments may need to account for species occupancy state and source configuration, but Structural source leverage is **not currently validated as a general population-prioritization metric**.

The present analyses do not show that protecting a high-leverage island prevents extinction, that restoring it causes recolonization, or that graph paths are realized dispersal routes. Such claims require additional independent temporal, demographic, genetic or intervention evidence.

### 4.7 Relation to island-biogeographic theory

Classical island biogeography links occurrence and turnover to the supply of colonists from source regions. The rescue effect further predicts that conspecific immigration can reduce local extinction.

Our results add a species-state qualification to that source-based view: source connectivity can change predictive role even when the response endpoint remains occurrence.

The same physical island can be weakly or strongly isolated depending on which other islands the focal species occupies. More importantly, the type of information carried by those occupied islands changes across occupancy regimes.

For the higher-occupancy exploratory layer, graph-transformed source context primarily constrained absences and did not depend uniquely on the actual adjacency. In the 5–12 layer, the preregistered constraint signature reversed toward presence opportunity without topology specificity. In the ultrarare layer, that presence-opportunity role strengthened and became specific to the observed adjacency.

Thus island isolation is not only multidimensional; it is also **species-state dependent**.

### 4.8 Evidence boundaries

Several features prevent a stronger claim.

First, all three mammal layers share the same island geography. The ultrarare result is prospective species-response evidence, not geographically independent replication.

Second, occupancy strata are based on pilot island occurrences, not abundance or formal conservation status. “Ultrarare” in this paper therefore means rare in the island-occupancy data, not necessarily globally threatened.

Third, the broad near-ubiquitous layer was non-estimable. We have not demonstrated a complete occupancy-response curve or a formal contrast window.

Fourth, occurrence prediction cannot distinguish contemporary colonization from demographic rescue, historical occupancy legacy or unmeasured biotic processes.

Finally, the fresh boreal non-support and terminal GIFT attempt limit generality, while the independent BALA three-wave test specifically shows that the mammal source-leverage conservation hypothesis did not improve heldout prediction of later contraction.

## 5. Conclusions

Island isolation cannot always be reduced to a species-invariant property of the target island.

The mammal layers did not show a single connectivity effect that merely grew stronger as occupancy declined. In the higher-occupancy exploratory layer, source context primarily improved absences. A preregistered 5–12 layer unexpectedly reversed toward presence opportunity, and that reversal prospectively motivated the 1–4 layer, where the presence signal strengthened and the actual adjacency outperformed degree- and distance-matched null networks.

Occupied-source connectivity therefore changed **what it predicted** across occupancy regimes, while exact topology specificity emerged only in the sparsest prospectively tested layer. But the independent BALA three-wave test adds an equally important boundary: **spatial source leverage did not improve heldout prediction of subsequent contraction after a source population was lost**.

Source-network structure can therefore be informative about present occurrence without automatically becoming a conservation-priority metric for future population loss. The ecological endpoint must be validated explicitly: occurrence, colonization, extinction, persistence and movement are not interchangeable consequences of connectivity. Future management use requires independent evidence that a proposed connectivity or leverage measure predicts the particular temporal or demographic outcome used to justify intervention.

## References

- Berlow, E. L., Knapp, R. A., Ostoja, S. M., Williams, R. J., McKenny, H., Matchett, J. R., Guo, Q., Fellers, G. M., Kleeman, P., Brooks, M. L. & Joppa, L. N. (2013). A network extension of species occupancy models in a patchy environment applied to the Yosemite toad (*Anaxyrus canorus*). *PLoS ONE* 8:e72200. https://doi.org/10.1371/journal.pone.0072200
- Brown, J. H. & Kodric-Brown, A. (1977). Turnover Rates in Insular Biogeography: Effect of Immigration on Extinction. *Ecology* 58:445–449. https://doi.org/10.2307/1935620
- Carter, Z. T., Perry, G. L. W. & Russell, J. C. (2020). Determining the underlying structure of insular isolation measures. *Journal of Biogeography* 47:955–967. https://doi.org/10.1111/jbi.13778
- Castorani, M. C. N., Reed, D. C., Alberto, F., Bell, T. W., Simons, R. D., Cavanaugh, K. C., Siegel, D. A. & Raimondi, P. T. (2015). Connectivity structures local population dynamics: a long-term empirical test in a large metapopulation system. *Ecology* 96:3141–3152. https://doi.org/10.1890/15-0283.1
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
- Weigelt, P. & Kreft, H. (2013). Quantifying island isolation—insights from global patterns of insular plant species richness. *Ecography* 36:417–429. https://doi.org/10.1111/j.1600-0587.2012.07669.x

## Data and Code Availability Statement

The global island mammal occurrence data are publicly available from Dryad (DOI: 10.5061/dryad.hmgqnk9j2; version 6). Response-independent global island geography derives from the public island reference dataset archived at Figshare/UvA (DOI: 10.21942/uva.22788464.v5). The plant context uses GIFT database version 3.2. The independent temporal boundary test uses the public BALA Azorean arthropod monitoring archive described by Pozsgai et al. (2024; DOI: 10.1038/s41597-024-03174-7).

Analysis scripts, preregistration contracts, frozen prediction surfaces, response-firewall receipts and figure-generation code will be supplied through an anonymized Supporting Information archive during peer review and deposited in a permanent public archive. The public development-repository URL is omitted from the blinded manuscript.
