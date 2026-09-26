# Confirmatory admission queue v0.42

## Role

This is the live queue for future Structural systems after the response-quality attrition extension.

It supersedes v0.38 only for **future queue admission**. The v0.38 queue and fixtures remain immutable historical/replay infrastructure for the v0.31-v0.40 chain and downstream mechanism tests.

The live queue begins empty.

## Required entry

Every entry binds:

- system ID;
- v0.31 protocol ID and path;
- v0.42 response-quality contract path;
- exact raw burned-pilot CSV path;
- SHA-256 of that raw pilot;
- exact stored v0.32 pilot result;
- exact stored v0.42 future-admission receipt;
- parent v0.31 protocol fingerprint;
- v0.42 quality-contract fingerprint.

## Validator

scripts/validate_confirmatory_queue_v0_42.py independently performs the following sequence:

1. verify the raw burned-pilot SHA-256;
2. rerun the exact v0.32 runner from the v0.31 protocol and raw CSV;
3. require exact equality with the stored v0.32 pilot result;
4. reconstruct the v0.42 response-quality contract;
5. recompute the combined future admission decision;
6. require both response-quality survival and the existing v0.31-v0.33 admission chain to pass;
7. reproduce the stored v0.42 receipt exactly;
8. verify both protocol and quality-contract fingerprints.

A manually edited pass flag, quality count, receipt or summary cannot enter the queue.

## Evidence boundary

Queue admission still authorizes only:

    freeze_confirmatory_protocol_only

The queue never authorizes confirmatory response access.

Pilot effect size remains null, prediction score remains null and predictive-denominator contribution remains zero.

## Historical boundary

No PNW, RMNP, LandFrag, GIFT, ISAR or murundu result is re-adjudicated by this queue.

LandFrag remains a closed 29/30 response-quality STOP and is not eligible for insertion.

## Synthetic CI

The repository retains one explicitly nonempirical synthetic queue fixture. CI replays it on every supported Python version so the validator is exercised with a real non-empty entry while the live empirical queue remains empty.
