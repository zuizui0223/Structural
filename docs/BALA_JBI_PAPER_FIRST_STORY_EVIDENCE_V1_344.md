# Paper-first synthesis v1.344 — Temporal reassembly and spatial convergence in island forest arthropods

**2 November 2026 · Source-backed manuscript positioning, not a new biological experiment. Original BALA taxon/plot source scorers v1.314/v1.316/v1.318 remain SEALED.**

## Current publication decision

Use the **BALA original source alone** as the central field-data paper. Do **not** merge the fundamentally different methods/years/sites of the SLAM/PRIBES/Madeira/Galápagos datasets into a pooled test of causality. Those independent source attempts have provided useful ecological context and identification ceilings, but are not an equivalent experimental replicate.

**Proposed title:** *Stable richness conceals spatial convergence and taxonomic replacement in island forest arthropods.*

**Main question:** When local assemblages maintain comparable numbers of species across decades, does their composition stay stable — and, if identities change, do different forest plots become **more similar or more different**?

This framing is stronger than simply saying "richness and beta diversity are different": a physically matched, multi-island long-term survey lets us quantify *both* the within-site replacement signal **relative to contemporaneous sampling heterogeneity** and the *direction* of spatial compositional change. It also produces a clear negative inference boundary: a spatial pattern in source-detected species does **not** identify colonization, survival or invasive source flux.

## Published prior art and exact gap

