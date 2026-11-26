# Weiss2016 PLOS R2 URL structural fail — header-only predicate diagnosis

Previous PLOS original author-supplement tests: CI #44240546963 = PLOS redirect URL outside original endpoint allowlist, no file read; CI #44240803381 = publisher HTTP302 verified, Cloudflare R2 host and issuer Location SHA256 `2595cce0ff5b38d31337d871b664fe7bb3878ab55c1ed714eb7407845cbeb5fc`, no file read; CI #44241120553 = **source-only STOP** `SOURCE_ORIGINAL_ISSUED_R2_HOST_OR_URL_NOT_ALLOWED` after confirming Location SHA, but **before issuing any object-download request**.

This is not a fourth blind fetch: **the only task now is to diagnose which URL predicate stopped the pinned PLOS-issued original URL**. The exact original Weiss S1 DOI 10.1371/journal.pone.0149506.s001 and 512 species / six published guild codes remain author-reported, not observed original source data. Gloor Carpathian 116×species outcomes remain sealed. The independent Franzén original Dryad table was HTTP401 and is NOT retried.

## Exactly one publisher-header-only diagnostic

1. One GET, NoRedirect, original PLOS URL `https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0149506.s001&type=supplementary`, require HTTP302 and Location SHA256 **exact** prior digest. No download of Location, no body read.
2. Parse the Location entirely in memory and export only boolean predicates: scheme=https, exact known publisher-issued R2 hostname, username present, password present, port present, query present, fragment present, path absolute, path nonempty, path unquoted-dotdot, URI nonempty, and URL exact SHA checked. The raw Location string, URL path, query names/values, tokens, and any contents must NOT be printed, returned or persisted.
3. This diagnostic does not grant URL policy relaxation. A SOURCE STOP/DRIFT or contradictory values will end this source route rather than prompting another download. A bounded structurally valid **publisher-issued** URI may be considered for a different prospectively precommitted file gate, never reused as an authentication bypass.
4. Absolutely no DOC bytes, guild labels, Gloor species names/captures, old forest/BALA/GEB outcomes, eBird, TinyFish, or new ecological scores. Draft PR #469 only, main unchanged.
