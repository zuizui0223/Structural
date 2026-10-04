# Ultrarare source irreplaceability diagnostic v1.121

The v1.119 ultrarare result shows that exact island adjacency carries held-out presence information. This diagnostic asks a narrower response-free question: among species with the same number of occupied pilot sources, how spatially interchangeable are those sources?

The graph operator does **not** require occupied-source stepping-stone chains. Paths traverse the full frozen island graph, including islands without a focal-species pilot occurrence. Therefore the relevant quantity is source leverage, not an occupied-population articulation point.

For source s of species j, define A_js as the sum across 4,126 held-out geometry targets of exp(-graph_distance/bioregion_scale), with unreachable targets contributing zero. Let q_js=A_js/sum_s(A_js). The effective source number is N_eff=1/sum_s(q_js^2). Equal leverage gives N_eff equal to the nominal source count; domination by one source drives N_eff toward 1.

For species with 2-4 pilot sources, the matched null samples 1,000 alternative pilot-source configurations while preserving both nominal source count and the exact number of sources in each bioregion.

This is a post-hoc pilot-plus-geometry mechanism diagnostic. It uses no held-out occurrence values and cannot upgrade the v1.119 evidence hierarchy. It does not infer realized dispersal, recolonization, demographic rescue, persistence, threatened status, or an intervention effect. Its role is to make the biological hypothesis concrete: raw source count and spatially effective source redundancy need not be the same quantity.
