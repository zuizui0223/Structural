# Boreal secure Stage-A workflow v0.73

## Why this revision exists

The public Dryad landing page exposes file names and documentation, but direct
file download returns 403 without authenticated API access. v0.72 already froze
the exact authenticated transport. v0.73 makes that route executable without
putting credentials or raw mixed files into repository artifacts.

## Credential strategy

Preferred GitHub Secrets:

- `DRYAD_CLIENT_ID`
- `DRYAD_CLIENT_SECRET`

The workflow exchanges those credentials for a short-lived bearer token at run
time. The token is written only to the runner's `GITHUB_ENV` file. The token
receipt contains only mode and expiry metadata.

A still-valid `DRYAD_TOKEN` secret is accepted only as a fallback.

## Manual-only execution

The workflow has only `workflow_dispatch`. It does not run on push, pull
request, or schedule. Merging v0.73 therefore cannot spend credentials or open
file headers by itself.

Repository permissions are read-only and checkout does not persist a GitHub
credential.

## Evidence surface

The runner performs:

1. short-lived token preparation;
2. v0.72 opaque exact-byte transport;
3. v0.71 header-only audit;
4. deletion of the raw mixed CSV directory;
5. upload of three JSON files only:
   - `token_receipt.json`
   - `transport_receipt.json`
   - `header_audit.json`

Raw CSV files are never uploaded as workflow artifacts.

## Scientific boundary

A successful v0.73 run still contributes **zero empirical evidence**. It may
reveal header names, because header classification is the explicitly frozen
Stage-A goal, but it does not authorize any safe row value, protected response
value, model fit, pilot response, confirmatory response, or v0.11 intake.

The next irreversible action after a successful run is a separate repository
revision that freezes the exact header SHA/manifests. Only after that revision
is merged may the safe coordinate/habitat projection be executed.
