# A-Islands island-biogeography synthesis v0.1 — source-pool handoff

## Status

This is an ecological synthesis of **already-frozen** A-Islands results. It adds no new subgroup search, threshold search, taxon selection, graph-scale tuning, or empirical denominator.

The frozen Structural primary result remains unchanged. The post-outcome A-Islands discovery sequence remains exploratory.

## Ecological question

Why can two islands with similarly weak mainland access differ in whether a focal species is supported?

The A-Islands results suggest that classical mainland isolation and focal-species source isolation are not the same state.

A useful distinction is:

- **mainland-access state** — island area, mainland distance, nearest source and species-independent archipelago context;
- **insular source-network state** — whether the focal island remains connected to the focal species' occupied outer-training source islands, including multi-hop paths.

The central ecological hypothesis is a **source-pool handoff**:

> As mainland access weakens, the ecologically relevant source context can shift from mainland-anchored isolation toward continuity with the occupied insular source network.

This is an occurrence-support hypothesis, not evidence of realized dispersal or contemporary colonization.

## 1. Ordinary islands are largely explained by classical state variables

Across species range-breadth classes, the R1 tier that adds island area, mainland distance and nearest focal-species source improves held-out prediction:

- narrow species: R1−R0 = **−0.0128**;
- mid-breadth species: **−0.0161**;
- wide species: **−0.0134**.

By contrast, adding more diffuse source pressure, generic archipelago context and finally species-conditioned topology is on average redundant or adverse.

Ecologically, this says that most islands do not require a high-order network explanation once their size, mainland isolation and direct source context are represented.

## 2. Source saturation explains why topology is especially redundant for widespread species

Species breadth is positively associated with C−R3 adversity:

- Spearman rho = **+0.201**;
- Pearson r = **+0.422**.

For species occupying at least 61 islands:

- mean C−R3 = **+0.0190**;
- only **26.1%** of species are favourable.

For species occupying 10–12 islands:

- mean C−R3 = **+0.00128**;
- **42.5%** are favourable.

A parsimonious ecological interpretation is **source saturation**: widespread species already have many occupied source anchors, so coarse species-conditioned connectivity adds little information under ordinary island conditions.

## 3. Mainland remoteness changes that relationship

The breadth × mainland-distance interaction is negative:

**β = −0.00267, p = 7.3×10⁻⁴.**

The same interaction remains after adding breadth × island area:

- breadth × mainland distance: **β = −0.00273, p = 6.7×10⁻⁴**;
- breadth × island area: β = +0.00098, p = 0.125.

Thus the ecological moderation tracks **mainland remoteness rather than island size**.

The pattern strengthens into the remote tail. At the frozen upper-25% isolation definition, the breadth × extreme-isolation interaction is strongly negative; deeper-tail diagnostics strengthen rather than erase it.

This is not evidence for a universal kilometre threshold. It supports a qualitative regime change toward the most mainland-remote islands.

## 4. Remote islands divide into remote-but-linked and remote-and-unlinked states

The key A-Islands result is not simply that remote islands behave differently.

Among the reconstructed five-fold-evaluable data, every row where focal-species connectivity exceeds generic mainland stepping occurs in the remote tail.

Those rows share one striking state:

- focal-species connected frequency = **1.0** across the four frozen radii;
- generic mainland stepping frequency = **0.75**;
- generic mainland access fails at the smallest 25-km scale while the focal species remains linked to an occupied insular source.

This separates two biologically different forms of remoteness:

1. **remote-and-unlinked** — weak mainland access and no compensating occupied source path;
2. **remote-but-linked** — weak mainland access but continuity with occupied insular sources.

That distinction is invisible to mainland distance alone.

## 5. The signal is specifically associated with source-network continuity

In the frozen upper-25% remote panel, controlling species identity and island identity, R3 underprediction is larger when:

- focal-species connectivity exceeds generic mainland stepping: **β = +0.0726**, p ≈ 2.0×10⁻⁶;
- continuous focal-source minus generic connectivity is larger: **β = +0.0889**, p ≈ 4.9×10⁻⁸;
- a multi-hop 25-km source path exists: **β = +0.0644**, p ≈ 1.2×10⁻⁵.

A direct occupied source within 25 km is weaker and not conventionally detected:

- β ≈ +0.0417, p ≈ 0.073.

After explicitly adjusting for nearest occupied source distance, the source-network associations remain:

