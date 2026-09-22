# Transition pilot partition freeze v0.31

## Purpose

v0.30 established that endpoint-transition estimability must be tested before a fresh confirmatory future target is spent.

v0.31 makes that requirement executable.

Before any pilot response is opened, a protocol must freeze:

- the system;
- the partition axis;
- a burned pilot partition;
- a disjoint confirmatory partition;
- one endpoint definition;
- one heldout design;
- the exact test-row and class-support gates.

## Two evidence partitions

### Pilot

The pilot exists only to answer:

> Can the declared future endpoint support the declared heldout design often enough to make the planned loss estimable?

It never estimates a connectivity effect and never enters the predictive denominator.

### Confirmatory

The confirmatory partition remains completely sealed during the pilot.

Even if the pilot qualifies, confirmation does not open immediately. A new confirmatory protocol must still freeze:

- typed connectivity;
- reference state;
- feature construction;
- scoring implementation;
- response firewall.

## Fail-closed rules

A protocol stops before pilot opening when:

- the pilot response was already opened before partition freeze;
- the confirmatory response was already opened;
- pilot and confirmatory units overlap;
- the pilot is designated for effect estimation.

A pilot failure consumes the version. No threshold lowering or endpoint swapping is allowed.

## Fingerprint

The v0.31 protocol object has a canonical SHA-256 fingerprint. Any change to partitions, endpoint semantics or gates creates a different protocol identity.

## Current empirical boundary

PNW and RMNP remain closed and are not candidates for repair.

v0.31 does not authorize a new biological system. It creates the machinery that any future system must pass before its pilot response is opened.
