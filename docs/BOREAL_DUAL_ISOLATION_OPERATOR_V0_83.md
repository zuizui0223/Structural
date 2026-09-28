# Boreal dual-isolation source operator v0.83

## The structural problem

The v0.75 graph was designed for **validation**, not for ecological source
continuity. Its spatial blocks are connected components at a sparse radius.
Consequently, two islands in different heldout blocks have no path at that
radius by definition.

If that same graph were reused for the candidate C predictor, every training
source outside a heldout component would be unreachable. The source-continuity
predictor would therefore collapse exactly at the spatial-transfer boundary.

That is a design artifact, not an ecological result.

## v0.83 solution

v0.83 freezes a second graph from the same response-independent 42-island
coordinates.

- Construct symmetrized k-nearest-neighbor graphs for k = 1, 2, ...
- Choose the **smallest k** for which all 42 islands are connected.
- Break neighbor ties by great-circle distance, then island ID.
- Weight edges by haversine distance.
- Freeze the source-decay scale as the type-7 median of positive selected-edge
  lengths.
- Require at least one source-graph edge to cross a v0.75 validation block.

No beetle occurrence value is used to choose k, edge weights or kernel scale.

## Reference ladder

The distinction now matches the v0.55 hypothesis directly.

**R2** adds response-independent generic graph context: degree fraction, mean
shortest-path distance and closeness.

**R3** adds training-only species source context in ordinary geography:
occupancy breadth, nearest Euclidean occupied source and diffuse Euclidean
source pressure.

**C** adds training-only source continuity in the frozen kNN graph:
nearest occupied-source graph path and graph-path source pressure.

Thus C asks whether the *configuration of reachable occupied insular sources*
adds heldout information after classical external isolation and direct/diffuse
geographic source context are already represented.

## Training/heldout firewall

For pilot-response model fitting, a focal pilot island is defensively excluded
from its own occupied-source set. For confirmatory predictions, all and only
the frozen pilot islands can supply occupied sources.

Confirmatory occurrence values can never enter a source predictor.

## Claim boundary

The primary remains the v0.55 overall heldout C-minus-R3 log-loss contrast.
External isolation is context, not a required regime-switch interaction. Tail
checks cannot rescue a failed primary.
