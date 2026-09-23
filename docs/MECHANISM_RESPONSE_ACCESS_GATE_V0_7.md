# Mechanism response access record gate v0.7

## Purpose

v0.6 authorizes one exact lane/partition response read.

v0.7 **consumes** that authorization and records exactly which response file was opened before any scoring is permitted.

## Authorization replay

The v0.6 authorization receipt must be Git-tracked.

v0.7 replays v0.6 from the tracked v0.5 receipt and all raw qualification inputs.

The stored v0.6 receipt must match the replay exactly.

## Lane isolation

Response files are lane-specific.

### M1 contemporary colonization

Exact surface:

`partition_unit,block,unit_id,z_t,z_t1`

Only rows with `z_t=0` are permitted.

Thus authorizing M1 does not expose M2's state-1 transition outcomes.

### M2 rescue/persistence

Same columns, but only `z_t=1` rows are permitted.

### M3 historical legacy

Exact surface:

`partition_unit,focal_population,source_population,comparison_class,genetic_value`

Every focal/source/comparison tuple must already exist in the response-blind source-pair design qualified before genetic outcomes were opened.

### M4 environmental proxy

Exact surface:

`partition_unit,block,unit_id,target`

Every unit and block must already occur in the frozen enriched environment matrix.

## Missing outcome values

Missing confirmatory outcomes remain missing.

They are counted explicitly and are not converted to zero, absence, non-colonization, extinction or low genetic affinity.

## What the access receipt binds

The receipt records:

- authorization id and authorization-receipt SHA-256;
- protocol fingerprint;
- exact response partition;
- response-file SHA-256;
- row/support audit;
- a deterministic access id.

After the receipt is created:

- `response_access_consumed = true`;
- the prior response authorization is no longer treated as open;
- only frozen scoring is authorized.

## Still no scientific result

v0.7 does not calculate an effect.

It sets:

- effect size = null;
- prediction score = null;
- mechanism claim = unauthorized;
- TTF handoff = unauthorized.

The only next action is:

`run_frozen_lane_scoring_only`.

## Current state

No empirical mechanism response has been accessed. CI uses synthetic response files only.
