# BALA source-loss leverage confirmatory protocol v1.139

## Question

The current mammal work shows that, for ultrarare species, occupied source islands are not interchangeable. The BALA system now provides the first independent three-wave opportunity to ask the conservation question directly:

> **If exactly one occupied source population disappears, does it matter which source was lost?**

BALA1 defines the pre-loss occupied-source state, BALA1→BALA2 defines the source-loss event, and BALA2→BALA3 provides the later persistence/contraction endpoint.

## Why the primary exposure is target-specific

A source population can be important for one target island and nearly irrelevant for another. The primary exposure is therefore not simply source count or a global centrality score.

For each target island i that remains occupied at BALA2, the baseline BALA1 source set excludes i itself. The leverage exposure E_i is the fraction of its BALA1 graph-kernel source access contributed by the source that disappeared by BALA2.

This directly asks how much source access the target lost.

## Strong reference

R2 deliberately includes:

- complete island fixed effects, absorbing static habitat, area, external isolation and generic island-network differences;
- BALA1 other-source count;
- BALA2 surviving-other-source count;
- nearest surviving-source Euclidean distance;
- diffuse surviving-source pressure;
- whether the target was already occupied at BALA1;
- response-independent BALA3 pitfall effort.

The primary event population is restricted to exactly one source loss, so nominal loss count is held constant by design.

C adds only E_i.

## Validation

The validation unit is the MF taxon, not the target row.

For every eligible confirmatory taxon, a model is trained on all other eligible confirmatory taxa and scored on that heldout taxon's BALA2-surviving target islands. Continuous variables are standardized using only the training complement.

The primary is the equal-weight mean across heldout taxa of C−R2 binary log loss.

A taxon contributes only if its training complement contains at least five contractions and five persistences. At least ten estimable taxon clusters are required for the primary to exist.

## Response firewall

The burned pilot has already passed without computing leverage or any candidate effect.

The confirmatory sequence remains:

1. split opaque rows into BALA1/2 versus BALA3 by safe Event IDs only;
2. open BALA1/2 only;
3. freeze all exposure/reference/candidate features and taxon folds;
4. only then open BALA3 once.

No BALA3 outcome can influence the leverage formula, graph, model, row population or validation design.

## Conservation interpretation

If C improves heldout prediction, the supported claim is narrow but useful:

> loss of source-access leverage contains future occupancy information beyond losing one population per se and beyond ordinary source distance.

It would not prove rescue, movement, recolonization or causal extinction prevention.
