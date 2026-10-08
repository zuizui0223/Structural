# The “actual topology” semantic audit — v1.185

## What was actually observed?

Island centroids and mammal island occurrences were observed/compiled. The **links of the source graph were not animal movements, migratory corridors, shoreline crossings, measured dispersal probabilities, or empirically recorded island-to-island colonizations**.

The original reference code, `scripts/build_global_mammals_reference_operator_v1_40.py`, first computes haversine distances between island centroids within each bioregion, then symmetrizes k-nearest-neighbor edges. It chooses the *smallest k making each regional graph connected*; this selection uses island geometry alone, not species response.

The resulting 5,401-node, 73,162-edge graph includes 12 regional components. Frozen regional k values range from 4 to 49. The operator is defensible as a constructed **geographic connectivity representation**, not as observed ecological dispersal adjacency.

## What the 20 rewired nulls test

The preregistered null ensemble retains nodes, coordinates, edge count, each node's degree, edge-length-quintile totals and connectivity, while changing graph edges. **It does not preserve the original k-nearest-neighbor locality rule, node-conditional geographic neighbor structure, edge orientation, or shortest-path stretch relative to straight-line distance**.

The ultrarare result therefore establishes this narrower statement:

> In this frozen constructed-graph model and held-out occupancy data, graph-path source features add realized-presence information beyond a source-aware Euclidean reference, and the **original geography-derived kNN graph** performs better than its 20 degree-/edge-length-bin-matched rewired surrogates.

It does **not** establish:

> The biologically realized island dispersal network or uniquely important stepping-stone routes have been found.

The latter would require independently measured movement/dispersal, propagule exchange, landscape resistance, colonization events or another appropriate ecological response.

## Why this matters for the claim of novelty

The kNN graph is designed to respect locality. Rewiring it while preserving only coarse edge-length bins can destroy spatial embedding and inflate shortest-path detours, *even if the original geographic kNN graph contains no independent dispersal information*. Hence 20/20 superiority does not by itself isolate biological topology from a geometry-derived algorithmic advantage.

The Euclidean nearest-source and diffuse-source-pressure terms already in R3 make the held-out improvement interesting and nontrivial as **an empirical predictive residual**, but they do not eliminate this particular difference in the null construction or prove species movement along graph paths.

Similarly, response-free v1.181 showed *less*, not more, source-identity turnover than bioregion-matched random placements (mean delta −0.262, 95% CI −0.317 to −0.208). The v1.122 aggregate evenness result is not evidence that the observed sources occupy individually unique territories.

## Consequences

1. Preserve all frozen numerical results and the valid preregistered comparison. Do not relabel it as a failed statistical test.
2. Correct all unqualified language in the *current* manuscript: “observed/actual adjacency” means **original geography-derived kNN adjacency**, never measured dispersal links.
3. Do not claim that the 20-null comparison proves a species-specific dispersal mechanism or validates source-node conservation priority.
4. Do not change k, edge construction or null matching post hoc to rescue or elevate an ecological claim.
5. A future, genuinely independent study could compare measured flows or dated colonization with this frozen geographic hypothesis; it cannot be substituted by another same-response metric.

**Net status:** a valid predictive graph-representation result with ecological mechanism unresolved, not confirmation of observed movement topology.
