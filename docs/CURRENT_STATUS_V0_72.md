# Structural current status v0.72

## Fresh denominator

Still zero. No biological response value has been opened and v0.11 remains
unauthorized.

## What v0.72 closes

The boreal route no longer lacks a safe transport implementation.

Dryad file downloads now require authenticated access. v0.72 therefore freezes
an exact downloader that can request only the two already pinned mixed files,
reads the bearer token only from `DRYAD_TOKEN`, strips Authorization on
cross-origin redirects, and accepts output only when both byte size and SHA-256
match the pre-response metadata freeze.

The download stage treats the files as opaque bytes. It decodes neither header
nor data rows.

## Remaining sequence

1. execute exact authenticated transport;
2. run v0.71 header-only audit;
3. commit header SHA/manifests in a separate revision;
4. project only the frozen safe coordinate/habitat columns;
5. validate 42-island geometry and complete habitat support;
6. only then consider v0.11.

The scientific denominator remains unchanged until those steps are completed.
