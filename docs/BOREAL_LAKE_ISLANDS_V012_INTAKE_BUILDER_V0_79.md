# Boreal v0.12 intake builder v0.79

v0.79 removes the final manual JSON-composition step before the generic v0.12
future-intake validator.

## Inputs

The builder accepts only successful response-independent receipts from:

- v0.74 safe geometry/habitat projection;
- v0.75 spatial partition;
- v0.76 habitat reference.

It verifies that v0.75 binds to the exact v0.74 geometry SHA and that v0.76
binds to the exact v0.74 habitat SHA. It also requires at least 9 spatial
blocks, at least 3 pilot blocks, at least 6 confirmatory blocks, complete
42-island partition coverage, and the original response-independent evidence
ceilings.

## Source files in the generated intake

The generated v0.12 intake contains exactly three source-file roles relevant to
the admission gate:

1. `safe_geometry.csv` — role `geometry`, opened=true;
2. `habitat_reference.csv` — role `safe_metadata`, opened=true;
3. `beetles_speciesmatrix_presenceabsence.csv` — role `response`,
   opened=false, using the exact v0.65 Dryad SHA.

Thus safe derived predictor files are explicitly distinguished from the sealed
466-species occurrence matrix.

## Freshness semantics

The candidate is a single-time-slice static occurrence system. v0.12 explicitly
permits that endpoint. “Connectivity question already published = no” refers to
the exact v0.55 species-conditioned internal-source adequacy test, not to the
fact that the source article studied pyrodiversity and classical isolation.

“Response result seen by project = no” refers to the species-level 42-island
beetle occurrence target, which remains sealed. Published richness summaries
are not the v0.55 target response.

## Output ceiling

The builder immediately passes its generated object through
`validate_independent_system_intake_v0_12.py`. Success authorizes only:

- construction of a v0.31 partition protocol; then
- a fingerprint-bound v0.42 quality contract.

It does not authorize burned-pilot response, confirmatory response, mechanism
claims, or predictive evidence.
