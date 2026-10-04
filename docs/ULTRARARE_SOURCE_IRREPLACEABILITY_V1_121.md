# Ultrarare source irreplaceability diagnostic v1.122

## Question

The v1.119 ultrarare result shows that exact island adjacency carries held-out presence information. This response-free diagnostic asks a narrower question: among species with the same number of occupied pilot sources, how spatially interchangeable are those sources?

The graph operator does **not** require occupied-source stepping-stone chains. Paths traverse the full frozen island graph, including islands without a focal-species pilot occurrence. The relevant quantity is therefore source leverage, not an occupied-population articulation point.

## Effective source number

For source s of species j, define A_js as the sum across 4,126 held-out geometry targets of exp(-graph_distance/bioregion_scale), with unreachable targets contributing zero. Let q_js=A_js/sum_s(A_js). The effective source number is N_eff=1/sum_s(q_js^2).

N_eff answers a concrete question: how many equally influential sources would produce the same concentration of graph-pressure leverage? Four nominal sources can therefore behave like four spatially complementary contributions, or like little more than one dominant contribution.

## Exact response-free result

The frozen pilot contains 529 ultrarare species and 877 occupied pilot source cells. Nominal source counts are 317 species with one source, 116 with two, 56 with three and 40 with four.

Among the 212 species with 2–4 sources:

- the median dominant source accounts for 0.661 of total graph-pressure mass;
- the median N_eff / nominal count is 0.744;
- 18 species have at least one source whose deletion would leave some held-out geometry targets with no graph-reachable pilot source.

By nominal source count, median N_eff is 1.584 for two-source species, 2.121 for three-source species and 2.567 for four-source species. Thus four observed pilot sources correspond to only about 2.57 equally influential graph-pressure contributions at the median.

## Matched placement null

For every 2–4-source species, 1,000 random source configurations were drawn from pilot islands while preserving both nominal source count and the exact number of sources in each bioregion.

The result does **not** support a simple clustering/redundancy story. Observed configurations are, on average, more complementary than the matched random placements:

- actual minus matched-null N_eff = +0.282;
- species-bootstrap 95% interval = [+0.205, +0.362];
- actual N_eff exceeds the species-specific null mean in 141/212 species;
- actual N_eff exceeds the null 97.5th percentile in 32/212 species.

The useful biological distinction is therefore not “few sources are clustered.” It is that **raw source count does not measure how much independent source-access leverage is retained, and the observed sources often occupy complementary parts of the island network**.

## Conservation hypothesis

The sharper hypothesis is:

> For species with only a few occupied island sources, population losses of equal numerical size can differ in structural consequence because sources differ in graph-pressure leverage and spatial complementarity.

This is more specific than saying “configuration matters.” It predicts that the relevant quantity for future conservation tests is the decrement in effective source number or source-access leverage after a population loss, not the count of populations lost alone.

## Claim boundary

This remains a post-hoc pilot-plus-geometry mechanism diagnostic. It uses no held-out occurrence values and does not change the v1.119 evidence hierarchy. It does not show realized movement, recolonization, demographic rescue, persistence, extinction risk, threatened status or an intervention effect. “1–4 pilot presences” also does not mean that only 1–4 global populations remain.

The decisive next test is temporal or otherwise independently response-sealed: does loss of a high-leverage source predict a larger subsequent contraction in occurrence than loss of a low-leverage source, after nominal source count and ordinary distance are held constant?
