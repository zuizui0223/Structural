# Weiss 2016 original PLOS S1 supplementary publisher redirect provenance (2026-11-18)

## Frozen original/source-only reason

Source-only CI [#44240546963](https://github.com/zuizui0223/Structural/actions/runs/44240546963) correctly executed synthetic no-outcome tests, then stopped **before any supplement bytes** with `SOURCE_NOT_ORIGINAL_PLOS_ARTICLE_SUPPLEMENT_ENDPOINT`: the PLOS supplementary URL returned a redirect to a URL not allowed by our too-restrictive same-endpoint-only policy. This is a **redirect-source verification STOP**, NOT HTTP401 and not absence of published guilds. Original Gloor 2026 beetle species/abundance data remain sealed. The separate Franzén 2026 Dryad 425-species original file remains HTTP401 SOURCE ACCESS STOP and will NOT be retried or replaced by a mirror.

PLOS 2016 DOI 10.1371/journal.pone.0149506 (CC BY), original author S1 Table DOI 10.1371/journal.pone.0149506.s001, author-reported 512 beetle species / six original trophic labels m,n,p,s,x,z. These have not been independently extracted from source DOC.

## One exact redirect-HEADER-only diagnostic before any changed fetch policy

1. Issue **ONE anonymous GET without following redirects**, exactly to publisher URL `https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0149506.s001&type=supplementary`, with 30-second timeout. Do not read response BODY even if HTTP200. Read only HTTP status, media type and Location header in memory.
2. On HTTP 3xx, export only **the destination host name, HTTPS yes/no, URL path category (e.g. /plosone/article/file, /resource, /articles), and query PARAMETER NAMES**, not the whole Location URL nor any token/query values. SHA256 of the original Location header may be recorded to detect drift, not a credential. For host not within recognized public PLOS publisher/PMC, mark unverified; no redirects are followed.
3. If HTTP 200, classify as source-direct-PLOS; do not read the file content. If HTTP401/403, mark SOURCE_ACCESS_STOP and do not request alternate URLs. Any errors are source/protocol STOP, never ecological null.
4. No original species/guild values, Gloor species columns, old BL/BALA/GEB results, or model effect calculations. eBird/TinyFish unused; Draft PR #469 only.

This test may justify a *new and separately frozen* official publisher-delivery allowlist, but it is NOT itself permission to follow a third-party storage host or inspect biological outcomes.