- excess focal connectivity: **β = +0.0739**, p ≈ 0.0037;
- continuous focal-source minus generic connectivity: **β = +0.2125**, p ≈ 1.4×10⁻¹⁰;
- multi-hop source path: **β = +0.0537**, p ≈ 0.0062.

So the ecological information is not reducible to "there is a source nearby."

It is associated with **path continuity through the archipelago**.

## 6. Multi-hop paths are the clearest island-biogeographic result

For true-presence rows with nearest occupied source between 25 and 100 km:

- multi-hop 25-km source path:
  - n = 3,635;
  - mean C−R3 = **−0.1042**;
  - favourable fraction = **77.8%**;
- no multi-hop path:
  - n = 2,538;
  - mean C−R3 = **+0.0810**;
  - favourable fraction = **35.5%**.

Across 211 paired species, the mean multi-hop minus non-multi-hop difference is **−0.2064** (Wilcoxon p ≈ 1.6×10⁻²¹).

Even among islands connected at the smallest 25-km graph scale, multi-hop source connections are at least as informative as direct-source connections.

This supports a specific island-biogeographic idea:

> Intermediate islands can preserve focal-species source-network continuity even when no occupied source is directly close to the focal island.

The data do **not** show organisms physically moving through those intermediate islands. The result is a source-network state consistent with a stepping-stone mechanism.

## 7. Presence support changes in the remote regime

For the broadest-quarter species, true-presence rows show a large contrast.

### Near islands
- mean C−R3 = **+0.1921**;
- favourable fraction = **33.7%**;
- topology lowers predicted occurrence probability on average.

### Most remote islands
- mean C−R3 = **+0.0161**;
- median = **−0.0123**;
- favourable fraction = **59.0%**;
- topology raises predicted occurrence probability slightly on average.

Thus the source-network coordinate changes ecological role.

Under ordinary, source-rich conditions it is largely redundant. Under extreme mainland isolation it distinguishes remote islands whose focal-species source network remains intact.

## 8. Proposed island-biogeographic model

The results support a two-context assembly model.

### Context A — mainland/source-rich regime

Occurrence support is largely represented by:

climate + island area + mainland isolation + direct/diffuse focal-source context.

Species-conditioned topology is mostly redundant, especially for widespread species.

### Context B — mainland-decoupled regime

Generic mainland access weakens.

The important distinction becomes whether the focal species retains an occupied **insular source path**.

The effective source context therefore shifts from:

**mainland access → archipelago-internal occupied source continuity.**

This is the proposed **source-pool handoff hypothesis**.

## 9. Relation to island-biogeography theory

Classical island biogeography emphasizes island area and isolation. Later work has emphasized that isolation is multidimensional, including mainland distance, stepping-stone availability and network position.

A-Islands adds a species-conditioned layer:

> The same physical archipelago does not provide the same connectivity state to every species, because the ecologically relevant source network depends on which islands that species already occupies.

The contribution is therefore not "network metrics beat distance."

It is:

> **At extreme mainland isolation, the identity and continuity of the occupied insular source pool can matter more than generic geographic connectivity.**

## 10. What would make this a strong island-ecology paper

The current A-Islands evidence is discovery evidence. A strong ecological paper requires an independent test of three predeclared predictions:

1. **Regime switch** — source-conditioned topology is more informative in a response-independent extreme-isolation tail than elsewhere.
2. **Source-pool decoupling** — within that tail, remote-but-linked units outperform remote-and-unlinked units relative to the same strong reference.
3. **Multi-hop continuity** — source-network information remains when nearest-source distance is controlled and when the nearest occupied source lies beyond the smallest frozen graph scale.

A fourth, stronger biological test would add temporal or genetic data to distinguish contemporary colonization, rescue/persistence and historical occupancy legacy.

## Claim boundary

Do not claim from A-Islands alone that:

- multi-hop graph paths are realized dispersal routes;
- intermediate islands are proven stepping stones;
- the pattern estimates colonization probability;
- remote populations are maintained by rescue effects;
- mainland isolation has a universal numerical threshold;
- source-pool handoff is confirmed outside A-Islands.

The supported ecological statement is narrower:

> **Mainland isolation and focal-species source isolation can decouple, and this decoupling marks systematic occurrence support on very remote islands that is not captured by island area, mainland distance, nearest occupied source, diffuse source pressure or generic archipelago stepping alone.**
