# Static source information versus temporal conservation consequence v1.161

## Central ecological distinction

Structural now separates two questions that are often conflated in island connectivity studies:

1. **Occurrence information** — does the arrangement of occupied source islands contain information about where a species is currently found?
2. **Conservation consequence** — does losing a structurally important source population predict greater subsequent contraction elsewhere?

The repository contains positive evidence for the first question in one prospectively sealed occupancy regime, but the first independent three-wave test did not support the second.

This distinction is now the central conservation interpretation.

## 1. Static occurrence information is occupancy-regime dependent

The global mammal system fixes one geography but separates species by pilot occupancy.

### Ultrarare: 1–4 pilot presences

Prospective heldout evidence:

- 529 species;
- 2,182,654 heldout cells;
- presence-cell C−R3 = **−0.5963**;
- 95% CI **[−0.7439, −0.4645]**;
- source-support contrast = **−0.6705**;
- actual topology minus matched rewired topology = **−0.0585**;
- actual adjacency outperformed **20/20** null graphs.

This is the strongest current evidence that, for very sparsely occupied species, **which islands remain occupied and where they sit in the archipelago can carry occurrence information beyond source count, ordinary source distance and generic network geometry**.

### Rare: 5–12 pilot presences

Prospective heldout evidence:

- 96 species;
- overall C−R3 = **−0.000442**;
- 95% CI **[−0.001098, +0.000204]**;
- actual topology better than **11/20** matched nulls.

The overall gain did not replicate and topology specificity was absent.

### Higher occupancy: ≥13 pilot presences

Exploratory evidence:

- 79 species;
- overall C−R3 = **−0.001814**;
- natural-prevalence gain driven mainly by absence prediction;
- post-hoc actual topology was worse than the matched null ensemble (**0/20** nulls beaten).

Thus connectivity is not one invariant island property and not one invariant species effect.

## 2. Static source leverage is unequal

The response-free ultrarare leverage diagnostic showed that occupied populations are not interchangeable even when source number is the same.

Among 212 mammal species with 2–4 occupied pilot sources:

- median dominant-source share = **0.661**;
- median effective/nominal source ratio = **0.744**;
- observed effective source number exceeded matched-null expectation by **0.282** on average;
- 95% bootstrap interval = **[0.205, 0.362]**.

This establishes **structural irreplaceability**, not demographic importance.

## 3. The independent temporal test did not validate management leverage

BALA provided the required temporal ordering:

**BALA1 source state → BALA1-to-BALA2 source loss → BALA2-to-BALA3 later contraction.**

The one-shot confirmatory population contained:

- 20 taxa;
- 64 target rows;
- 20 later contractions;
- 44 persistences.

Candidate C added only target-specific pre-loss lost-source access beyond a strong R2 containing source counts, remaining-source geometry, island identity and survey effort.

Primary result:

- C−R2 = **+0.000674**;
- 95% CI **[−0.02130, +0.02558]**;
- primary supported = **false**.

Therefore:

> **A population can be structurally distinctive in a static source network without its loss carrying generalizable information about future contraction elsewhere.**

This is not evidence that connectivity never matters dynamically. It is evidence that **static source leverage cannot be promoted automatically into a conservation-priority metric**.

## 4. Why this matters for island conservation

Network-based conservation often ranks patches, islands or populations by centrality, stepping-stone value or contribution to connectivity. Such rankings can be useful, but they answer a structural question unless validated against demographic or occupancy dynamics.

The Structural evidence now provides a direct boundary:

> **Where a species occurs, which source islands are structurally distinctive, and which source losses matter for future persistence are three different quantities.**

For island conservation this means:

- occupancy state should be considered before interpreting connectivity;
- source count should not be treated as equivalent to source leverage;
- source leverage should not be treated as equivalent to future demographic consequence;
- management ranking requires temporal or demographic validation.

This distinction is consistent with earlier warnings that graph connectivity alone cannot establish regional persistence and with empirical work showing that connectivity can affect colonization and extinction differently.

## 5. Current evidence hierarchy

1. **Ultrarare global mammals** — prospective heldout evidence that actual occupied-source adjacency contains realized-presence information in one geographic system.
2. **BALA three-wave arthropods** — independent prospective temporal primary showing that lost-source leverage did not improve prediction of later contraction.
3. **Rare 5–12 mammals** — prospective non-replication of overall gain and topology specificity.
4. **Higher-occupancy 79 mammals** — exploratory source-context signal without actual-topology specificity.
5. **Boreal beetles** — fresh local non-support for a universal graph-path increment.
6. **318-island mammals** — nonfresh stress evidence rejecting universal extreme-isolation amplification.
7. **A-Islands / Tanzania** — foundational evidence that structural information is reference-conditioned.
8. **GIFT plants** — fresh attempt terminal without an ecological primary; selected exploratory context only.

## 6. Revised central claim

> **Species occupancy changes the predictive role of source islands, but static source-network importance is not equivalent to temporal conservation consequence. For ultrarare mammals, the actual arrangement of the few occupied source islands contained prospective heldout presence information. Yet an independent three-wave arthropod test did not show that losing a higher-leverage source better predicted later contraction after strong controls. Connectivity metrics therefore require endpoint-specific validation before they are used to rank island populations for conservation.**

## Claim boundary

Do not claim:

- realized dispersal along graph paths;
- demographic rescue;
- that the BALA non-support proves connectivity is dynamically irrelevant;
- that source leverage is a validated or invalidated universal management metric;
- causal extinction prevention from protecting high-leverage islands;
- a monotonic rarity–connectivity law;
- geographically independent replication of the mammal occupancy-regime result.

## Current scientific priority

Do not pursue eBird in this project.

No same-dataset mammal threshold mining or BALA rescue analysis is authorized.

The next independent temporal system, if pursued later, must be a **non-eBird** candidate frozen before response access and selected without knowledge of a favourable source-leverage outcome.
