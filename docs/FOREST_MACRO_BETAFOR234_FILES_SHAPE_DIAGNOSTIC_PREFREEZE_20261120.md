# BETA-FOR234 original publisher file-descriptor SHAPE diagnostic — prespec 2026-11-20

## Immutable initial attempt

The source-only first-visit [Actions #44743174521](https://github.com/zuizui0223/Structural/actions/runs/44743174521) successfully captured `BETAFOR234_SOURCE_METADATA_STOP_SOURCE_PUBLISHER_FILE_DESCRIPTORS_INVALID_COUNT`. The frozen v1 parser requires a nonempty, <=100-list of publisher `files` items. This was a **publisher metadata source STOP, NOT evidence of ecological null or a passing original source index**. Original member downloads=0, sampling/patch IDs=0, organism/OTU rows=0, model fits=0. Do not change the v1 parser/receipt or infer the reason for the STOP.

## New separated diagnostic, not eligibility relaxation

The only allowed original access is one official `https://zenodo.org/api/records/18467123` request using the existing response-cap/no-redirect `published_record_GET_only` helper from frozen v1. From the official JSON, without downloading any file member, inspect and summarize ONLY:
- exact `id=18467123`, versioned DOI `10.5281/zenodo.18467123`, `status=published`, license `cc-by-4.0` (all must match or diagnostic STOP);
- whether `files` is absent, null, a list, or another type; if list, report ONLY its integer length, and counts of entries that include source-reported descriptor `key`, `checksum`, `size` (NO name, checksum or location values);
- whether record JSON has a published top-level `access` object and publisher `links` object; report only safe predeclared top-level presence booleans, never fetch links.
- digest of the exact publisher REST JSON as a provenance receipt, not a content source hash, and a flag `not_original_file_MD5_verified`.

Never print unexpected filename, sample/patch/region IDs, personal metadata, location, URLs (other than the exact record ID), original file contents, OTU source values or inferred ecological effects. Never follow a link or vary record ID/version/host after a failure. This diagnostic alone **never authorizes first-header, plot treatment or species response access**. All outcome locks stay closed.

## Interpretation rule

- If `files` is not a nonempty list, document `SOURCE_PUBLISHER_NO_PUBLIC_FILE_DESCRIPTOR` with detailed type/count. That is a **real source-access ceiling** for this official record, NOT reason to fabricate a 234 response denominator.
- If list length >100 or descriptors use unrecognized keys, document exact **source schema incompatibility**; a separately precommitted source validation contract is required, without reading biological members.
- Even a valid list does not itself prove 234 plot observations, ID/treatment crosswalk, control pairing, original sample effort/attrition, coverage or suitability for alpha/beta. Those are all separate gates.

One high-priority main goal remains independent `alpha` vs within-forest `beta` contrast under matched treatment/control with six original geographic blocks; do not reopen consumed 99-patch OTU primary, change its p=.0625, or treat shared BETA-FOR samples as independent countries. PR #469 remains draft, main unchanged.
