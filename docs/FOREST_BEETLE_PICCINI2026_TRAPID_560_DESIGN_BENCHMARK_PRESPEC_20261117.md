# Piccini2026 560 nominal trap-slot benchmark vs original recorded trapID — SOURCE-ONLY prespec (2026-11-17)

## Verified starting point, fixed BEFORE this test

Original published 2026 source [DOI 10.25625/H8EMJS](https://doi.org/10.25625/H8EMJS), publisher MD5, 22,414 method rows, 8 field sites, 5 stands per site, 40 plot IDs and 3 stratum labels. [Source-only dependency run #43902496929](https://github.com/zuizui0223/Structural/actions/runs/43902496929), SUCCESS, artifact #14243375009 SHA256 de15a1678092bc5fb7e6955061d23e3cd9fc6d7ef9328542700b409efd650b98:
- Original source column ordinal 4 'trap': **8** distinct labels, all reused across multiple plots and strata.
- Original source column ordinal 7 'trap_ID': **320** distinct labels, each in one plot but **120** labels reused across more than one stratum.
- Original source column ordinal 8 'trapID': **557** distinct labels, **0** labels reused across different plots or vertical strata, each repeated across 2–7 source period *tokens*. The labels are not independently verified physical traps, and original period tokens are not known calendar years.
- No original trait/guild/capture abundance value read, original zero-capture opportunity and trap-days unavailable.

Independent author published field design: **40 nominal plots × (8 floor pitfall + 3 subcanopy FIT + 3 canopy FIT) = 560 nominal plot×layer trap slots** across differently sampled years. The observed source number of 'trapID' labels 557 is arithmetically three less than this *design benchmark*, but 3 must **not** be called genuinely missing deployed traps or evidence of zero catch, because the source record contains biological captures and four plots were replaced after storms.

## One new narrowly diagnostic endpoint — no biology

1. Use the same official released 2026 source and original checksum. Select only exact original **source column spelling 'trapID'** (case-sensitive) and generic 'plot', 'stratum' and optional 'site/stand/period' metadata fields. This selection is motivated by the already executed author-header functional-dependency audit, **not** by the relative biological effect of 557/320/8 fields. NEVER use the field for a biological test in this diagnostic.
2. Reconstruct **sets of distinct recorded 'trapID' labels** within every author plot×stratum. Expect exact 40 plots×3 layers (120 groups), verify 557 source labels never cross plot×layer. Output **anonymous** sorted per-layer distributions of 40 plot-level distinct label counts, and counts of plot×stratum groups with exactly 3, 8, fewer or more. Do not print source stratum/plot/trap labels.
3. Compare the sorted layer-level 40-plot distributions against the nominal multiset [3,3,8] only as a **design compatibility audit**. Output whether the expected 560 nominal total matches 557 observed recorded labels, absolute difference 3, and the number of 40 source plots compatible with exactly one 8-ID layer plus two 3-ID layers. Never force a missing observed label to zero or invent a source-capture opportunity.
4. Counts per stratum cannot prove floor/subcanopy/canopy semantic labels, because author source 'stratum' token codebook has not yet been mapped to original calendar dates; the nominal 2019 and 2021 methods must remain separate.
5. Biological GO still requires original explicit field key semantics, complete zero-capture trap effort, trap exposure-days and taxon-guild meaning, plus four storm-changed plot crosswalk. Regardless of numerical compatibility, output **SOURCE_NOMINAL_560_VS_RECORDED_557_ONLY_NO_BIOLOGICAL_SCORE**; this audit cannot establish causal or predictive ecological effect.
6. No old original species outcomes re-opened (Thai, Finland, PREDICTS, NEON, BALA, mammals/GEB); no eBird/TinyFish. Draft PR #469 remains unmerged.

The follow-up is a diagnostic of sampling architecture; it cannot retroactively make the 2026 paper's vertical height effect identifiable across different years and trap types.
