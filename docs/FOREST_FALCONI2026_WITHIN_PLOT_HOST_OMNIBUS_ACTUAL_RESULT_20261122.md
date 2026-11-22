# Ecuador saproxylic beetles: five-host emergence sorting within physical forest plots (2026-11-22)

## One executed original-data result — EXPLORATORY conditional association

**Within the same 59 physical plots, recorded adult beetle emergence differs among the five standardized offered tree-host types under a fixed within-plot exchangeable-label conditional null.** This remains a **retrospective, previously outcome-exposed, one-study observational association**, not newly collected biology, a causal host-selection experiment or a confirmed cross-forest generalization.

Original field study: Falconí-López et al. (2026), *Forest Ecology and Management* 619:124102, DOI 10.1016/j.foreco.2026.124102. The authors **already reported** increasing abundance/richness with recovery, host networks, density and stage-dependent specialization. This is a separate matched-binary statistic, not a first discovery of saproxylic host filtering.

**Original source:** author-distributed `R skript and raw data.zip`, user supplied exact original 11,201 bytes, SHA256 `8c6e822866207a3398d6ce32fd35b6786713472ea87c2c1f3267984ebb79500d`. The original PDF reports 62 plots and 306 recovered logs; the available physical-key source table has **61 plots and 300 log rows**, and a complete five-host matched denominator of **59 physical plots / 295 log rows**. Two source-incomplete plots (4/1 logs) are not converted to no-emergence, never scored or extrapolated. The source-only plot/log key and zero-vs-positive audit was already completed before this new statistical question. Original 4-stage × host × morphospecies records cannot be treated as plot-level species composition.

### One frozen whole-five-host test, not the outcome-selected best pair

Protocol [FOREST_FALCONI2026_WITHIN_PLOT_HOST_OMNIBUS_FROZEN_20261122.md](FOREST_FALCONI2026_WITHIN_PLOT_HOST_OMNIBUS_FROZEN_20261122.md) saved after known host rates (therefore only exploratory) and **before the new omnibus score**. For original 59×5 binary (Y_{ih}=1[mathrm{Indiv}_{ih}>0]), condition on each physical plot's original number of positive logs. Cochran's Q of the five column success counts is **24.301369863013697**. Exact source arithmetic independently agrees with `statsmodels.stats.contingency_tables.cochrans_q`: Q = 24.301369863013697 (reference asymptotic chi-square 4df p = 0.0000694981; not the fixed primary p).

**Fixed conditional null:** within each plot, randomly permute only host labels (never exchange between plots or stages); 19,999 permutations, seed 20261122, one-sided Q-tail with +1 adjustment. **0 / 19,999** randomized Q values reached the observed Q; reported Monte Carlo resolution-limited **p = (0+1)/20,000 = 0.00005**. This is a Monte Carlo estimate with finite resolution, not a fully enumerated exact p and not proof of a design-based randomized treatment.

| Offered host | Source matched logs with detected adult emergence | Source matched logs total | Recorded emergence fraction |
| --- | ---: | ---: | ---: |
| CACAO | 39 | 59 | 66.10% |
| FERNAN SANCHEZ | 44 | 59 | 74.58% |
| GUABA | 19 | 59 | 32.20% |
| MASCAREI | 35 | 59 | 59.32% |
| SAPANILLO | 32 | 59 | 54.24% |

All 169 positive original log outcomes retained; the other 126 were original zero-capture logs, not invented absent/deployed logs. Omnibus maximum-minus-minimum fraction **0.4237288136**, descriptive only; Fernan-vs-Guaba is outcome-selected and has **no new pairwise p-value**. Source matched physical-plot positive-log counts (number out of five): 1:8, 2:12, 3:22, 4:14, 5:3. This shows 59 independent plot clusters, not 295 independent forests or 10,650 replicate individuals.

**By source forest recovery class, descriptive only (physical plots):**
- Agriculture (11): Cacao 4, Fernan 6, Guaba 4, Mascarei 4, Sapanillo 4
- Early regeneration Reg1 (21): 14, 16, 5, 12, 13
- Late regeneration Reg2 (12): 9, 10, 3, 8, 7
- Old growth (15): 12, 12, 7, 11, 8

No additional stage-stratified hypothesis test was performed. Source `WoodDensity` is unique and constant per offered Host label; separate identity vs density causal effects are **unidentifiable**.

### Key contrast with previously scored LOPO predictive endpoint

The **earlier** 59-plot crossvalidated E0→E1 gain after adding Host to forest recovery/location reference was **+0.030624 log loss** (~4.63% reduction), 95% plot-bootstrap **[-0.005204,+0.064390]**, conditional p=0.0906: **NOT SUPPORTED**. The stronger within-plot omnibus and weaker new-plot predictor are not contradictory. They test different hypotheses: **local host-associated sorting in known matched plots** versus **reliable extra predictive information after accounting for stage/location in held-out plots**. A within-plot Q cannot rescue the failed held-plot predictive support, nor does the 59-fold crossvalidation create 59 independent forests.

### Inferential boundaries and next biological gate

The conditional null assumes original standardized logs/effort and comparable within-site placement. Source documentation does **not** verify random host-log placement, source substrate microconditions, equal decay or instrument-level catch; a small within-plot p cannot establish a randomized causal effect on colonization, host preference or density. Binary `Indiv>0` means observed adult emergence, not total population occupancy. More data are needed to compare **actual plot×host×morphospecies** community replacement, detectability and resource continuity. One Ecuadorian field network does not make an island-like source-pool mechanism or 3D forest niche general law.

**Runnable source-frozen code**: `analysis/forest_macro_global/falconi2026_within_plot_host_omnibus.py`. Original ZIP must be supplied locally; the repository holds no raw beetle/log rows, field IDs or species IDs. No earlier PREDICTS, Finland, Chiu, Carpathian, BETA-FOR, NEON, BALA, mammal or GEB frozen score changed. No eBird/TinyFish; PR #469 remains Draft/unmerged.
