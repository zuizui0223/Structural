# Boreal mixed-file header freeze v0.71

## What changed

The remaining boreal geometry/habitat problem is now an **execution/transport problem**, not a missing firewall design.

Structural already has a SHA-pinned mixed-CSV firewall. v0.71 adds the missing pre-row stage: exact bytes are hashed, then **only the first physical CSV record is decoded**. No data row is semantically opened.

The two required Dryad files were already frozen metadata-only in v0.65:

- `alpha_diversity_ALL_islands.csv`: file 4569034, 3441 bytes, SHA-256 `f63b37b3c4c9d5453c53b0b565c4bfb7b8485e017f257fbeea663b20cbf6bddf`;
- `RDA_environmental_variables.csv`: file 4569033, 8594 bytes, SHA-256 `30b296c8243d433b8c4aaa2e934dcb9d57b0f909094ad03cfc645babbab61046`.

No new Dryad content request is made by this revision.

## Two-stage firewall

### Stage A — header only

`scripts/audit_boreal_mixed_headers_v0_71.py`:

1. verifies exact byte size;
2. verifies the already-frozen file SHA-256;
3. decodes only the first physical CSV record;
4. matches declared safe and protected column names;
5. leaves every unclassified column closed;
6. emits the observed header SHA and a candidate manifest.

A pass means only **qualified to freeze header manifests**.

It does **not** authorize safe-row projection in the same execution.

### Stage B — later revision only

After the Stage-A result is committed as a separate pre-row revision, the existing
`structural.mixed_csv_firewall.project_safe_columns` machinery may be bound to
that exact file SHA + header SHA manifest.

This separation prevents a header discovered at runtime from being immediately
used to reinterpret rows in the same run.

## Minimal geometry projection

For the alpha-diversity mixed file, v0.71 ultimately needs only:

- `Island`
- `Lat`
- `Long`

The extra response-independent columns are classified as safe only because their
names were already frozen in v0.68. Response-derived richness columns are
protected. Optional or response-selected scale columns remain closed.

## Minimal habitat projection

For the RDA mixed file, the intended local habitat pool is restricted to:

- `Basal.area`
- deciduous canopy cover
- deciduous understory cover
- conifer canopy cover
- conifer understory cover
- `total.cwd.volume`

plus `Island` for routing.

Other documented non-response columns remain closed at this stage. This is
deliberately narrower than the maximum v0.68 allowlist.

## What remains blocked

The exact file bytes are still unavailable through the previously attempted
Dryad transport route. Therefore:

- header SHA values are not yet known;
- coordinates are still 0/42;
- safe habitat rows are still unopened;
- v0.11 remains unauthorized;
- fresh denominator remains zero.

The next valid event is to obtain exact SHA-matching local bytes through an
independently auditable route, run Stage A only, and commit the resulting header
manifests before any row-level projection.
