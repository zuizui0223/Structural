# Boreal exact authenticated transport v0.72

Dryad currently requires an authenticated API session for file downloads. v0.72
predeclares the only transport route that Structural will accept for the boreal
mixed files.

## Scope

The downloader has no URL argument and no file-ID argument. It can request only:

- file 4569034, `alpha_diversity_ALL_islands.csv`;
- file 4569033, `RDA_environmental_variables.csv`.

Their byte sizes and SHA-256 digests are inherited from the metadata-only v0.65
freeze and the v0.71 header contract.

## Credential handling

`DRYAD_TOKEN` is read only from the process environment.

The script never accepts the token on the command line and never writes it into
a receipt. On a redirect from Dryad to a different origin, the custom redirect
handler removes the `Authorization` header before following the redirect.

This matters because the download route can redirect to object storage and the
bearer token must not be forwarded to that host.

## What a successful transport means

The complete mixed files necessarily contain both pre-response and protected
columns. v0.72 therefore does **not** pretend that response bytes do not exist.

Instead, it treats the downloaded payload as opaque bytes:

1. stream to a temporary file;
2. compute byte count and SHA-256 without CSV decoding;
3. compare both to the frozen target;
4. delete any mismatch;
5. atomically rename only an exact match.

A successful receipt still records:

- header decoded: **false**;
- data rows semantically opened: **0**;
- biological response values opened: **false**;
- fresh evidence: **false**;
- safe-row projection: **unauthorized**;
- v0.11: **unauthorized**.

## Next gate

After exact transport, run the v0.71 header-only audit. Even a successful header
audit does not permit row projection in the same run: its header SHA/manifests
must first be committed in a separate revision.
