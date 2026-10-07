# Balanced redundancy in ultrarare source networks — v1.183

## What v1.181 tested

The earlier v1.122 diagnostic showed that the total graph-access mass was more evenly distributed among the 2–4 observed occupied sources of ultrarare mammal species than among bioregion-matched random source placements.

That aggregate result left two incompatible spatial explanations:

1. **distributed irreplaceability** — different sources dominate different target regions;
2. **balanced redundancy** — multiple sources co-cover much of the same target region with relatively even contributions.

v1.181 was frozen before execution to distinguish these alternatives using no heldout occurrence response.

## Exact result

The exact NumPy 2.3.3 workflow completed the scientific calculation for 212 multi-source species before a push-only non-fast-forward failure.

Across species:

- median local alpha effective sources = **1.439**;
- median target-surface gamma effective sources = **1.983**;
- median beta source turnover = **1.132**;
- median target dominant-source share = **0.776**.

Relative to 1,000 source-count- and bioregion-matched random placements per species:

- **beta turnover: −0.2620**, species-bootstrap 95% CI **[−0.3167, −0.2076]**;
- local alpha effective sources: **+0.3939**;
- target-surface gamma effective sources: **+0.1344**;
- target dominant-source share: **−0.1390**.

Only **48/212** species had beta turnover above their null mean, only **2/212** exceeded the null 97.5th percentile, while **34/212** fell below the null 2.5th percentile.

## Interpretation

The distributed-irreplaceability hypothesis is not supported.

Observed source sets do not partition target space into more distinct source territories than matched random placements. They show the opposite pattern:

> **source influence overlaps more strongly across target islands, while total source contributions remain relatively balanced.**

This is **balanced redundancy** in the structural graph-access sense.

The two components matter:

- higher alpha means more sources contribute simultaneously at a typical supported target;
- higher gamma means aggregate source representation remains relatively even across the full target surface;
- lower beta means the identity/composition of influential sources turns over less from target to target;
- lower dominant share means individual targets are less winner-take-most than under matched random source placements.

Thus the positive v1.122 aggregate effective-source result should not be described as spatial complementarity. It is aggregate balance combined with unusually strong co-coverage.

## Why this matters for the ultrarare heldout result

The preregistered v1.119 occurrence result remains unchanged: actual island adjacency outperformed all 20 matched rewired topologies for realized presences in the 1–4-presence species layer.

v1.181 rules out one intuitive mechanism for that signal.

The topology-specific occurrence result is **not** accompanied by unusually strong source-territory partitioning or node-level spatial irreplaceability. The few occupied sources instead overlap more in the target space they structurally reach.

Therefore:

> **network-level topology specificity does not imply node-level irreplaceability.**

A source network can contain occurrence information as a collective configuration even when individual sources are structurally redundant with one another over target space.

This is a stronger conservation boundary than the earlier source-leverage story. Network-level predictive value cannot be translated automatically into a ranking of individual source populations.

## Relation to BALA

BALA independently showed that target-specific lost-source leverage did not improve heldout prediction of later contraction.

v1.181 does not explain the BALA result because the taxa and geography differ. It does, however, remove a proposed mechanistic bridge: the mammal static topology result no longer supports an interpretation in which the last few sources form distinct, individually irreplaceable spatial territories.

## Claim boundary

Supported:

- aggregate graph-access contribution is more balanced than matched random source placement (v1.122);
- target-space turnover in source influence is lower than matched random placement (v1.181);
- local effective source number is higher and local dominance is lower than matched random placement;
- the v1.119 actual-topology presence result remains supported.

Not supported:

- realized dispersal overlap;
- demographic redundancy;
- insurance effects;
- source-sink dynamics;
- causal persistence;
- a temporal range-contraction process;
- management equivalence of source islands.

“Balanced redundancy” refers only to the frozen graph-access operator.
