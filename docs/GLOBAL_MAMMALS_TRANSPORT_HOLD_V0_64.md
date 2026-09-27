# Global mammal pristine transport HOLD v0.64

## Current boundary

The 5,592-island mammal system remains **pristine and response-sealed**.

Its predictor-side island geography is no longer the blocker.

A response-independent Weigelt mirror has been independently resolved, its mixed `islanddata` table placed behind a column firewall, and a compact safe table frozen:

- Weigelt rows: **17,883**;
- unique Weigelt IDs: **17,883**;
- safe columns: **23**;
- safe-table SHA-256:
  `ebb4b54cc9b056a1ea61fcae3a53bf578c0e47488e4a496d40fceaeca4f4b8af`.

The external-isolation reference variables are complete across all 17,883 safe rows:

- area;
- mainland distance;
- current isolation / SLMP;
- past connection / GMMC;
- elevation;
- temperature mean and variation;
- climate-change velocity;
- precipitation mean and variation.

The remaining blocker is transport of the exact frozen 2024 mammal presence/absence matrix.

## Frozen response identity

Dryad DOI:

    10.5061/dryad.hmgqnk9j2

Frozen current response file:

    Appendix_1_presence_absence.csv

Physical identity:

- bytes: **60,486,843**;
- SHA-256:
  `32bf3f077af7e66ddcbf05fc675d6c51656f59111c27cd37129e14c658430fa6`;
- source-reported island rows: **5,592**.

The source documentation states that Appendix 1 island-row IDs correspond to the `ID` column in Appendix 2.

## Frozen ID-only crosswalk

The crosswalk science is already fixed.

When the exact bytes become available, the only semantic opening permitted before formal intake is:

- first CSV field of the header;
- first CSV field of each of the 5,592 data rows.

All species headers and all 0/1 occurrence values remain sealed.

ID normalization is fixed to:

1. strip surrounding whitespace;
2. if the string is a nonnegative integer or an integer with only zero decimal digits, canonicalize to a base-10 integer string;
3. otherwise retain the exact stripped UTF-8 string.

The join is exact canonical membership against frozen Weigelt `id`.

Forbidden fallbacks:

- island-name fuzzy matching;
- coordinate nearest-neighbour matching;
- archipelago-assisted matching;
- manual matching informed by outcomes.

## Transport audit

Three distinct Dryad file routes have now been tested, all **before any response byte was received**.

### v0.61
`/api/v2/files/{id}/download`

Result:

    HTTP 401 before response bytes

### v0.62
`/downloads/file_stream/{id}`

Result:

    HTTP 403 before response bytes

### v0.63
`/stash/downloads/file_stream/{id}`

Result:

    HTTP 403 before response bytes

Across all three:

- response bytes read: **0**;
- routing IDs decoded: **0**;
- species headers decoded: **0**;
- occurrence values decoded: **0**.

The biological response is therefore still pristine.

## Stop rule

No further Dryad URL variants may be tried.

The project resumes this system only when an independently auditable source provides bytes that satisfy **both**:

- exact length = 60,486,843 bytes;
- exact SHA-256 =
  `32bf3f077af7e66ddcbf05fc675d6c51656f59111c27cd37129e14c658430fa6`.

A separately supplied exact file is also acceptable if its provenance is recorded and it has not been semantically preprocessed for Structural.

Once exact bytes exist, resume at the frozen ID-only crosswalk. Do not redesign the join.

## Why an older version is not substituted

Dryad records an older 2023 Appendix 1 and a corrected June-2024 presence/absence matrix in which duplicated entries were removed.

The current candidate was prospectively frozen to the 2024 version.

Transport failure is not a scientific reason to silently replace the response with the older version.

## Island-biogeography state

The v0.55 dual-isolation hypothesis remains untested.

The predictor side is now unusually strong:

- external current isolation;
- past land connection;
- island area;
- climate;
- elevation;
- safe island identity.

But **internal source isolation is species-conditioned** and therefore cannot be built until the exact mammal response can at least be routed to the frozen island geography.

The next valid scientific event is therefore one of two things:

1. exact frozen Appendix 1 bytes become available and the ID-only crosswalk resumes; or
2. another genuinely new island system enters v0.55 response-sealed.

No result is inferred from the transport failure itself.
