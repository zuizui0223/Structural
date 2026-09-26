# Indo-Pacific atoll package resolution — Zenodo identity v0.1

## Resolved

The FAIR² source is now bound to two public persistent identifiers:

- SenScience FAIR² package DOI: `10.71728/senscience.4f2j-8h1k`
- Zenodo mirror DOI: `10.5281/zenodo.18848127`

The Zenodo record was resolved metadata-only through the FAIRdata.ai registry, which identifies the Zenodo record as `IsVersionOf` the SenScience package.

The source data article independently states that the FAIR² package is archived in Zenodo and exposed through MLCommons Croissant-compatible metadata/download components.

## Still unresolved

Structural has **not** downloaded the atoll data package.

The following remain unknown in this lane:

- exact file list inside Zenodo record 18848127;
- byte size of each file;
- checksum of each file;
- mapping from each file to safe metadata / geometry / response / mixed / unknown.

No vascular-plant table has been parsed.

## Why this matters

The next gate is physical identity, not ecological analysis.

Before v0.11 intake, the project must be able to reproduce a content-blind inventory of the exact archived package. A DOI alone is insufficient because it does not prove which bytes constitute the response or which files can be opened safely.

## Resume condition

Proceed only when a metadata-only interface exposes the Zenodo record's file names, sizes and checksums, or when the exact archive can be downloaded opaquely and hashed without decoding any member content.

Then use the existing pipeline:

    exact Zenodo package identity
      -> v0.11 content-blind inventory
      -> v0.12 SHA-pinned file-role firewall
      -> open safe metadata/geometry only
      -> construct formal v0.11 independent-system intake
      -> v0.31 + v0.42 pre-pilot freeze
      -> only later consider burned-pilot response access

## Current evidence state

- active empirical candidate: no;
- plant response opened: no;
- plant prevalence inspected: no;
- source-pool-handoff direction inspected: no;
- pilot authorized: no;
- confirmatory response authorized: no.

The Zenodo identifier resolves provenance only. It does not promote the system into the empirical denominator.
