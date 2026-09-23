# Structural release bundle builder v0.1

## Purpose

The release bundle builder prepares the exact payload that can later be deposited in the durable DOI/public archive.

It does **not** publish anything and does not authorize a final tag.

The bundle combines:

1. the exact Git-tracked repository snapshot at `HEAD`;
2. the already-verified structural submission package v2;
3. the one-time A-Islands strong-reference raw outcome ZIP;
4. the original A-Islands authoritative benchmark ZIP;
5. the frozen A-Islands isolation contract/geometry ZIP;
6. the frozen Tanzania held-out result ZIP;
7. a machine-readable SHA-256 manifest.

## CI staging mode

CI has no access to the private retained ZIPs.

Therefore it runs:

```bash
python scripts/build_release_bundle_v0_1.py \
  --submission-package build/structural_submission_v2
```

This must build a deterministic **staging** bundle while explicitly recording the four missing external artifacts.

With the current human-policy HOLD, the expected stage is:

`STAGING_HOLD_HUMAN_POLICY_GATES`

Missing raw ZIPs are not silently treated as archived.

## Complete archive mode

After the human/manual release gates clear, download the four round-trip-verified retained ZIPs and run:

```bash
python scripts/build_release_bundle_v0_1.py \
  --submission-package build/structural_submission_v2 \
  --aislands-strong-raw /path/to/aislands-isolation-adequacy-authoritative-outcome.zip \
  --aislands-original /path/to/aislands-authoritative-benchmark.zip \
  --aislands-contract /path/to/aislands-isolation-adequacy-contract.zip \
  --tanzania-result /path/to/tanzania-heldout-current-flow-eog-result.zip \
  --require-complete
```

Every external ZIP must reproduce the exact committed byte size and SHA-256 from its retention receipt.

## Determinism

The release ZIP is deterministic for an unchanged commit and unchanged inputs:

- members are sorted lexicographically;
- member timestamps are fixed to 1980-01-01;
- file mode is normalized;
- the internal manifest hashes every bundled file except itself;
- an external receipt records the final ZIP SHA-256.

## Important boundary

A successful complete bundle still does **not** authorize:

- DOI publication;
- `v0.1.0` creation;
- a GitHub Release;
- journal submission.

The existing release preflight and a later release-ready receipt tied to the exact candidate commit remain authoritative for those actions.
