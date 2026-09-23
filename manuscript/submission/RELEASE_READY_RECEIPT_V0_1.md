# Structural release-ready receipt v0.1

## Purpose

The release-ready receipt is the final machine gate before the software/archive release.

It is intentionally **not committed to the release candidate before tagging**.

A receipt binds to one exact Git commit. Committing the receipt itself would create a new commit and invalidate that binding.

## Current state

With the present author/journal-policy HOLD and incomplete CI staging bundle, the evaluator must return:

`HOLD_NOT_RELEASE_READY`

CI treats that correct HOLD as success only when `--allow-hold` is supplied.

## Issuance requirements

A release-ready receipt can be issued only when all of the following are true:

1. the release-candidate verifier returns `READY_FOR_RELEASE_CANDIDATE_RECEIPT`;
2. the committed release preflight has been explicitly advanced to the same state after human/manual approval;
3. the submission package is verified and bound to exact `git HEAD`;
4. the deterministic release bundle contains all four retained raw ZIPs;
5. bundle ZIP size and SHA-256 reproduce its external bundle receipt;
6. the internal bundle manifest is bound to the same `git HEAD`;
7. candidate tag is identical across preflight, candidate verifier and bundle.

## Receipt authorizations

Only an issued receipt authorizes the release workflow to:

- create `v0.1.0` exactly at the receipt's source commit;
- create the matching GitHub Release;
- publish the already-reserved archive record with the verified complete bundle.

It does **not** authorize final journal submission. The publisher-rendered preview remains a journal-UI gate.

## Exact-tag rule

Once created:

- `v0.1.0` must point exactly to the receipt's source commit;
- the tag must never be moved to a later commit;
- any repository change after receipt issuance requires a new candidate commit, rebuilt package, rebuilt bundle and new receipt.

## Command

Current CI/HOLD check:

```bash
python scripts/issue_release_ready_receipt_v0_1.py \
  --submission-package build/structural_submission_v2 \
  --release-bundle-zip build/structural_release_bundle_v0_1.zip \
  --release-bundle-receipt build/structural_release_bundle_v0_1.zip.receipt.json \
  --allow-hold
```

After every human/manual and identifier gate clears, run the same command against the **complete** release bundle without `--allow-hold`.

The generated receipt is a release artifact. Do not commit it before the tag is created.
