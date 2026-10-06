# SW Finland colonization-topology hypothesis v1.165

## The question

The published study already established that colonization over ~70 years was strongly related to **how many islands a species historically occupied** and **distance to the nearest historically occupied island**. The Structural test therefore does not ask whether source availability matters.

It asks:

> **Among species whose complete historical source configuration can be reconstructed without reading the recent outcome, does the exact arrangement of historical source islands predict later colonization after source count and nearest-source distance are already supplied?**

That is the direct temporal counterpart to the global-mammal topology result.

## Why the t0 reconstruction is deliberately conservative

The archived analysis table is a complete-case modelling surface, not necessarily the full set of historical absences. A routed row safely establishes that a species was historically absent from that island, but a missing archive row is **not** evidence of historical presence.

Therefore Structural never takes the global complement of the archive.

For each species, v1.164 first recovers the historical occupied-island count response-independently. A species is topology-eligible only when

    archived historical-absence rows + historical occupied-island count = 471 islands.

Only for such a species is the complement of the routed absence rows an exact historical source set. Species with incomplete accounting are excluded **before any recent colonization outcome is opened**. At least 30 exact-source species are required or the route stops.

This protects the key mechanism from a subtle but serious error: missing complete-case rows cannot be converted into source populations.

## Why this is stronger mechanistically than another static occurrence test

Historical occupancy precedes the recent colonization endpoint by decades. Once exact t0 source identities are proven, the source state can be frozen before later outcomes are used.

The causal ordering is:

    exact historical source state
        → frozen graph / null topologies / predictions
        → later colonization outcome.

BALA tested the opposite demographic direction—source loss followed by later contraction—and did not support a general lost-source-leverage effect. The SW Finland system asks whether source configuration instead has a more direct role in **colonization opportunity**.

## Strong reference

A favorable result will not be allowed to mean merely “nearby sources matter.”

R0 already contains frozen recipient-island state, species traits and the t0-safe pair-specific `Gowdis_traits` historical community-trait dissimilarity.

R3 further contains, all recomputed from the exact historical source set:

- historical source count;
- nearest historical source distance;
- diffuse Euclidean historical-source pressure.

C adds only graph-path source information.

Twenty connected degree- and edge-length-bin-matched rewired graphs provide the topology null.

## Continuous sparse-source prediction

For every eligible potential colonization event, finite-source theory supplies a response-free configuration-sensitivity score:

    S_i(n) = [(M−n)/(n(M−1))] × H_i,

where H_i is the heterogeneity of target-to-source spatial weights and n is the exact historical source count.

The primary therefore does not depend on choosing an arbitrary “rare species” threshold. A separate nonrescuing mechanism test asks whether actual-topology advantage is stronger for high-S events.

## Evidence boundary

The geography and temporal endpoint are independent of the global mammal system, but the original paper already reports broad colonization results. This route is therefore **literature-outcome-aware**, not pristine fresh confirmation.

What remains prospectively protected is the row-level future endpoint relative to the exact new topology hypothesis. Exact-source eligibility, the source graph, matched nulls, spatial split, reference and predictions must all be frozen before confirmatory outcome access.
