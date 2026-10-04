# Occupancy-regime island-ecology synthesis v1.119

## Central ecological question

Island isolation is usually treated as a property of the target island: distance from a mainland, amount of nearby land, or position in an archipelago. For a focal species, however, the relevant source landscape also depends on which other islands are actually occupied.

The current Structural evidence supports a more specific question:

> **Does the ecological role of island connectivity change as a species occupies fewer islands?**

The answer from the global mammal system is yes in the predictive sense, but not as a simple monotonic law.

## Evidence layers in one geographic system

All three mammal layers use the same final 5,401-island geographic system, the same 1,275 pilot islands, the same 4,126 held-out islands and the same strong R3 reference. They differ only in the pilot-defined occupancy of the focal species.

### Layer U — ultrarare species: 1–4 pilot presences

This layer was prospectively defined before any of its held-out responses were opened.

- 529 species
- 2,182,654 held-out island × species cells
- 2,347 realized presences
- held-out prevalence 0.108%
- 110 held-out blocks containing at least one realized presence

The preregistered presence-opportunity primary was strongly supported:

- presence-cell C−R3 = **−0.5963**
- 95% block-bootstrap interval = **[−0.7439, −0.4645]**

The complementary absence direction behaved as predicted:

- absence-cell C−R3 = **+0.000236**
- 95% interval = **[+0.000077, +0.000418]**

Thus the graph-path source representation improved probability assignment specifically where these ultrarare species were actually present, not across the overwhelmingly absent background.

The source-support prediction was also supported. Among presence cells, the benefit was substantially stronger where a graph-reachable occupied source existed:

- nonempty-minus-empty presence contrast = **−0.6705**
- 95% interval = **[−0.8009, −0.5427]**

Most importantly, this was not reproduced by arbitrary graph structure. The actual island adjacency outperformed the mean of 20 degree- and edge-length-matched rewired graphs on the preregistered presence metric:

- actual C minus mean rewired C = **−0.0585**
- 95% interval = **[−0.0993, −0.0163]**
- actual graph better than **20/20** null graphs

This is the strongest current evidence that the exact arrangement of occupied islands can carry species-specific occurrence information.

It is still not direct evidence of contemporary movement, colonization or demographic rescue.

### Layer R — rare species: 5–12 pilot presences

This independently sealed layer contained 96 species.

The preregistered overall natural-prevalence replication did not pass:

- C−R3 = **−0.000442**
- 95% interval = **[−0.001098, +0.000204]**

The original absence-focused signature reversed:

- absence C−R3 = **+0.000430**
- presence C−R3 = **−0.2774**

But topology specificity was absent:

- actual C minus mean rewired C = **+1.56 × 10⁻⁶**
- 95% interval = **[−2.12 × 10⁻⁴, +2.04 × 10⁻⁴]**
- actual graph better than **11/20** nulls

This layer therefore looks like a transition state: source-related information can improve realized-presence prediction, but the exact island adjacency is not distinguishable from matched surrogate topology.

### Layer M — higher-occupancy exploratory species: ≥13 pilot presences

The original exploratory layer contained 79 species.

At natural prevalence:

- C−R3 = **−0.001814**
- 95% interval = **[−0.002817, −0.000997]**
- favourable in 108/168 blocks, 10/12 bioregions and 64/79 species

But the gain was driven by absences:

- absence C−R3 = **−0.00580**
- presence C−R3 = **+0.11644**

A later frozen-output topology audit showed that this gain was not specific to the observed adjacency:

- actual C minus mean rewired C = **+0.000225**
- 95% interval = **[+0.000124, +0.000330]**
- actual graph better than **0/20** matched null graphs

The original exploratory signal should therefore no longer be described as evidence that the exact observed island topology is informative. It is better interpreted as information in a network-transformed occupied-source context.

### Broad near-ubiquitous layer

A prospective layer defined by only 1–12 pilot absences selected zero species and terminated at the frozen pilot gate. The threshold was not widened.

Therefore the broad end of the proposed occupancy gradient remains prospectively untested.

## Revised island-biogeographic interpretation

The combined evidence does not support one universal connectivity effect.

Instead, the same archipelago can mean different things for species in different occupancy states.

### When very few source populations remain

