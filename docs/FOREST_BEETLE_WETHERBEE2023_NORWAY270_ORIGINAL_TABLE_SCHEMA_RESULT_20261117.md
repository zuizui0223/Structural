# Norway Wetherbee 2023 boreal beetles: official 3-table original schema and cohort lineage remain unjoined (2026-11-17)

## Verified publisher source, not an ecological positive

Official [Zenodo 10.5281/zenodo.8272489](https://doi.org/10.5281/zenodo.8272489) original archive and its 8 exact original files were verified in [GitHub Actions #44082232916](https://github.com/zuizui0223/Structural/actions/runs/44082232916) SUCCESS. Article [Wetherbee et al. 2023 DOI 10.1002/ece3.10739](https://doi.org/10.1002/ece3.10739) reports **270 forest sampling sites from 8 historical projects (1997–2007)**, 339 obligate saproxylic beetle species, differences in forest naturalness, relative predatory guild and morphological indicators. These are published PRIOR ART. Overlap with previous original Burner 2022 Norway 468-site field collections is still **UNRESOLVED**, not independently replicated biology.

The three original candidate species/trait/site-information files were **publisher MD5 verified** in [corrected Actions #44082986667](https://github.com/zuizui0223/Structural/actions/runs/44082986667) **SUCCESS**. Original CSV source bytes passed through private runner memory for hashing; **only first HEADER line of each source file was parsed**, not a single site/species/trait numerical row. Aggregate-only artifact ID **14328635332**, SHA256 **93dcaf345a0fd4bddbe19fa1653085b2179bf1af66cc32dd382299538f88fa49**.

| Original author file (unchanged) | Original MD5 and bytes | Schema-only actual result |
| --- | --- | --- |
| `GBIFnormalized_SpcSite_matrix_FD_unique.csv` | MD5 `1cc6d3599dccd80b0889b55b5d571eda`; **2,759,229 bytes** | **1,090 CSV header fields**, comma; no *predefined generic site/project/guild field name* matched, so likely a wide matrix, but its orientation and actual population **not proven** |
| `GBIFnormalized_Trait_RAW_df.csv` | MD5 `da5aa42586fe6994deb039565a782f8a`; **485,427 bytes** | **64 fields**: generic `species`, `genus`, `family`; `winglength`, `bodyroundness`, `bodylength`, `abund` identified as *header names only* |
| `SiteInfo_Alltaxon_Pred_Detri_SxFD.csv` | MD5 `2b0d5e8a7c209a958b6034838d1fd1ee`; **403,751 bytes** | **41 fields**, only generic `tree` field matched with frozen exact whitelist; no unambiguous original study/plot/trap/year or quantitative deadwood units identified from generic header match |

The original published `tree` header does not, by itself, mean that **living/deadwood host resource quantities** are measured, nor does a wide CSV of 1,090 header fields prove 1,090 independent sites or species. All literal author species and site headers remain unexported.

### Source-only chronology and code correction

Initial new original three-CSV Actions [#44082790526](https://github.com/zuizui0223/Structural/actions/runs/44082790526) failed a *synthetic known-truth checksum-length test* because one locally transcribed original publisher MD5 was missing its final two characters `ee` (30 not 32 hex). This was documented [BEFORE source file retrieval](FOREST_BEETLE_WETHERBEE_NORWAY_CSV_MD5_LITERAL_FIX_20261117.md), fixed without changing the scientific protocol or row selection and independently re-tested in #44082986667. The corrected run obtained all three official MD5 matches and source header outputs without opening biology.

### Scientific decision

**NORWAY_270_ORIGINAL_SCHEMA_VERIFIED_SOURCE_LINEAGE_AND_HOSTWOOD_JOIN_HOLD.** The 2023 original publication already concluded that predator relative abundance, wing length and body roundness describe forest naturalness, so restating those effects with same original field observations is NOT new ecology. No cross-study hostwood guild predictability test is authorized until authors' method and original R reader resolves project×physical site/year units and whether local measured hostwood resources exist. A new original cohort cannot be claimed as independent of the Burner Norway historical matrices without explicit source lineage comparison.

Previous Piccini 40-plot original floor heldout +11.7% directional gain/p=.09375 **not supported**; Finland VD10 small positive/p=.015 conditional; three-country Burner conditional trait-label shuffle D+.091059; PREDICTS, Thai, NEON, BALA and mammal GEB scientific holds remain fixed. Original Georgia 40-site environment↔species ID crosswalk still unverified, Kriegel Europe Dryad primary file access HTTP401. No eBird/TinyFish, no PR merge or manuscript submission.
