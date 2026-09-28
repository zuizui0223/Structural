# Boreal v0.31 + v0.42 pre-pilot freeze v0.80

v0.80 closes the response-independent chain after a clean v0.12 intake.

## Partition semantics

The generic v0.32 runner has two distinct identifiers:

- `partition_unit` controls whether a row belongs to the frozen pilot or
  confirmatory partition;
- `block` controls leave-one-block-out estimability.

For the boreal system these are deliberately different:

- **partition_unit = island code**;
- **block = v0.75 spatial-component ID**.

Thus a confirmatory island row is rejected immediately even when it lies near a
pilot island, while the estimability audit still holds out entire response-
independent spatial components.

## Fixed species universe

The burned pilot may define exactly one common beetle species universe:

> species with target 1 on at least two distinct frozen pilot islands.

That universe is computed once from pilot response only and then applied
unchanged to every pilot heldout block and every later confirmatory island.
Heldout-specific species filtering is forbidden.

## v0.31

The frozen endpoint is static binary beetle detection in the standardized
30 × 30 m island plot. It does not claim complete whole-island occupancy,
colonization, rescue or persistence.

Default estimability gates remain:

- minimum heldout test rows = 3;
- minimum training positives = 5;
- minimum training negatives = 5;
- minimum estimable pilot spatial blocks = 3.

## v0.42

The quality contract is fingerprint-bound to the exact v0.31 protocol and
requires at least three response-qualified pilot spatial blocks.

Schema drift, missing/duplicate pilot islands, non-binary targets, inability to
construct the common species universe, or insufficient applicable targets are
not repairable after pilot opening.

## Evidence ceiling

The generic v0.31/v0.42 components can be internally qualified while the
**overall boreal bundle still has pilot_response_authorized=false**.

A separate response-router/access authorization must be frozen before the
primary beetle occurrence file is opened.