For species present on only 1–4 pilot islands, the exact placement of those occupied islands matters for predicting realized presences. Degree and edge-length distributions alone did not reproduce the actual-topology signal.

This is compatible with an island-biogeographic state in which the few remaining occupied islands are not interchangeable. Their spatial arrangement relative to unoccupied targets can determine whether a target retains source access beyond what is represented by mainland isolation, generic island connectivity, source count, regional prevalence and Euclidean source proximity.

### At 5–12 occupied pilot islands

The exact adjacency no longer had detectable value beyond matched null topology, although presence probabilities still improved.

This suggests that the information carried by source context can change before a stable topology-specific network signal emerges.

### At higher occupancy

The exploratory natural-prevalence gain was dominated by excluding absences, and actual adjacency was worse than the matched null ensemble. Here, graph transformation appears to summarize broader source context rather than a unique realized topology.

## Relation to classical island biogeography

Classical island biogeography treats colonization pressure as declining with isolation from a source. The rescue-effect extension further recognizes that immigration from conspecific sources can reduce local extinction risk.

The current results do not measure colonization or rescue directly. They add a species-state qualification:

> **The ecological information associated with surrounding occupied islands depends on how many islands the focal species occupies.**

For an ultrarare species, the identity and arrangement of the last few occupied islands can contain information about where the species is still found. For more widely occupied species, source information can be redundant with broader spatial context or can operate through a different predictive signature.

## Conservation implication

The strongest defensible conservation implication is not “always protect network hubs.”

It is:

> **Connectivity assessments should be conditional on the occupancy state of the species being conserved.**

For an ultrarare island species, two archipelagos with the same number of remaining occupied islands need not provide the same source context if those populations occupy different positions in the island network. The prospective ultrarare result therefore motivates testing whether conservation planning should preserve not only the number of remaining populations but also their spatial arrangement.

This is a hypothesis for management, not an intervention result. The present occurrence data do not show that restoring a link will cause recolonization, rescue or demographic persistence.

## Cross-system boundaries

Other Structural systems prevent overgeneralization.

- A-Islands shows that structural information can disappear when a stronger ecological reference is supplied.
- Tanzania likewise shows adverse or uncertain incremental structural information beyond a strong current-state reference.
- The 318-island mammal stress test rejected a universal extreme-isolation amplification hypothesis.
- Boreal beetles provide valid fresh local non-support for a universal source-topology increment.
- GIFT plants did not complete a fresh ecological primary; the endpoint-available subset is descriptive only.

Thus the new ultrarare signal should be treated as a specific occupancy-regime result, not a universal connectivity law.

## Current evidence hierarchy

1. **Ultrarare 1–4-presence mammal layer** — prospective preregistered species-layer evidence; presence opportunity, source-support and topology-specificity predictions supported.
2. **Rare 5–12-presence mammal layer** — prospective preregistered non-replication of the overall gain; presence improvement but no topology specificity.
3. **Original ≥13-presence mammal layer** — large exploratory signal; post-hoc audit shows no actual-topology specificity.
4. **Boreal beetles** — valid fresh local primary non-support.
5. **318-island mammals** — independent nonfresh stress test rejecting universal extreme-isolation amplification.
6. **A-Islands / Tanzania** — foundational evidence that structural information is reference-conditioned.
7. **GIFT plants** — fresh attempt terminal without ecological score; selected exploratory subset only.

## Current central claim

> **The predictive role of occupied source islands changes with species occupancy. In a preregistered ultrarare mammal layer, realized presences were strongly associated with graph-path source information and the observed island adjacency outperformed matched rewired topologies. A separate rare layer did not replicate the overall gain or topology specificity, while a higher-occupancy exploratory layer showed an absence-focused gain that was not specific to the observed adjacency. Connectivity should therefore not be treated as a species-invariant property of an island.**

## Claim boundary

Do not claim:

- realized dispersal along graph paths;
- demographic rescue;
- that ultrarare species universally depend on stepping stones;
- a monotonic effect of rarity;
- a formal unimodal occupancy–connectivity relationship;
- broad-species saturation from the failed broad pilot;
- geographically independent replication.

The next decisive test is an independent response-sealed island system with occupancy strata fixed before held-out response access.
