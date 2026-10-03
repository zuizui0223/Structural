# Macro dual-isolation synthesis v1.97

## Revised central result

The strongest current conclusion is no longer that species-conditioned source topology is broadly informative across mammals.

Instead:

> **The predictive role of occupied-source networks changes with species occupancy regime.** In the original 79-species exploratory layer, graph-path source continuity improved natural-prevalence held-out log loss and acted mainly as absence-constraint information. In a preregistered, previously sealed 96-species layer restricted to 5–12 pilot presences, that overall gain did not replicate, the presence/absence asymmetry reversed, and the actual graph was indistinguishable from degree- and edge-length-matched rewired nulls.

This second layer is prospective held-out evidence at the species-response level, but it uses the same islands, geography and reference model. It is therefore **not geographically independent replication**.

## Layer 1: original exploratory mammal signal

- 79 species selected from the pilot with at least 13 presences and 13 absences.
- 4,126 held-out islands in 168 blocks.
- C−R3 = **−0.001814**.
- 95% block-bootstrap interval = **[−0.002817, −0.000997]**.
- 108/168 blocks, 10/12 bioregions and 64/79 species had negative effects.
- The gain was driven primarily by true absences:
  - absence C−R3 = **−0.00580**;
  - presence C−R3 = **+0.11644**.
- The gain weakened with external isolation and broader occupancy.
- Graph-source-nonempty cells showed substantially larger gains than graph-empty cells.

Evidence class: **nonconfirmatory exploratory**.

## Layer 2: preregistered sealed rare-species validation

Before any new held-out values were read, the second layer was fixed to species with **5–12 pilot presences** and at least 13 pilot absences.

This produced:

- **96 species**;
- 1,275 pilot islands;
- 4,126 held-out islands;
- **396,096 held-out cells**;
- held-out prevalence = **0.00311**;
- 20 deterministic rewired graph nulls preserving degree sequence and edge-length-bin counts within bioregions.

All R3, actual-C and 20 rewired-C predictions were frozen before any second-layer held-out response was decoded.

### P1 — overall C−R3

Observed:

- C−R3 = **−0.000442**;
- 95% block-bootstrap interval = **[−0.001098, +0.000204]**.

Result: **not supported**.

The point direction remained slightly negative, but the preregistered support criterion failed.

### P2 — occupancy-constraint signature

Prediction: absences improve, presences do not.

Observed:

- absence C−R3 = **+0.000430**;
- presence C−R3 = **−0.27744**;
- class-balanced equal-block diagnostic = **−0.13841**.

Result: **not supported; direction reversed**.

In the rarer species layer, C improved realized-presence prediction strongly and did not improve absence prediction.

### P3 — stronger effect where graph sources exist

Observed:

- nonempty-minus-empty contrast = **−0.00603**;
- 95% CI = **[−0.01626, +0.00118]**;
- paired blocks = 166.

Result: **not supported**, although the point direction matched the preregistered prediction.

### P4 — actual topology versus rewired topology

Observed:

- actual C minus mean rewired C = **+1.56 × 10⁻⁶**;
- 95% CI = **[−2.12 × 10⁻⁴, +2.04 × 10⁻⁴]**;
- actual graph better than **11/20** null graphs.

Result: **not supported**.

The actual graph carried no detectable advantage over degree- and edge-length-matched rewired topology in the rarer species layer.

## Ecological interpretation

The new evidence changes the interpretation in an important way.

### 1. Source-network information is not a general mammalian isolation axis

The original 79-species signal cannot be generalized to all mammal species. A preregistered, previously sealed rarer-species layer failed the primary replication.

### 2. Predictive asymmetry depends on occupancy regime

The original layer behaved mainly as **absence constraint**.

The rarer layer showed the opposite qualitative signature: **presence probabilities improved strongly while absence probabilities did not**.

Thus “source topology = constraint information” is itself a boundary-specific interpretation, not a universal mechanism.

### 3. Topology specificity is absent at the sparse-species boundary

The degree- and distance-matched rewiring test is especially important. In the rare layer, actual graph topology was not better than null topology.

This means that when occupied sources are very sparse, graph-path features may primarily encode generic source scarcity/geometry rather than specific network organization.

### 4. The source-network contrast-window hypothesis survives only as a boundary hypothesis

The combined evidence is compatible with a contrast window:

- very rare species (5–12 pilot presences): no supported overall gain; no topology specificity;
- low-to-moderate occupancy species in the exploratory layer: strongest negative C−R3;
- broad species within the exploratory layer: weaker C−R3.

But the current data do **not** establish formal unimodality. The only prospective result is the failure of the rare-species layer to replicate.

## Evidence hierarchy

1. **Sealed 96-species mammal layer** — preregistered species-wise held-out validation in the same geographic system; primary non-replication.
2. **Original 79-species global mammal layer** — large, spatially held-out, nonconfirmatory exploratory signal.
3. **Boreal beetles** — valid fresh local primary non-support.
4. **GIFT fresh lane** — terminal without ecological score.
5. **GIFT endpoint-available continuation** — nonconfirmatory, strongly selected descriptive concordance only.
6. **Historical 318-island mammal test** — nonfresh stress context.

## Revised defensible central claim

> The topology of occupied island sources is not uniformly informative across mammal species. A large exploratory layer showed a broad natural-prevalence gain dominated by improved absence prediction, but a preregistered, previously sealed rarer-species layer failed to replicate the overall gain, reversed the prediction asymmetry, and showed no advantage of the actual graph over matched rewired topologies. Species occupancy therefore appears to delimit when source-network structure carries distinct island-biogeographic information.

## Claim boundary

Permitted:

- the original 79-species layer showed a broad exploratory C−R3 gain;
- the sealed 96-species layer did not replicate that gain;
- prediction behaviour differed qualitatively between occupancy layers;
- actual topology was not distinguishable from matched null topology in the rare layer;
- species occupancy is a plausible boundary condition on source-network information.

Not permitted:

- global confirmation of source-network topology;
- universal occupancy-constraint mechanism;
- formal proof of a unimodal contrast window;
- topology-specificity in the original 79-species layer;
- geographically independent replication;
- causal dispersal-path interpretation.
