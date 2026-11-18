# Structural forest macro — Neff 2022 author R-code and BExIS18270–31123 physical plot-key test (2026-11-18)

## Actual executed source-only decision

[GitHub Actions #44221854038](https://github.com/zuizui0223/Structural/actions/runs/44221854038) **SUCCESS** on the Draft forest macro PR #469 branch; artifact **14390058657**, GitHub-reported ZIP SHA256 **628a1508492e5b23ea5d6e5624b3495e83446faef31ddd6999d9f027f4d717fc**. Actual original R code from [Neff et al. 2022](https://github.com/nefff1/fcnt_blngdd/blob/main/R_full_code.R) was verified by immutable Git blob SHA1 **9bf7adb9c833275e0289ac1f459d50648ed6a17b**, without execution. The exact publisher original BExIS18270 stand-EP and BExIS31123/tag1 beetle PlotID files were SHA256-verified to the earlier frozen source bytes. ONLY original EP/PlotID values were read privately, not forest numeric/basal area, beetle taxa/captures or TrapID.

Original source fixed before this test:
- BExIS18270 **240,356 bytes**, SHA256 `1161dfe75ea6c5ee3fab1dda98c5ec1d142db2e08a03b63d6c6266bc27b0914d`, 4,200 rows / 150 original EP plot tokens.
- BExIS31123/tag1 **8,103,493 bytes**, SHA256 `73f759e8ce8b2e302dbbc5bddc947252caeb5b0b1fb15aa0280e732f7a31617e`, 59,850 source long rows / 30 physical PlotID tokens.

### One prospective alias test, and why it STOPPED

A historical Neff author R script uses a **four-character → five-character** site-name expansion in other BExIS data sources (e.g., deadwood source 24546), adding `0` after the first three characters of a 4-character plot ID. Its original **stand BExIS18270** read call, however, merely renames `EP` to `PlotID`; it does **not** apply this conversion specifically to 18270. The following is therefore an explicitly tentative, prospectively frozen source-only rule—not a validated author 18270 crosswalk.

| Source ID-only comparison | Actual result |
| --- | ---: |
| Exact original 18270 EP vs 31123 PlotID intersection (before candidate rule) | **3 / 30** |
| Original 18270 EP fields of **four characters**, eligible for author-published rule | **0 / 150** |
| Stand EP tokens changed by the one fixed rule | **0** |
| Transformed EP key collisions | **0** |
| Post-transformation original 18270 EP vs 31123 PlotID intersection | **3 / 30** |
| Previously unmatched plots recovered | **0** |
| Original experiment plots still unmatched | **27 / 30** |

**Final method status:** `METHOD_CANDIDATE_PARTIAL_OR_COLLIDED_HOLD_NO_FURTHER_ID_SEARCH`. The status label also covers collision scenarios, but the actual failure in this run was **zero eligible 4-character original EP strings and zero new matches**, not an ID collision. This specific rule is exhausted. Do NOT try arbitrary new left padding, prefix removal, fuzzy matching, code length rules or later dataframe row-order alignment. The historical Neff 2022 `18270_2` source and present pinned publisher original 18270 source may differ in internal plot-ID grammar or version—**not verified**. The original-author dataset-version crosswalk or actual author field correspondence is needed.

## Important prior art and biological boundary, independently checked

**Neff et al. (2022), *Functional Ecology*, DOI 10.1111/1365-2435.14186**, previously tested exactly three hierarchical filters in BELongDead: regional pool → forest site, site → patch, patch → offered deadwood log. Their original field system had 29 forest sites across three German regions, **347 original logs** (two temporal decomposition periods yield **694 log×period observations**, not 694 independent physical logs) and 13 functional traits. They measured local forest stand tree-basal-area composition (conifer vs broadleaf / species background), landscape, canopy, deadwood quantity and host-log identity; they found prior-published functional sorting across steps, especially tree-genus/decomposition at object scale. This is PRIOR ART. Source paper: https://doi.org/10.1111/1365-2435.14186; author repository: https://github.com/nefff1/fcnt_blngdd.

Neff's exact original R includes `mutate(PlotID = substr(TrapID, 1, 5))`, `rename(ToplaAdults = NumberAdults)`, and `filter(ToplaAdults > 0)` for a historical `31123_19_Dataset`. This proves their **specific published implementation excluded nonpositive catches**; it does NOT establish original comprehensive trap-opportunity negatives or zero-capture records. Their earlier historical `31123_19` data extraction is not assumed byte-equivalent to current published tagged BExIS31123/tag1.

Therefore a fresh Structural **host-identity / forest composition / trait filtering positive on these same German beetles is NOT a new general ecological mechanism**. The only defensible next novel test is prospectively frozen *out-of-geography predictive transport of specifically measured stand resources to separately measured functional guild composition*, beyond a source-aware historical reference, with source-native sampling effort and independent location/region holdout. BELongDead alone cannot establish between-country/biome transport.

## What was protected and next admissible task

- Original BExIS31123/BExIS31124 **15 unmatched TrapID method tuples** remain unresolved, despite common parent log/year tokens. There are no authenticated aliases.
- Original BExIS20406 vs 31123 **379/379** plot–log method tokens match literally; 2,829/2,943 original 31123 log×year tokens match eclector equipment records. Of 114 unmatched, **109 in 2013** are absent from all 20406 method rows; **5 in 2017** occur as other non-eclector method records. Neither is a false-zero sampling occasion.
- Original BExIS24546 ambient 2012 deadwood shares 30/30 exact plots but **DWV mixes m³ and m³/ha** by source stratum; do not mix, and do not equate 2012 values to all 2010–2017 exposure years.
- Forest BExIS18270 stand resource quantities/trees not read; current stand join **3/30**, no valid direct ecological exposure.
- Positive prior Structural results unchanged: Finland 142-site measured total deadwood Host_tree guild out-of-spatial-block gain +0.00024237 (nine cells, conditional p=.015), Chiu/Vogel six-plot offered-tree detected-species prediction +0.019699892 (+4.54%, 6/6 parent plots exact p=.03125), Piccini Germany eight-site floor guild directional +11.7% but exact p=.09375 (UNSUPPORTED), PREDICTS original forest alteration +0.0942, NEON CHM p=.1759 non-support.
- Original BALA and GEB holdouts untouched, eBird/TinyFish unused. No ecological scorer was run, no author contacted, no PR merge or main modification.

## Exact reproducibility

Prespecified contract: [FOREST_BELONGDEAD_NEFF2022_AUTHOR_CODE_PLOTKEY_CROSSWALK_PRESPEC_20261118.md](FOREST_BELONGDEAD_NEFF2022_AUTHOR_CODE_PLOTKEY_CROSSWALK_PRESPEC_20261118.md).
Implementation: `analysis/forest_macro_global/belongdead_neff2022_author_plotkey_crosswalk.py`.
Workflow: `.github/workflows/forest-belongdead-neff2022-author-plotkey-source-gate.yml`.
One pinned author-code rule, one pair of publisher-pinned source ID columns, and **zero** new beetle effects or stand measurements.
