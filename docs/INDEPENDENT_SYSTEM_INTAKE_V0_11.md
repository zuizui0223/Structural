# Independent system intake v0.11

## Purpose

v0.10 remains the frozen response-sealed intake audit. v0.11 is a future-only bridge that prevents a newly arriving system from treating a clean v0.10 receipt as permission to proceed directly to pilot response access.

A future system must leave intake with permission to **construct two pre-pilot objects**, not one:

1. a v0.31 disjoint pilot/confirmatory protocol;
2. a v0.42 response-quality attrition contract bound to the exact v0.31 fingerprint.

## Replay, not rewrite

The v0.11 validator first replays the existing v0.10 validator unchanged. All source identity, freshness, file-role, response-sealing, anti-selection and closed-system checks therefore remain intact.

Historical v0.10 receipts are not re-adjudicated.

## Successful action

A clean intake returns:

    eligible_to_construct_v0_31_and_v0_42_pre_pilot_contracts

and authorizes only:

    construct_v0_31_protocol_then_bind_v0_42_quality_contract_only

The ordering matters. The v0.42 contract cannot be created until the exact v0.31 fingerprint exists.

## Evidence ceiling

A successful intake still authorizes **zero response access**:

- burned-pilot response: false;
- confirmatory response: false;
- mechanism response: false;
- TTF handoff: false.

It also emits no effect size, prediction score or predictive-denominator contribution.

## Future path

    independent system arrives response-sealed
      -> v0.10 intake replay
      -> v0.11 bridge PASS
      -> construct v0.31 protocol
      -> bind/freeze v0.42 quality contract
      -> only then consider burned-pilot authorization

This closes the stale pre-v0.42 instruction that a clean intake should construct only v0.31.
