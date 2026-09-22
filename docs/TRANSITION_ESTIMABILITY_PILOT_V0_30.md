# Transition estimability pilot v0.30

## Why this gate exists

The first two real dynamic connectivity attempts reached fully frozen feature surfaces but never reached a predictive comparison.

- PNW future state collapsed toward presence.
- RMNP future state collapsed toward absence.

The failure occurred **before model fitting** in both systems.

Therefore the next problem is not a new connectivity metric. It is whether a proposed future endpoint contains enough transition variation to support the declared heldout design.

## Burned-pilot design

A future protocol must separate three things before any focal response is opened:

1. **pilot period/sample** — permanently consumed for feasibility only;
2. **confirmatory lagged/current state**;
3. **confirmatory future target**.

The pilot response may be opened first, but the confirmatory response remains sealed.

The pilot is run through the **same test-row and training-class gates** planned for confirmation.

Example:

- minimum heldout rows = 3;
- training positives >=5;
- training negatives >=5;
- at least 3 heldout blocks must be estimable.

## Pilot outcomes

### qualified_for_new_confirmatory_protocol

Enough pilot blocks pass the exact planned class/test-row gates.

This does **not** mean connectivity works.

It only means the declared endpoint/heldout design has shown enough response variation in a disjoint pilot to justify spending a fresh confirmatory target.

### stop_endpoint_variation

Too few pilot blocks are estimable.

The endpoint/version stops.

No threshold lowering, endpoint swap, block change, or alternate target is allowed inside that protocol version.

## Evidence firewall

The pilot:

- is never scored as a connectivity effect;
- is never pooled with confirmation;
- never enters the predictive denominator;
- cannot be reused as a second confirmation.

Its only output is feasibility.

## Why this is different from candidate hunting

The pilot and confirmatory partitions are declared **before** pilot response access.

A failure consumes the candidate/version rather than triggering a search for a better target in the same data.

This converts endpoint variation from an accidental post-response surprise into an explicit prospective design object.

## Relationship to Structural ↔ EGWE

Structural asks whether a typed connectivity representation adds information beyond current state.

EGWE asks whether the supplied state is sufficient for future fate.

v0.30 adds a prerequisite:

> before testing future-state sufficiency, the future-state endpoint itself must generate enough informative transitions to make the declared loss estimable.

Thus the methodological spine becomes:

    response-blind system admission
        → burned transition pilot
        → endpoint estimability gate
        → typed connectivity/state freeze
        → confirmatory future response
        → adequacy / portability / residual-history tests

## Current boundary

PNW and RMNP remain closed.

v0.30 does not reopen their targets and does not authorize a new empirical candidate.
