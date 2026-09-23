# Confirmatory admission raw-pilot replay v0.38

## Purpose

v0.37 removed trust in the pilot result's stored estimability flags by reconstructing block-level gates and arithmetic.

One evidence gap remained: an internally consistent pilot-result JSON could still be written by hand without proving that it came from the actual burned-pilot input.

v0.38 closes that gap.

## Required queue artifacts

Every non-empty confirmatory queue entry must now identify:

1. its frozen v0.31 protocol;
2. the raw burned-pilot CSV;
3. the SHA-256 of that exact CSV;
4. the stored v0.32 pilot result;
5. the deterministic admission receipt.

The raw pilot is permanently burned evidence. It is not predictive evidence and cannot enter the confirmatory denominator.

## Replay rule

CI reruns the v0.32 pilot runner from:

`frozen protocol + raw pilot CSV`

The replay must exit as qualified and the complete replayed result object must equal the committed `pilot_result.json` exactly.

Only after that exact replay does CI apply:

- v0.37 arithmetic and block-estimability reconstruction;
- v0.33 confirmatory-exposure and fingerprint gate;
- deterministic receipt reproduction.

Thus neither a hand-edited `estimable=true` nor a fully fabricated but internally coherent pilot-result JSON can enter the queue.

## Evidence boundary

A v0.38 queue PASS still means only:

`freeze_confirmatory_protocol_only`

It does not authorize confirmatory response access.

The pilot contributes zero observations to predictive scoring, PNW/RMNP remain closed, and the live confirmatory queue remains empty.

## TTF

TTF remains outside this admission chain.

Cross-species transferability cannot authorize, select, rescue or relax a Structural pilot. A future TTF handoff begins only after the relevant within-system protocol has independently passed its own Structural qualification path.
