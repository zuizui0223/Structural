# BETA-FOR 2025 four header-role identity from ORIGINAL AUTHOR R SCRIPT — new source-only v4 prefreeze

v3 original first-four-field diagnostic [#44732045081](https://github.com/zuizui0223/Structural/actions/runs/44732045081) successfully verified original 28.4MB `com_singletons.csv` but STOPPED at `ORIGINAL_UNMATCHED_FOUR_HEADER_FIELDS_UNSAFE_OR_DUPLICATE`; old v3's restriction to four nonempty unique safe ASCII identifiers remains immutable. No original organism rows were parsed.

## Independent first-party author method, verified before v4 original source read

The **separate publisher original code archive** DOI [10.5281/zenodo.15165462](https://doi.org/10.5281/zenodo.15165462), public version v1, provides:
- `01_Singleton_Filter.R`, original MD5 **54a9473aeba0d5e680897bde3c412787**. Author `read.delim(...,sep=';')` on original `data/com_singletons.csv`; **`coloff <- 4`** and sampling fields are columns 5 onward. Correcting singletons uses original estimated-vs-observed counts and seed1; the *corrected* data file is generated separately, NOT the same as raw original file.
- `02_Prepare_Data.R`, original MD5 **8f0d3fdf0ad14ac4bf38f579a017329e**, identifies `sample$X`, `sample$Order`, `sample$Family`.
- `06_iNEXT_3D.R`, original MD5 **ac36dd37848693eb48d35196902f6389**, `matti <- sample`, `rownames(matti) <- matti$OTUNr` and drops `Family, Order, OTUNr`; author works with abundance-type OTU matrix and **98% sample coverage** when estimating Hill TD and PD, not raw richness as corrected occupancy.
- `09_indicatorspecies.R`, original MD5 **2c7888ab3733a2b651f7650604f12345**, explicit author meta fields `OTUNr, Family, Order`, then patch/sample labels. Authors already established indicator species differences across open/closed and with/without deadwood; this is PRIOR ART.

The exact original `com_singletons.csv` FIRST header was fixed by previous source stream SHA256 **9fc427a6ed338de1f0bd3903668049b9814e0569a2ac9d1defd72d505a4d12af**, has 598 semicolon columns, including EXACT 594/594 literal sample labels from `BETAFOR_information.csv`. Four non-sample header tokens remain.

## New frozen v4 source schema test; still no biological values

1. Fetch ONLY official published record 15371332 `BETAFOR_information.csv` and `com_singletons.csv`, exact published MD5s, as done v3; stream source body for MD5 but parse ONLY first physical OTU CSV header; verify 598 columns, original complete first-header SHA and 594 original sample literal labels.
2. **New author-evidenced allowed first four metadata positions ONLY:** exactly **one empty/unnamed first column** that R may import as synthetic `X`, plus the literal three original author field names `OTUNr`, `Family`, `Order` in any order, *OR* the same three plus explicit literal `X`. The unnamed (index1) variant is authorized by the original code's `sample$X <- NULL` and previously failed all-nonempty first-header gate. No other unknown header symbol, synonym, duplicate or additional fields permitted; if mismatched, STOP and don't guess.
3. Expose only the source anonymous semantic role admission booleans and position indices for four columns (not raw original taxon IDs, sample IDs, or raw OTU values). Do not read sample rows or any original OTU record body. **A v4 header PASS authorizes no biological effect scoring on its own.** Taxonomic assignment, duplicate OTU ID check, original singleton correction and sequence coverage gates require a separate prospective biological protocol.
4. Never retune original v1/v2/v3 STOPs, existing unrelated forest/Island results, genus/taxon selection or source namespace. Source original row/abundance access remains zero.

This is a methodological source-codebook compatibility audit, not a resubmission or positive ecological experiment. No eBird/TinyFish, PR #469 Draft, main unchanged.
