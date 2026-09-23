# Confirmatory admission verifier v0.37

## Purpose

v0.37 removes the last important self-reported quantity from the v0.36 admission path.

The v0.32 burned-pilot runner records a block-level audit with test and training class counts plus an `estimable` flag. v0.36 checked that the number of `estimable=true` blocks matched the reported total, but it did not independently reconstruct whether those flags were justified by the frozen v0.31 thresholds.

v0.37 now recomputes that decision.

## Recomputed block gate

For every held-out block, the verifier reconstructs the exact v0.30/v0.32 rules:

```
test_rows >= minimum_test_rows
train_positive >= minimum_train_positive
train_negative >= minimum_train_negative
```

Only a block satisfying all three is recomputed as estimable.

The stored `estimable` flag and `reasons` list must exactly match this reconstruction.

## Arithmetic integrity

The verifier also requires:

- `positive + negative = applicable_rows`;
- test positive/negative counts sum to test rows;
- training positive/negative counts sum to training rows;
- each training set equals the complement of its held-out block;
- held-out blocks partition the global applicable, positive and negative counts;
- block labels are nonempty and unique;
- the reported estimable-block count equals the independently recomputed count;
- the recomputed count itself meets the frozen `minimum_estimable_blocks` threshold.

Thus a pilot result cannot enter the confirmatory queue by editing `estimable=true`, its summary count, or its global class totals while leaving contradictory block counts.

## Version boundary

v0.37 is a verifier hardening, not a new biological protocol and not a new evidence denominator.

The committed data shapes remain:

- v0.31 protocol;
- v0.32 pilot-result schema;
- v0.36 queue and receipt schema.

Existing live queue state remains empty.

No confirmatory response is authorized by this verifier. A clean pass still licenses only:

`freeze_confirmatory_protocol_only`

## TTF

Nothing changes for TTF.

TTF remains a later, independent out-of-species transferability layer. It cannot relax, substitute for, or select systems through the Structural burned-pilot estimability gate.
