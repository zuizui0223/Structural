# Carpathian original author file-method/schema gate, frozen after metadata-only admission (2026-11-18)

## Trigger and evidence boundary

Previously prespecified metadata-only [Actions #44234217086](https://github.com/zuizui0223/Structural/actions/runs/44234217086) returned original public Zenodo record 22142713, publisher JSON 10,323 bytes SHA256 `c1ec934e700ebfa150d32d71ee23373bff28042c63d8eb55c2fbb56334b6ce30`, record published and **CC BY 4.0**. **14 official author files** (381,190 bytes combined) were listed but **ZERO original data files opened**. This prior metadata source was HOLD only because file names `Beech.csv`, `Spruce.csv`, `Beech_Spruce.csv` do not lexically identify a plot/environment table; biological filenames `B_SR_BEETLES.csv`, `S_SR_BEETLES.csv` were identified. No new ecological result.

Scientific question remains exactly: can physical-site measured forest deadwood resources add *heldout predictive information* for **independently defined feeding guild composition** beyond forest, elevation, canopy, landscape and stand/range? Gloor et al. 2026 already reported richness, red-list and db-RDA composition associations in these same plots. Only a distinct, prospectively fixed method + prediction may be new; seeing original Rscript does not authorize p-hacking the same response.

## Exactly seven original filenames, fixed MD5 / file length *before* new access

| File | Publisher bytes | Publisher MD5 | Source-role *candidate* |
| --- | ---: | --- | --- |
| `B_SR_BEETLES.csv` | 34504 | `711755433cd6ec452ae1971f20b3c281` | Beech beetle response matrix, unproven |
| `S_SR_BEETLES.csv` | 21701 | `9320f3803ebfb9002cdcea42c14dd2f1` | Spruce beetle response matrix, unproven |
| `Beech.csv` | 7936 | `78ce4d753000f8945c3984bb2bba8b06` | Environmental plot metadata candidate |
| `Spruce.csv` | 7584 | `0fa184c63bbb227f04097e15083bc9ec` | Environmental plot metadata candidate |
| `Beech_Spruce.csv` | 15231 | `223239b47d513aebd703777483a76277` | Combined plot metadata candidate |
| `README.txt` | 8985 | `0d707ef099271af8470759bf877f1b51` | Original publisher methods/column descriptions |
| `Rscript.R` | 98489 | `25836117f89d5c96f6e5c54c33ba0c94` | Original author code, read only as program TEXT, NEVER executed |

The original article and archive are Gloor et al. 2026, JAE DOI 10.1111/1365-2664.70594, Zenodo DOI 10.5281/zenodo.22142713.

## EXACT source-only execution contract

1. GET Zenodo record 22142713 JSON only from official publisher once and verify entire metadata SHA256 above **before** using its file download links; record exact keys/bytes/md5 for all seven files above. Avoid redirects to other storage hosts, mirrors, credentials, retries or alternative sources; HTTP stop is scientific SOURCE HOLD, not ecological null.
2. GET each of the exactly seven original file contents **at most once** by original record's `links.content` URL, with strict Zenodo host and record-ID path and size+MD5 check. Original file bytes stay runner-private. No other file, especially S_SR/B_SR birds/fungi/lichens or r2 result CSV, may be fetched. Preserve checksum receipts and source role.
3. For each **five CSV files**, decode **only its FIRST physical header line** in UTF-8 and parse with standard CSV; remaining bytes may be counted by newline for physical original row-count *without decoding or accessing columns*, but **NO data row**, including beetle species labels, incidence/abundance, spatial coordinates or forest measurements, may be opened. Output original FIRST-LINE field names only if they satisfy a strict alphanumeric/underscore/dot/hyphen grammar and are **not** species/taxon labels. If matrix-wide headers appear to be species, **do not emit any literal names**, only field count and whitelisted generic key/measurement-family counts. Do not export beetle column names even if they look innocuous.
4. Parse **README.txt** and **Rscript.R** as exact MD5-verified published source METHOD TEXT ONLY, never execute. Return ONLY fixed patterns/counts: evidence of per-plot ID, stand/range ID, habitat measured variables, feeding-guild/functional trait definitions, trap effort/zero-capture, name of each of the five fixed CSVs and whether original R uses join-by-ID vs position-binding. No raw prose, individual IDs, taxon labels, transformed response values or analysis coefficients in logs/reports.
5. Required biological schema eligibility for a later completely separate response protocol: unique physical plot key on each candidate species and environment table, unambiguous join without row index, one original stand/range blocking field, original land/wood measured covariate with units, valid original beetle species/feeding guild ontology with missingness rules and source effort/repeated dates. Meeting only row number 60 or 56 is NOT site-key proof. If missing, `SOURCE_SPECIES_ENVIRONMENT_SITEKEY_OR_GUILD_UNVERIFIED`. A successful source check does NOT authorize any guild-response opening.
6. Do not reopen original sealed Finland/Chiu/Piccini/PREDICTS/NEON/BALA/GEB/BELongDead responses; no new biodiversity effect. No eBird/TinyFish, main merge, author communication or independent-replication claim.

## Publication prior art to prevent misleading novelty

Gloor et al. already fit per-forest-type beetle richness/red-list GLMMs and partial Sørensen db-RDA conditional on forest stand, with eight predictors including deadwood volume, canopy and elevation. Kriegel et al. 2023 DOI 10.5061/dryad.brv15dvch already found differential wood-substrate vs ambient-energy associations among trophic beetle guilds across Europe. Therefore neither “saproxylic beetles respond to deadwood” nor “guilds differ in substrate vs ambient effects” is new. The only prospective differentiation is *out-of-range, source-qualified* prediction of guild composition beyond a declared strong reference (not a causal effect of wood). This paper is one national system with nine original mountain ranges; no causal between-beech/spruce interpretation.


## Response-unopened publisher link-adapter correction (2026-11-18)

Original source-only Actions #44234924543 **SUCCESS as a source STOP**: `SOURCE_ZENODO_ORIGINAL_CONTENT_LINK_ABSENT`. No original author file was requested or opened, so no biological outcome has been exposed. This is **not** a published-record or scientific eligibility failure. The source REST manifest exposes the publisher's `files[].links.self` download relation rather than the code-assumed `links.content`. The [Zenodo official REST files documentation](https://developers.zenodo.org/) explicitly documents `links.self` as an original download URL (under `/api/files/{bucket-id}/{original-filename}`).

**Prospectively frozen source-only technical repair**: accept *only* `links.content` or, if absent, `links.self` directly supplied in the SAME SHA-frozen publisher record 22142713. The exact original record metadata SHA, seven original file names, per-file MD5+byte-size locks, host, and no-row/no-code-execution restrictions are unchanged. Permit a source-issued `https://zenodo.org/api/files/{UUID}/{frozen filename}` URL after checking the two path segments and exact allowlisted filename; never construct a URL from an untrusted filename, change host, follow redirects, retry blocked download paths or substitute other records. Abort on URL- or digest-drift as source transport STOP. No hypothesis, feature, trait or biological scoring modification is authorized by this adapter repair.


## Response-unopened HTTP 406 content-negotiation correction (2026-11-18)

Actions [#44235254788](https://github.com/zuizui0223/Structural/actions/runs/44235254788) passed synthetic source checks and accepted the Zenodo publisher `links.self` URL after the previous adapter correction, then **STOPPED at HTTP 406** on the first original file GET; no file content/biological record was delivered or parsed. HTTP 406 is specifically an HTTP content-negotiation problem with the first-run `Accept: application/octet-stream,text/plain;q=0.6` header, NOT biological data absence, not original publisher license failure. A single **source-transport-only** repair switches the file-GET Accept to `*/*` while keeping the exact publisher-supplied URL, source record SHA, file name/length/MD5 locks, strict no-redirect policy, source read scope and source-value redaction unchanged. No source or outcome candidate is added, renamed or reselected. If this fails again, diagnose the serving endpoint rather than trying extra URLs or content variants.
