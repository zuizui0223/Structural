# BELongDead author study overview of logs (BExIS 20406/tag2): source-only admission gate (2026-11-18)

## Question and status before new source access

The current Structural forest macro programme has (a) Finnish 142 author-site locally measured total deadwood -> Host_tree guild heldout gain H² +0.00024237 (9 cells, conditional signed-cell p=.015), (b) Chiu/Vogel six-parent-plot offered tree-host identity -> detected beetle species mixture gain H² +0.019699892, 6/6 plots, exact p=.03125; and (c) **no independently validated between-region host-wood × feeding-guild transfer**. Original 2010–17 BELongDead experimental BExIS31123 has 30 plots in three regions, 379 logs and 13 deliberately offered wood types; 31124 has 15 unexpected TrapID method tuples whose exact log×host×year parents occur in 31123 but their IDs are not reconciled. Original BExIS24546 ambient 2012 wood shares 30 plots but m³ and m³/ha strata cannot be pooled.

Prior original author BExIS13930 (alias numbers), 16846 (changes in log naming), 16427 (subplot naming), 16390 (2009/10 instrumentation) were inspected through source dictionaries only; original 16846 and 16390 published tagged CSV headers verified, but neither establishes trap-deployment/zero-capture opportunities. Do not turn a log alias into a trap alias.

## New independent original-author method source, fixed before any row access

**Exactly BExIS dataset 20406, published tag 2**: *BELongDead - 10 - Study overview logs*, Weisser (2018), original project listing https://www.biodiversity-exploratories.de/en/projects/arthropods-i-land-use-above-ground-arthropod-diversity-and-arthropod-affected-processes/ . This is NOT a new study, new region or biological cohort; it may document original log identity or sampling status relevant to the existing 30-plot field experiment. Its content is **unknown before this gate**; the catalogue title is not evidence that it contains effort.

One planned immutable method-only source intake:

1. GET **only** official publisher /api/dataset/20406 and /api/metadata/20406?tag=2.0 (single read-only request each, no redirects, authenticated workarounds or mirrors). Require readable JSON, source dataset identity and recognizable public CC BY 4.0 or CC0 rights. Save SHA256, byte length, status and rights-verification boolean. Do not export any free-text original metadata, site labels or biological data.
2. If and only if rights are verified and both endpoints accessible, GET official /api/DataStatistic/20406 once. Read ONLY the published author `VariableName, VariableDescription, Unit, DataTypeName` fields in memory to generate bounded **predeclared lexical candidate-family counts**: log/stem ID, plot/subplot, alias/renaming, trap/collector/installation, period/date/year, explicit sampled-zero/catch effort and wood resource. Never traverse/export `uniqueValues`, species/capture counts, original sample labels, source numeric min/max, raw codebook text or individual rows.
3. After rights pass, GET **exact tagged** /api/data/20406/tag/2 once. Stream only for SHA256 and byte length, decode and parse ONLY the first original CSV header line; all remaining bytes remain opaque. Stop for redirect, HTTP 401/403/404, malformed/HTML/non-CSV file or >20MiB. Do not export raw original header tokens, method rows or specimen/wood measurements. Record first-header field count and lexical method-family counts, with no assumed count.
4. Compare only dictionary field count versus exact tagged header count if both were obtained; a difference is a VERSION/SCHEMA HOLD, not license to use a later version or a different source. A match is schema support, not proof of exact same field definitions.
5. No biological response calculation under any outcome. No old BExIS31123/31124 or 24546 source access in this gate, no joining to their 15 TrapID keys, no species/guild/abundance, no modification of frozen original Finland, Chiu, Piccini, Burner, PREDICTS, NEON, BALA or GEB scoring. eBird and TinyFish remain unused.

Possible statuses: `SOURCE_ACCESS_RIGHTS_STOP`, `SOURCE_DICTIONARY_OR_ORIGINAL_TAG_STOP`, `SOURCE_TAGGED_HEADER_DICTIONARY_MISMATCH`, `SOURCE_AUTHOR_METHOD_SCHEMA_CANDIDATE_ONLY`, `SOURCE_NO_EXPLICIT_METHOD_CANDIDATE`. A completed GitHub Actions job can legitimately report STOP; PASS is only for execution/schema, not ecological effect.

## What would justify the following step

To verify the 15 original TrapID mismatches or a true per-log/year opportunity frame, a **separate** prospective original-author-method-only identifier protocol is needed, explicitly identifying source columns and their ecological meanings. No fuzzy string transformations, row alignment, casefold rescue, substituting standard forest trap dates 17016 or deriving true zeros from absence of a species row. Even a method-only crosswalk does not itself demonstrate a new country-level feeding-guild effect.

Prior interpretive ceiling: previous host preference, successional and forest management effects were published before Structural; a future publishable claim requires original resource-identity information to add independent, spatially blocked or region-heldout predictive value for a predefined guild response, not rediscover host preference.
