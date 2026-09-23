# Structural release-candidate verifier v0.2

## Purpose

This verifier turns the release/admin sequence into a reproducible check without authorizing publication.

It connects four objects:

1. the exact Git commit;
2. the v0.1.0 release preflight;
3. author/journal-specific approval state;
4. the built submission package.

## Stages

### HOLD_HUMAN_POLICY_GATES

At least one author approval, author metadata field, journal-specific Guide check, or equivalent human/manual gate is unresolved.

This is the current expected stage.

### READY_FOR_IDENTIFIER_RESERVATION_AND_IDENTIFIER_ONLY_PR

All human/manual gates are complete, but `<RELEASE_TAG>` / `<ARCHIVE_DOI>` placeholders remain unresolved.

This means the project may proceed to DOI reservation and an identifier-only repository change. It does **not** authorize a final release.

### READY_FOR_RELEASE_CANDIDATE_RECEIPT

Human/manual gates and identifiers are complete, and the repository/package state is internally consistent.

Even this stage does not create or authorize the final tag by itself. A separate release-ready receipt tied to the exact candidate commit is still required by the preflight.

## Package verification

When run against a built package, the verifier requires:

- package `source_commit == git HEAD`;
- frozen A-Islands strong-reference fingerprint matches the submission manifest;
- Tanzania fingerprint matches the submission manifest;
- EOG-WF empirical denominator remains excluded;
- all canonical submission figures exist in the package.

## CI use

After the normal package build:

```bash
python scripts/verify_release_candidate_v0_2.py \
  --package-dir build/structural_submission_v2 \
  --allow-hold
```

`--allow-hold` means that a correctly represented human-policy HOLD is CI-green. It does not convert HOLD to GO.

## Scientific boundary

The verifier may inspect release/admin metadata and frozen result identities.

It may not:

- rerun or retune scientific outcomes;
- alter R3;
- alter graph scales or taxa;
- alter the empirical denominator;
- authorize a Structural candidate;
- use TTF to change release or scientific status.
