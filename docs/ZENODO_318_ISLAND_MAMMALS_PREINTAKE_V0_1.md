# Zenodo 318-island mammals — pre-intake v0.1

## Status

**HOLD before v0.11 intake.**

No mammal occurrence value has been opened by Structural.

Source:

- Zenodo record: 10.5281/zenodo.11220273
- associated article: 10.1111/gcb.17375
- 318 islands
- 1,474 mammal species

## Why this is a useful island-biogeography test

This system allows a cleaner, coarser test of the **source-pool handoff** idea than the failed Indo-Pacific atoll pilot.

The central question is:

> As islands become more isolated from continents, does the occupancy state of the same species on other islands in the focal archipelago become increasingly informative?

Unlike A-Islands, this candidate does not initially require a pairwise island graph. Its source coordinate is the **occupied archipelago source pool**.

That makes it an independent test of the ecological idea rather than a replication of the same graph operator.

## Strong reference

The planned reference absorbs:

- zoogeographic context if safely available;
- annual temperature;
- annual precipitation;
- maximum elevation;
- island area;
- distance to continent;
- distance to nearest larger landmass;
- past land-bridge connectivity;
- response-independent number of eligible islands in the archipelago;
- global training-only species occupancy breadth.

The candidate adds:

- the fraction of other training islands in the focal archipelago occupied by the species.

The primary held-out contrast remains candidate minus strong-reference log loss; negative is favourable.

## Isolation-regime prediction

The primary moderator is response-independent distance to continent.

Extreme isolation is frozen prospectively as the upper 25% of the eligible-island distribution.

Prediction:

> training-only within-archipelago source support has a more favourable incremental value on extremely continent-isolated islands than elsewhere.

q70 and q80 are sensitivity checks only and may not rescue a failed q75 primary.

## Historical isolation

The source also supplies a past-connectivity variable indicating whether an island had a Last Glacial Maximum mainland connection.

This supports a secondary prediction:

> present archipelago source-pool support should matter most where contemporary mainland access is weak, while past connectivity may explain more of the structure for poor dispersers.

This is secondary and cannot rescue the primary.

## Dispersal-mode secondary

A bat versus non-volant comparison is attractive because the source literature reports a stronger role of current isolation for bats and past isolation for non-volant mammals.

However, this comparison is not yet authorized.

The bat/non-volant classification must be frozen from response-independent taxonomy or trait metadata before response opening.

## Partition concept

The source-pool candidate needs other islands from the same archipelago to remain available as training sources.

Therefore the intended design is **within-archipelago island splitting**, not leave-one-archipelago-out.

Before response access:

1. open only the safe columns of data_models_islands.csv;
2. retain archipelagos with at least four safe-metadata islands;
3. within each archipelago rank islands using a deterministic SHA-256 salt;
4. allocate at least two islands to the burned pilot and retain at least two for confirmation;
5. freeze the exact island lists.

Within each partition, the held-out design is leave-one-island-out.

The focal island is never allowed to contribute its own response to its source-pool feature.

## Mixed-file firewall

data_models_islands.csv contains both safe predictors and response-derived summaries.

Safe candidate columns:

- ID
- Archipielago
- Type
- protected_percentageI_VI
- dContinent_km
- Anntemp_promedio
- Annprec_promedio
- Area_km2
- Elev_max
- Human_foot
- distance_biggerLandmass

Forbidden before response authorization:

- SppRich
- Thre_sp
- Island_FRic
- Island_Red
- SES_FRic
- SES_FRed
- SR

The column firewall must be frozen before any data row is opened.

## Response workbook gate

Mammal_occurrence_islands.xlsx is still closed.

Before v0.11 intake the project must establish schema-only:

- workbook sheets;
- island identifier field;
- species occurrence layout;
- exact occurrence value domain;
- any native/introduced/status coding;
- any bibliographic columns;
- join semantics to data_models_islands.ID.

The endpoint is deliberately **not** finalized until this domain is known.

This directly incorporates the Indo-Pacific atoll lesson: an apparently simple response must not be opened until the complete categorical value domain has been frozen.

## Stop conditions

Stop before response if:

- Zenodo file identities are not reproducible;
- mixed-file safe columns cannot be isolated;
- occurrence value domain cannot be completely frozen;
- island IDs cannot be joined response-blind;
- too few archipelagos support the within-archipelago pilot/confirmatory split;
- one fixed species universe cannot be used consistently across held-out islands.

## Evidence state

- response opened: no;
- pilot authorized: no;
- confirmatory response authorized: no;
- effect estimated: no;
- counts as empirical confirmation: no.
