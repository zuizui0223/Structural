# Georgia 2023 40 forest sites: independent original data accessed, author site↔beetle-matrix crosswalk remains UNVERIFIED (2026-11-17)

## Result and final scientific decision

**The Georgia original public Zenodo source is authentically available and its two CSV/README files passed publisher MD5 checks. The ecological source-to-response join nevertheless remains scientifically unverified.** Original site-side environmental data: 40 original source rows, 40 unique author-labelled site IDs. Original beetle matrix: 58 header columns containing "species" and "group" named headers, but **0/40** original site IDs match any of those 58 column headers, under exact OR casefold comparison.

To diagnose whether a simple source import convention could explain the mismatch without opening biological values, an independently precommitted one-shot source-only diagnostic [protocol](FOREST_BEETLE_TRAYLOR_US40_SOURCE_ID_DIAGNOSTIC_PRESPEC_20261117.md) was executed in GitHub Actions [#44081646324](https://github.com/zuizui0223/Structural/actions/runs/44081646324) **SUCCESS** with known-truth tests, original publisher MD5 and no biodiversity/environmental numerical values opened. Artifact #**14328200632**, ZIP SHA256 **b9aab01b249adb287658c5a28a273c2f002422f1c9202a7f262f5a84322f7564**.

### Verified anonymous source-only identity diagnostic

| Fixed original-source test | Actual result |
| --- | ---: |
| Original forest environment unique site IDs | **40** |
| Forest IDs with digits only | **40** |
| Original beetle matrix header columns | **58** |
| Header columns with alphanumeric-mixed lexical pattern | **40** |
| Header columns with letters-only pattern | **2** |
| Header columns with punctuation/other lexical pattern | **16** |
| Exact original site-to-header matches | **0 / 40** |
| Case-insensitive matches | **0 / 40** |
| Remove punctuation + casefold | **0 / 40** |
| Simple R make.names diagnostic | **0 / 40** |
| Remove single X prefix only on digit-leading candidate headers | **0 / 40** |
| Original author README lines searched | **115** |
| Source README lines with explicit site-column identity / numeric mapping rule | **0 found under frozen rules** |
| New beetle species, guild, abundance or forest numerical source rows read/scored | **0** |

The 40 mixed alphanumeric headings **cannot** be equated to the 40 numeric author forest site IDs on column order, shape coincidence or an invented transformation. Lexical mismatches do not prove the two source files have unrelated sites: original author coding rules may exist elsewhere or require original source-specific data metadata. The README pattern scan only establishes that the *predeclared narrow rules* did not find an author mapping, not that no valid mapping exists in the world.

### Provenance and closed source selection

- Original [Zenodo 10.5281/zenodo.8246615](https://doi.org/10.5281/zenodo.8246615) record and three original published MD5 verified in original [CI #44080068092](https://github.com/zuizui0223/Structural/actions/runs/44080068092), including original author README, `site_forest_variables.csv` (96 columns) and `species_list_abundance_per_site_functional_group.csv` (58 columns).
- Exact original 40 environmental site rows vs original beetle header: [CI #44080643214](https://github.com/zuizui0223/Structural/actions/runs/44080643214), **0 exact / 0 casefold**, no source response data opened.
- One source-only lexical/README diagnostic: [CI #44081646324](https://github.com/zuizui0223/Structural/actions/runs/44081646324), five predeclared lexical checks all **0**, no original biological data opened.
- First old/new Zenodo schema discrepancy in #44079562477 was a source code parser error; corrected, independently verified, no ecological claim. Source methods were not altered after a biological outcome.

**Scientific status: SOURCE_SITE_ID_CROSSWALK_UNVERIFIED_NO_GUILD_RESPONSE.** Do not permit a row-order join, 40-column default reshape, ecology-regression coefficient, site-level uncertainty or new positive/negative inference. Only an original author-issued crosswalk or otherwise unambiguously publisher-documented rule can reopen this independent source. The Georgia study is a geographical independent field lineage from the German Piccini source but presently **not** an independently completed biological validation.

The 2023 study already reports forest-age biodiversity patterns; later 2024 morphology analysis comes from the same field lineage and is prior art. The previously sealed original Piccini 8-site floor one-pass (11.7% descriptive error gain but exact p=.09375 non-support), Finland VD10 +.00024237, Burner trait shuffle D+.091059, PREDICTS, Thai, NEON, BALA and GEB mammal scientific HOLD remain unchanged. No eBird/TinyFish. PR #469 remains Draft, not merged into main.

## Next admissible external biological evidence

Seek **another independently documented original forest survey** where the beetle species/feeding-guild values and local measured hostwood/tree environment explicitly share a verified site×year×method key and observed trap effort. Use one source-only eligibility audit before selecting a predictive ecological endpoint; no post-hoc favorable outcomes or re-use of the Georgia blocked site matrix.
