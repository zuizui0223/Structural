# Confirmatory admission infrastructure freeze v0.40

## Decision

The Structural burned-pilot admission machinery is frozen at v0.40.

No new gate feature is the active objective.

The frozen executable chain is:

```
v0.31
  freeze disjoint pilot/confirmatory partitions + endpoint + heldout gates
    ->
v0.32 + v0.39
  open only the exact three-column burned pilot and produce feasibility-only output
    ->
v0.38
  verify raw pilot SHA-256 and exactly replay the v0.32 result
    ->
v0.37
  independently recompute block estimability and heldout arithmetic
    ->
v0.33
  verify fingerprint, zero predictive contribution and no confirmatory exposure
    ->
v0.38 queue
  freeze_confirmatory_protocol_only
```

## Current state

The live confirmatory queue is empty.

That is an intended scientific state, not unfinished infrastructure.

A future system does not enter the queue because it is biologically attractive, because a connectivity result looks favorable, or because TTF needs another species. It enters only when a prospectively frozen v0.31 protocol and its immutable burned-pilot input reproduce a clean qualification chain.

## What may change

Implementation defects may be repaired when all of the following are true:

1. the defect is demonstrated without inspecting a new confirmatory response;
2. a failing synthetic/CI test reproduces the defect;
3. the repair does not lower or reinterpret the scientific gate;
4. any already-burned failed endpoint/version remains failed.

This is maintenance, not retuning.

## What does not happen next

The mainline does not:

- search rapidly for a favorable replacement dataset;
- lower class/test-row gates after failure;
- swap endpoint or heldout design after failure;
- use pilot outcomes as an effect estimate;
- open confirmatory outcomes immediately after admission;
- use TTF performance to select or rescue Structural systems.

## Next valid biological event

When a genuinely suitable system appears, the sequence resumes at a new v0.31 protocol.

If its burned pilot fails, that endpoint/version stops.

If it passes v0.31-v0.39 and enters the queue, the next object is a separate confirmatory protocol freezing the state/reference, typed connectivity, heldout design, scoring implementation and response firewall.

Only that later object can eventually authorize confirmatory response access.

## TTF

TTF remains downstream and logically independent.

Structural qualification asks whether a within-system confirmatory test is admissible. TTF asks whether a representation transfers to unseen species. Neither test substitutes for the other.
