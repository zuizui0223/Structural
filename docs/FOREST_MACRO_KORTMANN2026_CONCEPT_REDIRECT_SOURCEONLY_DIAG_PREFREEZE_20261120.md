# Kortmann 2026: exact original Zenodo 17775804 HTTP302 canonical-record diagnostic — prefreeze (2026-11-20)

## Historical source outcome (immutable)

The original manuscript (Kortmann et al. 2026, Biological Conservation 313:111647, DOI 10.1016/j.biocon.2025.111647) publicly cites **Zenodo DOI 10.5281/zenodo.17775804** for data/code. The predeclared source-metadata-only original run [#44744082425](https://github.com/zuizui0223/Structural/actions/runs/44744082425) issued a no-redirect GET to the exact `https://zenodo.org/api/records/17775804`, and correctly recorded **`SOURCE_KORTMANN2026_PUBLISHER_STOP_SOURCE_PUBLISHER_HTTP_302`**. No source data members, methods, site keys, specimen/OTU counts or biological outcome values opened. Leave that source STOP unchanged; do not retroactively mark it PASS.

Official Zenodo documentation describes that a **concept record can HTTP302 redirect to a specific record version**. The source's redirection therefore needs a response-blind diagnosis before deciding whether any canonical version can be admitted. It does NOT prove the target is a permissible version or a scientifically new independent forest study.

## This ONE response-blind diagnostic, frozen before action

Request EXACTLY the already-published `https://zenodo.org/api/records/17775804` URL once using GET with redirects disabled. **Do not follow any redirect**. Read only HTTP status and the `Location` response header from an HTTP302; no response body, no destination GET, no filename/file roster, no original data, no OTU/taxon, no source scientific model. Fail closed on other statuses and malformed/external redirect.

Allowed `Location` syntax:
- either relative `/api/records/<decimal positive ID>` or absolute `https://zenodo.org/api/records/<decimal positive ID>`;
- no credentials, query, fragment, port, external hostname, path parameters or trailing suffix;
- target ID must be a distinct positive integer. Output **only** source status, exact original record ID, target record ID, same-zenodo publisher flag and no-destination-read flag.

This diagnostic only provides a candidate canonical record ID, not the target's real DOI/version, publication status, file access/license, physical field independence or cross-study eligibility. If target ID identified, a **separate future precommitted** publisher-metadata audit can require target version-specific DOI, publisher status/license, file roster/digests and original paper linkage *before* any source member GET. No original biological rows from either original or target are authorized by this diagnostic.

Do not replace the fixed 17775804 DOI with an arbitrary new 'latest', concept DOI, search result or different author repository. No alternate host or URL rescue. Source technical 302 stays recorded as historical STOP. No BETA-FOR99, BETA-FOR234, Finland, Carpathian, Sweden, PREDICTS, BALA or island field response rescoring; PR #469 stays draft and main unchanged. No eBird/TinyFish.

**Science ceiling:** even if a target authenticates, Kortmann's undisturbed–disturbed–cleared triplets cannot be silently treated as BETA-FOR's matched canopy configuration × wood-type factorial with multiple within-state spatial replicates. Source plot/forest/region/method/coverage and provider overlap must be verified independently. No cross-biome replication is claimed.