[Pozsgai et al. (2026), *Scientific Reports* 16:27703](https://doi.org/10.1038/s41598-026-57146-5) already showed relatively stable long-term **abundance, biomass and species richness** in the Azorean BALA arthropod system, with heterogeneous trends of individual endemic and introduced taxa. Its Discussion explicitly identifies nuanced **community species replacement** as an unanswered question. Their overall stability, extinction-debt commentary and forest conservation background are **prior authors' results**, not new discoveries here.

Our distinct derived estimands are:

1. Matched physical-transect **temporal species identity** changes, separated from richness-difference components, and assessed against observed within-period disjoint half-trap heterogeneity.
2. Matched contemporaneous *between-transect* spatial species replacement (Simpson beta) changes **within islands**, separate from within-site temporal beta.
3. Whether local alpha richness and spatial community distinctiveness move in opposite directions, with island-level deletion and the pre-existing fixed half-Event partition sensitivity.

The data and sample design are the **published BALA original** archived as [DOI 10.15468/rpdkx9](https://doi.org/10.15468/rpdkx9); original source ZIP SHA256 `4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2`.

## Draft abstract (229 words)

Species richness is widely used to track biodiversity change, yet stable richness need not imply persistence of species identities or spatial differentiation among communities. We examined published long-term arthropod surveys of Azorean native forests, spanning approximately two decades across 29 repeatedly sampled transects on seven oceanic islands. We compared ground-dwelling spiders and beetles using fixed sampling opportunities, separating compositional replacement within transects from changes in species similarity among transects within each island. To quantify sampling heterogeneity, we contrasted inter-campaign dissimilarity with differences between disjoint subsets of sampling events within each campaign. Although aggregate richness had previously been reported as broadly stable, temporal Sørensen dissimilarity exceeded within-campaign half-sample differences in all seven islands for both spiders (island-equal excess +0.191) and beetles (+0.221). Beetle assemblages became spatially more similar on average (island-equal change in Simpson spatial beta −0.175), whereas spider assemblages showed a small and variable increase (+0.022). The beetle direction remained negative across 18 predefined complementary sampling partitions and after omission of any single island, although only four islands individually homogenized. In three of those four islands, mean local beetle richness increased. Thus, local richness and community identity can follow different spatial trajectories even where long-term species replacement is widespread. Our results concern observed assemblages, not directly measured local extinctions, immigrations, or causal invasion processes. Island monitoring should evaluate temporal replacement and spatial distinctiveness alongside richness.

*Avoid claiming a statistically significant between-guild interaction or a causal homogenization mechanism without an independent landscape-level design.*

## Evidence ledger: units are everything

| Endpoint | Source-grounded observation | Independent ecological n | Evidence / constraint |
|---|---|---:|---|
| Published abundance/richness trend | Broadly stable aggregate response, heterogeneous endemic/introduced taxa | 30 author plots; published prior art | Pozsgai et al. 2026, **not** Structural novelty |
| Temporal B1–B3 community beta | Source original spiders Sørensen 0.470, beetles 0.616; Simpson replacement 0.349 / 0.511 | 29 spider / 28 beetle physical plots | Frozen v1.314, observational detection |
| Comparable richness, different identity | 23/57 paired site×guild comparisons showed net richness change ≤1 taxon yet nontrivial identity replacement | 57 paired source responses, same physical plots; not 57 independent islands | Frozen v1.314; source site vs taxon pairs nested |
| Source half-trap detection benchmark | B1→B3 temporal dissimilarity exceeds same-phase half-sample mismatches by +0.1908 spiders / +0.2212 beetles | 29 / 26 eligible physical plots; **7 islands** | [v1.316 original source](https://github.com/zuizui0223/Structural/actions/runs/40636604430); 9 source-ID partitions are pseudoreplicated sensitivity |
| Spatial community trajectory | Island-equal Simpson B3−B1: **beetles −0.1753**, spiders +0.0224 | 28 / 29 physical plots; 49 / 56 **dependent pairs** | [v1.318 original source](https://github.com/zuizui0223/Structural/actions/runs/40806865705); 4/7 beetle islands negative, 3/7 positive |
| Sampling-opportunity direction | Original 18 source half-Event estimates: beetles **18/18 negative**, spiders only 13/18 positive | Same original plots/Events, NOT 18 new studies | Frozen v1.318, no independent detection correction |
| Robustness to an island's disproportionate influence | Leave any one island out: beetle spatial Simpson mean remains **−0.2341 to −0.1111**; spiders' spatial mean crosses zero | 7 nonindependent leave-one-island-out summaries | **v1.344 source-free**; NOT seven replication p-values |
| Richness versus spatial homogenization | Flores, São Jorge and Santa Maria had spatially homogenizing beetles despite higher mean source site richness | 3 of the 4 homogenizing islands | Frozen v1.318/v1.319, no species-specific cause |

Because the BALA ecological evidence comes from **one source archive**, the table rows are *nested derived estimates of the same field study*, not independent validations. The 7 island means are the relevant broadest geographic comparisons, and the source 29 physical forest transects are the plot-level units; 4,620 originally selected Event records are sampling opportunities, **not** replicated landscapes.

## Figure plan (three main figures; no speculative maps or mechanisms)

**Figure 1 — Same richness can hide changing membership.** Show the original paired physical plots and B1/B3 timeline. Two panels: spiders and beetles, depicting island-level temporal Sørensen dissimilarity and the matched within-campaign half-trap benchmark. Mark all seven islands with positive excess; show source eligible plot denominators 29/26, no independent p-values from split salts.

**Figure 2 — Long-term replacement does not determine whether communities converge.** Each of seven island contexts has two guild points for *B3−B1 spatial Simpson beta*. Negative values mean spatial homogenization, positive values differentiation. Show the observed island-equal shifts **−0.1753** beetles versus **+0.0224** spiders; preserve **4/7 vs 3/7** source island heterogeneity. An adjacent noninferential robustness panel can show seven source-free leave-one-island-out estimates: all Beetle negative but two Spider opposite to its full-sample mean. The repeated site pairs remain dependent.

**Figure 3 — Conservation implication of an alpha–beta mismatch.** Original island scatter of change in mean local Beetle richness (x) against change in spatial Simpson beta (y). Clearly label Flores, São Jorge, Santa Maria where alpha increases but spatial Simpson beta falls, plus Terceira where both alpha and beta fall. Do not depict introduced species flow or native forest "rescue" — neither was measured. Insets show per-island physical site counts, especially Santa Maria n=2.

Supplementary figures and tables should contain the alternative spatial Sørensen metric, source beta richness-difference decomposition, nine salts × complementary half partitions, raw site/pair denominators, exact B1/B3 source-period definitions and a source-count reconciliation from the authors' 30 published transects to the 29 physically matched response cohort.

## Arguments to anticipate before submission

**Q1 — Could the turnover be non-detection rather than biodiversity reorganization?** Original within-campaign half-trap Sørensen dissimilarity was substantial, **0.295 spiders and 0.423 beetles**, so this is a real concern. The across-campaign half-trap values were **0.486 and 0.644**. The observed positive difference is narrower than a detection-corrected occupancy estimate; cite as *observed change beyond contemporaneous sampling heterogeneity*, not true replacement, local disappearance, or recruitment.

**Q2 — Is Beetle homogenization an effect of one island or the smallest island?** No single original island is necessary for the negative island-equal direction: **7/7 leave-one-island-out summaries remain negative**, range **−0.2341 to −0.1111**. That is a descriptive source-free stability result, not a probability. Individual island signs still vary (4 negative/3 positive), and forest patches may have unmeasured common environmental histories.

**Q3 — Is this simply a richness-gradient identity?** Local mean source Beetle richness **rose on 3 of 4 islands with negative spatial Simpson delta**; thus simple richness loss is not a necessary correlate. Simpson replacement is nonetheless influenced by pool composition, taxonomic resolution and uneven detections. No claim that local endemic richness rose, nor that invaders drove homogenization.

**Q4 — Why spiders versus beetles?** Both show excess temporal identity change in 7/7 island means, but their *spatial* summary differs. The only warranted explanation is that the spatial coordination of species detection changes may vary between guilds. The current data do not establish a formal Beetle-minus-Spider interaction, different dispersal mechanism, or identical detection probabilities.

**Q5 — Is this a new multi-region confirmation of island biogeography?** No. It is the same published BALA Azorean archive, observationally analyzed with distinct metrics. The SLAM native/exotic forest association from [PR #463](https://github.com/zuizui0223/Structural/pull/463), independent PRIBES introduced-pool non-support [PR #462](https://github.com/zuizui0223/Structural/pull/462), and many source design STOPs are *context* and should NOT be pooled quantitatively or claimed causal support.

## Target and completion gate

**Candidate journal: [Journal of Biogeography](https://onlinelibrary.wiley.com/page/journal/13652699/homepage/forauthors.html)**, because the theoretical claim is about spatiotemporal biogeographic trajectories within a multi-island system, not a global macroecological law. Its published scope welcomes ecologically meaningful biogeographic patterns across local-to-global scales and well-documented unusual case studies, but demands a conceptual advance: present **temporal replacement × spatial convergence** as distinct axes, not merely "alpha ≠ beta". A more ambitious *Ecography* pitch would require stronger generalizable theory, and *GEB* would require broader-scale external support; no acceptance prediction is made.

Before submission, the actual source-free manuscripts/figures need:
- final automated reconciliation of **v1.314, v1.316, v1.318, v1.344** exact original SHA and site denominator, with original source species not reopened;
- plot-level uncertainty method that respects repeated plot identities and multi-fragment clusters; **not** naive 49/56 independent pair-level confidence intervals;
- explicit taxon/season/half-trap-detection limitations, with no extinction or immigration mechanism language;
- literature comparison beyond the original 2026 Scientific Reports BALA paper, especially biotic homogenization and island beta diversity literature, to ensure true added novelty.

## Execution evidence and status

Original 7-island BALA source SHA256 `4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2`. Original taxon workflows **v1.314** [#40615946292](https://github.com/zuizui0223/Structural/actions/runs/40615946292), **v1.316** [#40636604430](https://github.com/zuizui0223/Structural/actions/runs/40636604430), **v1.318** [#40806865705](https://github.com/zuizui0223/Structural/actions/runs/40806865705) were each executed in their one-shot evidence workflow and subsequently SEALED.

Source-only v1.344 [#41411530987](https://github.com/zuizui0223/Structural/actions/runs/41411530987) SUCCESS **4 tests**. Uses only pinned v1.316 source numerical aggregate SHA `1a65cb237271560b56484e992eca76ee6bf082048c55a6f3f68eb0f5a2436871` and v1.318 SHA `f4e61ddbbd255d3a35a46fb0254273889516984b82479b3949e5edd79853af02`. New original Event/Occurrence rows opened **zero**. Script `scripts/bala_temporal_spatial_paper_sourcefree_v1_344.py`; tests `tests/test_bala_temporal_spatial_paper_sourcefree_v1_344.py`; protocol `development/bala_temporal_spatial_cross_axis_sourcefree_protocol_v1_344.json`.

**Scientific state: paper-worthy observational result identified; not yet a submitted or causally validated manuscript.** The separately developed mapped-mammal GEB paper remains SCIENTIFIC HOLD, 0 genuinely pristine confirmatory systems admitted; protected original mammal/BioTIME/RLS/S2–S4 responses unopened and eBird unused.
