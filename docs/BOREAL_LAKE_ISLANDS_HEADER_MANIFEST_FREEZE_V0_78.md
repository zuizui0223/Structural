# Boreal Stage-A provenance and header manifest freeze v0.78

v0.78 closes the final provenance gap between the manual credential-bearing
Stage-A run and v0.74 safe-row projection.

## Stage-A workflow

The new workflow is manual-only and refuses to run unless
`GITHUB_REF=refs/heads/main`. Before any Dryad access it writes a safe
`execution_context.json` containing the repository, exact head SHA, run ID,
run attempt and workflow reference.

The workflow then reuses the frozen v0.72 exact-byte transport and v0.71
header-only audit, deletes the raw mixed CSVs, and uploads only four JSON files.

## Manifest freezer

`scripts/freeze_boreal_header_manifests_v0_78.py` accepts only those four JSON
files. It verifies:

- main-branch execution and repository identity;
- exact transport success with zero semantic row access;
- qualified header-only audit;
- exact v0.71 file SHA identities;
- unchanged safe/protected declarations;
- a valid 64-hex header SHA for each mixed file;
- no evidence-boundary drift.

Only after those checks does it emit the schema already required by v0.74:

`structural.boreal_lake_islands_header_manifest_freeze.v0_74`

with status `header_manifests_frozen_before_row_projection` and
`safe_row_projection_authorized=true`.

This is a provenance authorization, not ecological evidence. The freezer opens
zero row values and leaves v0.12, pilot and confirmatory response access closed.
