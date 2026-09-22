# Confirmatory admission queue v0.36

## Purpose

v0.36 turns the v0.31-v0.33 sequence into one reproducible admission boundary.

A system is **not** placed in the confirmatory queue because it looks promising, because a pilot effect is favorable, or because TTF would benefit from another species. It enters only when CI can reproduce the complete burned-pilot qualification chain from committed artifacts.

## Required chain

```
v0.31 frozen disjoint protocol
    -> v0.32 burned-pilot estimability result
    -> v0.33 freeze gate
    -> v0.36 reproducible admission receipt
    -> confirmatory-protocol queue
```

v0.36 recomputes rather than trusts the labels stored in the pilot result.

It requires:

- the exact v0.31 protocol fingerprint;
- the exact frozen pilot partition;
- a v0.32 result schema;
- `pilot_consumed=true`;
- `effect_size=null`;
- `prediction_score=null`;
- predictive denominator contribution exactly zero;
- no confirmatory-partition opening;
- zero confirmatory response rows seen;
- the frozen minimum estimable-block threshold;
- block-audit counts internally consistent with the reported estimable-block count;
- a clean v0.33 decision.

## What admission authorizes

Exactly one action:

`freeze_confirmatory_protocol_only`

It does **not** authorize confirmatory response access.

The later confirmatory protocol still has to freeze the state/reference representation, typed connectivity, heldout design, scoring implementation and response firewall before any confirmatory outcome can be opened.

## Queue integrity

The machine-readable queue is:

`development/confirmatory_admission_queue_v0_36.json`

Every non-empty queue entry must point to:

1. its frozen v0.31 protocol;
2. its v0.32 pilot result;
3. its deterministic v0.36 admission receipt.

CI reruns the admission logic and requires the stored receipt and protocol fingerprint to reproduce exactly. A manually added queue row without a reproducible PASS fails CI.

The queue is currently empty.

## TTF relationship

TTF remains downstream and independent.

A v0.36 admission proves only that a within-system confirmatory protocol may now be constructed. It does not establish within-system adequacy, operator portability, cross-species transferability, or TTF eligibility.

TTF must never be used to motivate lowering this gate or selecting systems based on favorable Structural outcomes.
