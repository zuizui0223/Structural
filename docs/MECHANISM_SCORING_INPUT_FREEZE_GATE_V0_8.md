# Mechanism scoring-input freeze gate v0.8

## Why this gate is inserted before v0.6

The mechanism chain already froze the protocol before response access.

But a protocol string is not enough.

For M1, M2 and M4, model predictions themselves must also be fixed before the confirmatory response is opened. Otherwise a model could be refit after response access while technically leaving the written scoring rule unchanged.

v0.8 closes that gap.

Its logical position is:

`v0.5 protocol freeze → v0.8 scoring-input freeze → v0.6 response authorization → v0.7 access record → scoring`

The version number reflects when the safeguard was added, not its logical position.

## M1 / M2

Exact response-blind prediction surface:

`partition_unit,block,unit_id,p_reference,p_candidate`

Probabilities must be strictly between zero and one.

The exact partition, unit set and file SHA-256 are frozen before response authorization.

## M3

There is no predictive probability surface.

Instead v0.8 freezes the response-blind scoring design:

`focal_population,source_population,comparison_class,weight`

The pair set must exactly equal the source-pair design qualified before any genetic outcome was opened.

Weights must be finite and positive.

This prevents pair selection or weighting after genetic outcomes become visible.

## M4

Exact response-blind surface:

`partition_unit,block,unit_id,p_original_reference,p_original_topology,p_enriched_reference,p_enriched_topology`

This freezes both questions needed by the environmental-proxy mechanism:

1. does enriched environment improve the reference?
2. does the topology increment collapse after enrichment?

No model can be added or refit after the response is seen.

## Receipt

The v0.8 receipt binds:

- v0.5 receipt SHA-256;
- exact protocol fingerprint;
- scoring input SHA-256;
- exact unit/pair key-set SHA-256;
- row/support counts.

It contains no outcome and no effect.

## Retrofit into the chain

Because no empirical mechanism system has yet entered the pipeline, v0.6 is updated to require a Git-tracked v0.8 receipt and exact scoring-input replay before it can authorize response access.

Synthetic historical v0.6/v0.7 fixtures are regenerated under this stronger chain.

## Current state

No empirical scoring input or mechanism response is open.
