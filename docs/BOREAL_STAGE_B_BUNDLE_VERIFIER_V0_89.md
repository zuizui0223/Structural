# Boreal exact-replay Stage-B bundle gate v0.89

v0.89 adds a second layer of verification to the response-independent Stage-B
workflow.

A Stage-B job is no longer accepted merely because each component command
returns exit code zero. Before upload, the bundle verifier independently
reconstructs the downstream design from the safe artifact surface.

## Exact replays

The verifier recomputes:

- v0.75 spatial partition from `safe_geometry.csv` + v0.74 receipt;
- v0.76 habitat reference from `safe_habitat.csv` + v0.74 receipt;
- v0.83 source operator from geometry + v0.74/v0.75;
- v0.79 v0.12 intake and the generic v0.12 validator;
- v0.80 v0.31 protocol, v0.42 quality contract and pre-pilot receipt.

Each replay must equal the Stage-B artifact exactly.

The v0.74 safe outputs themselves are SHA-bound to their projection receipt and
must retain the exact 42-island support. Transport identity is also rechecked
against the frozen v0.72 Dryad file IDs, byte sizes and SHA-256 values.

## Bundle receipt

Only after all checks pass does the workflow emit

`structural.boreal_stage_b_bundle_freeze.v0_89`

with status

`VERIFIED_RESPONSE_INDEPENDENT_PREPILOT_BUNDLE`.

The receipt includes a SHA-256 map of every Stage-B input file and a canonical
bundle fingerprint tying together Stage-A provenance, the v0.12 intake,
v0.31/v0.42 fingerprints and the v0.83 source operator.

## Evidence boundary

The verifier does not open a biological response. A verified bundle contributes
zero empirical evidence and still cannot authorize the burned pilot.

Its only consequence is to make one exact response-independent pre-pilot bundle
eligible for repository commit and subsequent separate v0.81 review.
