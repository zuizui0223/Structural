# Structural current status v0.71

## Fresh evidence remains zero

- active fresh systems: **0**
- confirmatory-eligible systems: **0**
- live confirmatory queue entries: **0**

No biological response has been opened.

## Boreal route

v0.70 established that six lake identities cannot replace the required spatial
geometry. v0.71 now resolves the **firewall implementation** needed to recover
that geometry safely when exact bytes become available.

The two mixed files already have frozen Dryad identities, byte sizes and SHA-256
hashes. The repository also already had a safe-column projection firewall.

The missing bridge was a pre-row header freeze.

v0.71 adds it: exact files are hashed as opaque bytes and only the first physical
CSV record is decoded. The result can freeze a header SHA and candidate manifest,
but row projection remains unauthorized until a separate revision commits those
manifests.

## Current blockers

1. transport exact SHA-matching bytes for the alpha mixed file and RDA mixed file;
2. run header-only audit;
3. commit header manifests;
4. only then project safe coordinates and habitat;
5. validate 42-island geometry and complete safe habitat before v0.11.

Thus the blocker is now sharply localized: **exact-byte transport → header
freeze**, not uncertainty about how to separate predictors from response.
