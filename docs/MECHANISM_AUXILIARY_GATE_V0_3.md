# Mechanism auxiliary qualification gate v0.3

## Purpose

M1/M2 dynamic estimability is executable in v0.2.

v0.3 makes the other two lanes response-blind and executable:

- **M3 historical colonization legacy**
- **M4 environmental proxy**

Neither gate reads the mechanism outcome it will later test.

## M3 — genetics before genetics

M3 qualification opens only sampling/design metadata:

```text
population_id,block,role,sample_n
```

and a predictor-only source comparison table:

```text
focal_population,source_population,comparison_class
```

where `comparison_class` is either:

- `graph_connected`
- `alternative`

The gate never opens:

- genotypes;
- allele frequencies;
- F_ST;
- coancestry;
- assignment probability;
- genetic effect direction.

A focal population is eligible only when:

1. its sample size reaches the frozen minimum;
2. it has enough adequately sampled graph-connected sources;
3. it has enough adequately sampled alternative sources.

The whole M3 lane then additionally requires enough eligible focal populations, eligible source populations and focal spatial blocks.

This prevents a future genetic result from being based only on the few source pairs that happened to look favourable.

## M4 — environment before response

M4 opens only:

```text
unit_id,block,<exact frozen enriched predictors>
```

The predictor columns must exactly match the response-blind list frozen in the mechanism protocol.

The gate checks:

- enough units;
- enough spatial blocks;
- missingness;
- number of distinct predictor values;
- enough complete rows in enough blocks.

It does **not** fit an occupancy model or inspect topology effect direction.

The enriched predictors must also be declared non-topological and cannot overlap the existing strong-reference predictor names.

## Why M4 is a qualification gate rather than another model search

The environmental-proxy explanation is especially vulnerable to researcher degrees of freedom.

Without this gate one could repeatedly add habitat variables until the topology effect disappeared.

v0.3 forces the full enriched predictor list and minimum support to exist before response access.

If the future enriched reference later absorbs topology, that outcome was not engineered by post-outcome variable selection.

## Independent lane decisions

M3 and M4 are qualified independently.

If genetics is well sampled but environmental coverage is inadequate, output is:

`partial_auxiliary_mechanism_estimability_only`.

That does not authorize M4.

The reverse is equally true.

## Evidence firewall

Qualification contributes:

- no effect size;
- no prediction score;
- no genetic outcome;
- no ecological confirmatory response;
- no predictive denominator;
- no mechanism claim.

A clean gate pass authorizes only a **separate frozen confirmatory mechanism protocol**.

## Current state

No empirical system is active.

CI exercises only synthetic response-blind metadata fixtures.
