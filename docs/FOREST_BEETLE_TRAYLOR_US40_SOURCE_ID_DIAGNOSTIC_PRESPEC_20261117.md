# Georgia 40 forest sites × beetle original 58-column matrix: source ID diagnostic ONLY (2026-11-17)

[Original source-only exact-match GitHub Actions #44080643214](https://github.com/zuizui0223/Structural/actions/runs/44080643214) completed: the forest environment CSV has **40 unique author source site IDs** across 40 rows; species/functional-group CSV has **58 fields**, recognized "species" and "group" headers, but **zero exact, zero casefold matches** between site values and species CSV header labels. No beetle original rows or environmental values inspected, ecological testing not authorized. Do not relabel species columns by position or 40-expected assumption.

The next and only narrow source-only diagnostic aims to distinguish:
(i) source printed site codes differed only because of a documented **standard import formatting** (e.g., R column name prefixing or punctuation), versus
(ii) genuinely absent original site crosswalk,
without author-blind fuzzy matching or field effects.

1. Fetch original three Zenodo 8246615 files by their already published MD5, no alternate route.
2. Read only one original author site ID field per 40 environment rows, the full **beetle CSV HEADER only**, and original author README metadata text. Keep all site/source labels and README body in runner-private memory.
3. For exact source ID strings and header candidate strings calculate only anonymized match counts for **predeclared global transformations**, separately: casefold; alphanumeric canonicalization removing punctuation; base R `make.names` style initial `X` for digit-leading IDs; a source-native single fixed "site" prefix or suffix *not* allowed without explicit README author rule. Never choose a successful mapping from dozens of transformations or output individual candidate matches.
4. Report safe anonymized category counts: number of site source labels that are digit-only, alphabetic-only and mixed; number of normalized source header fields by the same broad category; counts of collision-free matched keys under predeclared lexical operators; stop any conversion without author codebook validation. Report author README **method-only** text indicators or at most 8 short sanitized excerpts of documentation lines containing site/column/functional group definitions (mask literal digits and potential site codes), never raw authors' field samples or species values.
5. If no unique author source key crosswalk is established, status `SOURCE_SITE_ID_CROSSWALK_UNVERIFIED_NO_GUILD_RESPONSE`. A lexical match is a diagnostic, NOT author-confirmed original field identity or authorization to score 40 site guild outcomes.
6. No prior original biological scorers reopened; no eBird/TinyFish; PR #469 Draft/unmerged. Cross-study/cross-country prediction still requires independent guild ontology and monitoring effort alignment, not only 40 IDs.

This is not a post-result rescue after a failed ecological test: no original Georgia species/guild effect has ever been computed.
