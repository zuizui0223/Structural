# Mechanism confirmatory protocol freeze gate v0.5

## Purpose

v0.4 admits mechanism lanes one by one.

v0.5 freezes the **actual confirmatory protocol** for one eligible lane.

It still does not open the response.

## Why one protocol per lane

The four mechanism hypotheses do not share the same endpoint:

- M1: 0→1 colonization;
- M2: 1→0 extinction / persistence;
- M3: genetic source affinity;
- M4: residual topology information after an enriched environment reference.

A single generic “mechanism protocol” would make it too easy to change the endpoint or scoring rule after seeing which result is favourable.

Therefore each eligible lane receives its own immutable protocol fingerprint.

## Parent replay

The freezer reruns v0.4 from the raw inputs.

The selected lane must still be listed in `eligible_lanes`.

The lane protocol declares `parent_binding_mode = bind_from_replayed_v0_4_admission_at_freeze`.

The freezer then binds the receipt automatically to:

- the same system id;
- the replayed parent mechanism protocol fingerprint;
- the replayed Structural protocol fingerprint.

Those fingerprints are not manually transcribed into the lane draft.

## Common frozen state

Every lane freezes:

- response partition;
- local held-out design;
- spatial-transfer design;
- primary estimand;
- reference definition;
- candidate definition;
- scoring rule;
- uncertainty rule;
- success rule;
- secondary diagnostics.

The protocol must state:

- response firewall = sealed;
- confirmatory response not accessed;
- protocol not selected after response;
- mechanism claim not authorized.

## Lane-specific invariants

### M1

Must retain:

- target = 0→1;
- non-event = 0→0;
- frozen pilot minima;
- a predeclared detection model.

### M2

Must retain:

- target = 1→0;
- non-event = 1→1;
- frozen pilot minima;
- a predeclared detection model.

### M3

Must freeze:

- genetic outcome;
- genetic null;
- geographic control;
- graph-connected versus alternative source comparison.

The genetic outcome is still unopened.

### M4

The enriched predictor list must match the response-blind parent list exactly.

No new predictor may appear during confirmatory-protocol freezing.

The ecological response remains unopened.

## Output ceiling

A clean freeze records the protocol fingerprint and qualification-input SHA-256 values.

It still has:

- no effect size;
- no prediction score;
- zero predictive denominator;
- zero mechanism-claim contribution;
- no confirmatory response authorization;
- no mechanism claim;
- no TTF handoff.

The only next action is a **separate lane-specific response-authorization gate**.

## Current state

No empirical system is active. CI exercises synthetic protocols only.
