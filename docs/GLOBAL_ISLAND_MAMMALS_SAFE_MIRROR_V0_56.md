# Global 5,592-island mammals — safe Weigelt mirror v0.56

## Status

The pristine mammal response remains completely sealed.

The previous HOLD was broad: the current Dryad mixed island table could not be transported safely, so the physical island geography needed for a prospective Structural design could not be frozen.

That blocker is now narrower.

A public UvA/Figshare dataset, DOI `10.21942/uva.22788464.v5`, documents a `reference.gpkg` containing the Weigelt et al. (2013) `islanddata` point table **without modifications**, plus island/archipelago reference geography.

Structural has now resolved the exact physical location of that member without downloading its payload.

## Figshare container

Version 5 contains one archive:

- `labs.zip`
- 2,617,794,182 bytes
- MD5 `da14f19b12bae704b9df4e5c380b69fd`
- license: CC BY 4.0.

The metadata probe made zero file-content requests and zero requests to the mammal response.

## ZIP directory-only audit

Only 131,462 bytes of ZIP tail / central-directory metadata were read.

The archive contains four entries:

- `mountains.gpkg`
- `__MACOSX/._mountains.gpkg`
- `reference.gpkg`
- `__MACOSX/._reference.gpkg`.

No member payload was read or decompressed.

### reference.gpkg

Exact ZIP metadata:

- compression: Deflate (method 8);
- compressed size: **2,288,242,143 bytes**;
- uncompressed size: **3,859,476,480 bytes**;
- CRC32: `ff89b951`;
- local-header offset: `329551200`.

The full 2.62-GB archive therefore does **not** need to be downloaded as a unit. A future one-shot can read the small local header, derive the exact compressed-data start, stream only the `reference.gpkg` member, and verify its uncompressed size and CRC before opening the GeoPackage.

## Why this is scientifically useful

The 5,592-island mammal response is binary and still pristine.

For v0.55, the remaining pre-response need is a response-independent island geography that can support:

- external mainland/current isolation;
- historical isolation or land connection;
- island area and environment;
- generic archipelago permeability;
- stable island identifiers or a reproducible ID crosswalk.

The Figshare mirror offers a route to recover the original Weigelt island reference geography without touching mammal occurrence values.

## Next gate

The next action is one response-independent extraction of `reference.gpkg` only.

After exact member decompression, the workflow may inspect GeoPackage table names/schemas and the `islanddata` table. It must preferentially output only response-independent identifiers/geography/environment fields required for crosswalking and v0.55 design.

The giant GeoPackage itself must be deleted before artifact upload.

No mammal Dryad response file may be requested.

## Evidence boundary

This mirror resolution is **not empirical biological evidence**.

Current counters remain:

- mammal presence/absence response requests: 0;
- mammal response values opened: 0;
- v0.11 intake authorized: no;
- pilot authorized: no;
- confirmatory response authorized: no;
- fresh-confirmatory denominator: 0.
