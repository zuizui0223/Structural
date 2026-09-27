# Zenodo 318-island mammals — design-frozen stress test v0.47

## Evidence class

This system is **not pristine fresh confirmation**.

Before any 1,474-species occurrence value was opened, the following were already frozen response-blind:

- 318-island safe metadata join;
- eight eligible archipelagos and 309 eligible islands;
- 65 burned-pilot versus 244 heldout islands;
- q75 continent isolation = **1124.41 km**;
- the source-pool-handoff reference ladder and direction.

After that freeze, a public preview exposed island-level richness / threatened / functional-diversity summary columns from the safe-design source table. The raw species occurrence matrix remained unopened.

Therefore this lane is retained only as a:

**design-frozen, response-summary-exposed independent stress test.**

It never enters the fresh confirmatory denominator.

## Island-biogeographic question

The test asks whether an island's mammal assemblage contains information about the **occupied source pool elsewhere in the same archipelago** after strong island state is represented.

For a focal species and island, the candidate coordinate is the fraction of frozen pilot islands in the same archipelago occupied by that species.

The key ecological prediction remains the A-Islands source-pool-handoff prediction:

> source-pool information should matter more on islands that are extremely isolated from continents.

The primary extreme-isolation boundary was frozen before species occurrence access:

**dContinent >= 1124.41 km**.

## Frozen island design

Eight archipelagos contribute 309 response-independent eligible islands:

- Alexander: 46;
- Caribe: 4;
- Golfo California: 15;
- Indonesia: 59;
- Japan: 7;
- Macaronesia: 9;
- Mediterranean: 99;
- New Guinea: 70.

The deterministic split contains:

- 65 pilot islands;
- 244 heldout islands.

## Frozen response schema

The occurrence workbook contains:

- metadata columns: `ID / Island / Island_group`;
- 1,474 unique mammal species columns;
- 318 data rows;
- published presence/absence semantics;
- source analysis code that treats cells equal to 1 as presence.

Species-header SHA-256:

`1a23562c1397beed83c5c8a7fe2aaccbb94ff39206bec3864c3af82317184a6d`

No row-5+ occurrence value was opened during schema/design freezing.

## Burned-pilot species rule

The stress-test pilot inherits the generic replication-support rule already used in the prior atoll programme:

> keep a mammal species only if it is present on at least **two distinct frozen pilot islands**.

The threshold is not chosen from the exposed island richness summaries.

The same fixed species universe is used for every held-out pilot island so v0.32 held-out complement arithmetic remains valid.

## Strong reference and candidate

### R0
- archipelago fixed effects;
- annual temperature;
- annual precipitation;
- maximum elevation.

### R1
R0 plus:
- log island area;
- log continent distance;
- log distance to the nearest larger landmass;
- past land-bridge connectivity (`Type`).

### R3
R1 plus:
- pilot-derived global species occupancy breadth.

### C
R3 plus:
- pilot-derived occupied source fraction within the focal archipelago;
- its interaction with the frozen q75 extreme-isolation indicator.

All occupancy/source quantities are computed from pilot response only.

## Heldout scoring

Models are trained on the 65 pilot islands only.

The 244 heldout islands are not used to fit coefficients or source-pool states.

For pilot training rows, source fractions exclude the focal island. For heldout rows, all pilot islands in the same archipelago form the permitted source pool.

Primary estimand:

`mean(C−R3 log loss | extreme) − mean(C−R3 log loss | non-extreme)`

Prediction: **negative**.

Uncertainty is a 10,000-replicate archipelago-cluster bootstrap, seed 20260927.

Primary support requires both:

1. point estimate < 0; and
2. bootstrap 95% upper bound < 0.

## Claim boundary

Even a positive stress-test result would be **supportive independent evidence**, not fresh confirmatory evidence, because island-level response-derived summaries were exposed after design freeze but before the species-support/pilot protocol freeze.

The pristine 5,592-island mammal system remains a separate response-sealed HOLD and is not replaced by this stress test.
