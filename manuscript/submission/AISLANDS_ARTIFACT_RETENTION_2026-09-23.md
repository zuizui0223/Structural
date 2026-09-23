# A-Islands authoritative artifact retention check — 2026-09-23

## Finding

The one-time A-Islands strong-reference raw outcome artifact is still available in GitHub Actions and has been independently reverified.

It lives in the **source repository**:

`zuizui0223/eog`

not in `zuizui0223/Structural`.

The authoritative execution identity is:

- source commit: `a9329d929933c919fe6c1c03934f0314c40f5c50`;
- workflow run: `31564146592`, attempt 1;
- artifact: `9128998976`;
- artifact name: `aislands-isolation-adequacy-authoritative-outcome`.

## Current artifact status

GitHub reported on 2026-09-23:

- `expired = false`;
- created: `2026-08-12T04:52:16Z`;
- expires: **`2026-11-10T04:42:52Z`**;
- artifact size: 36,856,265 bytes;
- artifact digest:
  `sha256:59363bc82924e74445ad10a1d9732511e9bd5bcd056bef17ac89166f45b8355e`.

The downloaded ZIP independently reproduced that exact SHA-256.

## Internal output verification

The downloaded artifact also reproduced the committed authoritative hashes:

- decompressed `heldout_predictions.csv`:
  `511ffb27c5d3d1f446927afd179ce774809127067e19c7847cf4c02923ce0b43`;
- `fold_applicability_and_scores.csv`:
  `89de3b891cec5c838e9624d2e74cc4e8c977ad32772161f2e9856b879a6b7fb4`;
- `species_summary.csv`:
  `7ff1159d44220c5e617c759ad88a9a6fce75a25ff9ac96a771a9505be9d3f8ec`;
- `aggregate_result.json`:
  `d361236eb0197807507571eee5e49769e8ad2b994915cb4caceff8b70242c670`.

The embedded execution provenance also matches the committed Structural provenance for source commit, workflow run, attempt, result fingerprint and output hashes.

## Retention risk

The raw authoritative artifact is **not yet preserved outside GitHub Actions**.

GitHub reports an expiration time of **2026-11-10T04:42:52Z**.

Therefore the final archive workflow must preserve this exact verified ZIP, or preserve equivalent verified members while retaining the ZIP digest and member hashes, before the Actions artifact expires.

This is an archive/reproducibility requirement. It does not reopen or rerun the scientific analysis.

## Local verifier

After downloading the artifact ZIP, verify it with:

```bash
python scripts/verify_aislands_authoritative_artifact_v0_1.py \
  aislands-isolation-adequacy-authoritative-outcome.zip
```

A successful verification requires both the ZIP digest and all declared internal output hashes to match.

## Release implication

Do not mark the checklist claim that the raw authoritative outcome is archived as complete until the verified artifact has been copied into the final durable archive and checked there.

The current release remains on `HOLD_HUMAN_POLICY_GATES` for separate author/journal reasons; this retention requirement is an additional archive-content condition for the eventual release.
