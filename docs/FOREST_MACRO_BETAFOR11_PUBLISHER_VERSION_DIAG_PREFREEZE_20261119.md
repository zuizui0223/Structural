# BETA-FOR11 official publisher version-value diagnostic v2 — source-only prefreeze 2026-11-19

## Immutable historical v1 STOP, not a model rescue

The separate original publisher-only [GitHub Actions run #44545260657](https://github.com/zuizui0223/Structural/actions/runs/44545260657) executed successfully **as a recorded scientific STOP**: `SOURCE_METADATA_HOLD_PUBLISHER_VERSION_NOT_V1`. It read official `https://zenodo.org/api/records/15371332` metadata ONLY; 0 original files downloaded, 0 source biological rows opened, and no ecological effect fitted. Its v1 exact `metadata.version == "v1"` gate remains permanently unchanged. Public Zenodo [record page](https://zenodo.org/records/15371332) labels **Version v1** (published May 9 2025), but the REST field did not meet that exact literal requirement.

## Precommitted independent source diagnostic

Perform exactly ONE original publisher record GET, from the exact fixed URL, with the original `get_official_metadata_only()` URL/response/size protections. Extract and export ONLY these controlled scalar fields:
- `id`, `doi`, `status`, public `metadata.version` presence and its exact raw string (only if <=40 ASCII `[A-Za-z0-9_.-]`), `metadata.license.id`, and *non-sensitive* `versions` object key NAMES only (not arbitrary URLs/content);
- for six fixed original filenames, whether each publisher `checksum` exactly equals its **previously frozen original MD5** and whether source size is a positive safe integer, without exporting any unexpected filename, file link, file content or row;
- exact expected record `15371332`, versioned DOI `10.5281/zenodo.15371332`, official original public published status and CC BY-SA 4.0 license.

No query for any original six file member, no sample/header/OTU values, source code or ecological model. This new diagnostic must NOT classify the source as admitted simply because an unexplained version string is present.

If the returned version is an alternative public spelling (for example 1, 1.0 or missing), it remains *diagnostic* until a separately frozen new v2 admission explicitly reconciles official versioned DOI + publisher page v1 + exact six original checksums. Do not mutate the v1 historical report or bypass an actual publisher file change. No preexisting biological heldout is reopened.

The diagnostic is a **source-access/provenance operation**, not a biological finding. Prior BALA, PREDICTS, Finland, Carpathian, Sweden, NEON and island scores remain immutable; PR #469 remains Draft and main unchanged.
