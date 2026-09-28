# Boreal v0.31 + v0.42 pre-pilot constructor v0.80

v0.80 prepares the last response-sealed objects before a burned pilot could ever
be authorized.

## Parent gate

The constructor requires a validator-clean v0.12 intake receipt. Its intake
fingerprint must exactly match the supplied intake object, and the receipt must
authorize construction of v0.31 and v0.42 while still denying all response
access.

The v0.75 spatial receipt file SHA must also exactly equal the SHA frozen inside
the v0.12 intake.

## v0.31 protocol

Pilot and confirmatory partitions are the exact deterministic v0.75 spatial
block IDs.

The burned-pilot species universe is fixed once from pilot response only:
include beetle species detected on at least two distinct frozen pilot islands,
then apply that identical species set to every held-out pilot spatial block.

The generic estimability gates remain:

- minimum held-out target rows: 3;
- minimum training positives: 5;
- minimum training negatives: 5;
- minimum estimable pilot blocks: 3.

The pilot remains feasibility evidence only.

## v0.42 response-quality contract

The contract is fingerprint-bound to the constructed v0.31 protocol and requires
at least three response-qualified pilot blocks.

A block survives only if the fixed pilot-supported species universe yields at
least three exact binary island-by-species held-out targets. Unexpected response
codes, missing frozen pilot islands, or failure to construct the common species
universe are terminal STOP conditions. No post-open rescue is permitted.

## Access ceiling

The constructor runs the generic v0.31 and v0.42 evaluators, but a pass does not
itself authorize response access. It only produces frozen pre-pilot contracts.
A later, separate authorization gate is still required before the beetle pilot
matrix can be opened.
