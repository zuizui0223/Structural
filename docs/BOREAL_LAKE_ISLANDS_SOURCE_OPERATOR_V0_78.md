# Boreal source-pool operator v0.78

## Ecological contrast

v0.78 turns the v0.55 dual-isolation hypothesis into a concrete reference ladder
before any beetle response is opened.

The key design principle is that **species-conditioned connectivity does not get
credit for information already available from direct source context or generic
island geometry**.

### R2 — generic archipelago geometry

R2 adds response-independent:

- nearest other-island distance;
- diffuse surrounding-island pressure;
- area-weighted surrounding-landmass pressure;
- generic connected-component exposure;
- generic mainland stepping-stone frequency.

### R3 — direct and diffuse occupied-source context

R3 then adds training-only:

- global occupied fraction;
- nearest occupied training source;
- diffuse occupied-source pressure;
- area-weighted occupied-source pressure.

### C — species-conditioned network continuity

C adds only:

`occupied_component_frequency`

This is the fraction of frozen-radius graphs in which the focal island's
connected component contains at least one effective training presence.

Therefore a future C improvement cannot be attributed merely to a closer source,
more occupied sources, larger source islands, denser generic island surroundings
or more generic graph exposure: all of those are already represented in R3 or
earlier tiers.

## Frozen graph scales

The operator uses the q25/q50/q75/q90 rounded candidate radii produced by the
response-independent v0.75 geometry result. Exact duplicate rounded radii are
collapsed before equal averaging so the same graph is not double-weighted.

No species-specific radius can be selected.

## Training-only construction

For a held-out island, only training occurrence labels define the occupied
source set.

For a training row, the focal island is removed from both the training
denominator and the occupied-source set before its source features are computed.
This prevents a presence row from acting as its own trivial anchor.

If no effective training presence remains, the row is non-estimable. There is no
imputation or post-pilot gate lowering.

All 42 island nodes may still act as **response-blind physical stepping stones**
because their geometry is predictor information, not held-out occurrence.

## Diagnostics

Two decomposition terms are recorded but are not primary model predictors:

- direct occupied-neighbor frequency;
- multi-hop-only frequency, where an occupied source is component-reachable but
  not directly within the radius.

They may explain a future result descriptively, but neither may replace
`occupied_component_frequency` after outcomes are seen.

## Claim boundary

Connected frequency is structural occurrence support, not a movement,
colonization or rescue probability.
