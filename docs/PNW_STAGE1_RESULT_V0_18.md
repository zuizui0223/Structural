# PNW Stage 1 result v0.18

## Result

Stage 1 has now opened **2012 Rana cascadae lagged state only** and built the complete frozen R0/R1/R2/C predictor table.

All 2013 target values remain sealed.

## Normalization adjudication

The first authorized 2012 opening exposed two raw-table representation details that v0.17 had not enumerated explicitly:

1. `survtype` contains `full`, `partial`, `dry`, and missing values;
2. the master table does not contain an explicit RACA row for every surveyed site.

The normalization rule is now frozen as:

- valid survey visits = `full` or `partial`;
- `dry` is excluded as a valid amphibian survey occasion;
- for a valid survey visit, missing RACA site×species rows are zero-filled.

This follows the source metadata definition of survey type and the source-processing convention that expands site×species×life-stage combinations before zero-filling observations. It is not selected from the direction of the connectivity result.

Because this clarification was written after authorized 2012 fields had begun to open, it is recorded explicitly rather than being represented as preregistered. PNW was already permanently design-exposed, so its evidence ceiling does not increase.

## 2012 site-use state

Across all 219 physically valid 2012 source sites:

- positive: **134**
- negative: **19**
- non-estimable: **66**

RACA was explicit in 135 sites. The normalization step supplies survey-zero RACA rows for 84 sites where the RACA row was absent.

The frozen state-table fingerprint is:

`bbf407503d1db9f911989d27717bb44e80d4028b65647c7b588d23f5bf87b440`

## 2012→2013 evaluation universe

Among the 150 sites represented in both years:

- 2012 positive: **113**
- 2012 negative: **12**
- 2012 non-estimable: **25**

No 2013 response was used to classify these sites.

## Occupied-source connectivity

The source pool remains all 219 valid 2012 ponds.

The occupied-source set contains **134** RACA-positive 2012 sites.

The frozen movement worldset remains:

- 250 m
- 500 m
- 1000 m
- 1500 m
- 5000 m

No radius is selected.

## Feature table

The 150-row feature table contains:

- R0 lagged state;
- R1 local pond state;
- R2 nearest-pond and generic-pond connectivity;
- C occupied-source reachability and pressure.

Fingerprint:

`f2e85764d736ee069c5805e6a808b7e434bbb2930cfa0808e7ff723927af4ce6`

The derived table itself is retained with the working evidence package rather than committed because it is derived from the uploaded source. Its canonical serialization is deterministic in the Stage 1 builder.

## Stage 1 access receipt

- 2012 lagged state opened: yes
- 2013 future target opened: **no**
- 2013 target summarized: **no**
- model fits: **0**
- candidate ranking: **0**

## Next gate

Stage 2 may be authorized only after this Stage 1 receipt and feature fingerprint are merged and CI-green.

Once Stage 2 opens, the 2013 target may be constructed exactly once under the frozen rule. No feature, source anchor, radius, reference variable, held-out region, model family, or metric may change.
