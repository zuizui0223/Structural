# Ecuador Falconí-López beetles: 59 matched physical plots × 5 standardized host logs — actual original-data exploratory result (2026-11-22)

## Decision

**Observed host-tree labels had a positive but not decisively supported incremental value in plot-heldout prediction of observed adult beetle emergence. Adding host×recovery-stage interactions made prediction worse.** This is **within-one-original-study, source-grain-adapted retrospective exploratory evidence**, not confirmatory generalization or a causal host-tree effect. The original authors already published host/beetle/recovery ecology; this is a narrower analytical predictive reanalysis and not new fieldwork.

- Input author archive `R skript and raw data.zip`, verified **11,201 B / SHA256 `8c6e822866207a3398d6ce32fd35b6786713472ea87c2c1f3267984ebb79500d`**; user supplied the exact publisher file, matching [earlier original ZIP source-only receipt #45019858359](https://github.com/zuizui0223/Structural/actions/runs/45019858359).
- Original paper DOI 10.1016/j.foreco.2026.124102. Source plot metadata had **61** unique exact Plot=Plot_ID keys (vs 62 author field plots). Log table contained **300** unique Plot×Host source rows (vs 306 reported recovered logs), with **171** observed positive emergence-count logs and **129** explicit zero-count logs (43.0%). Original 300 rows summed to **10,650 adult beetles**, numerically matching the paper.
- Original source opportunity: **59 complete 5-host physical plots = 295 rows**, plus one partial four-host plot and one one-host plot. The two partial plots are **not imputed as biological zeros**, and were excluded from the predefined *complete-matched-plot* primary denominator solely by source opportunity, before scoring outcomes. Primary: 59 complete plots, 169 positive + 126 zero log rows, total 10,419 individuals. Recovery-stage physical plot distribution: Agri 11, Reg1 21, Reg2 12, Old 15.
- The source `PlotKat4HostSpecIndiv_3.csv` `Plot` key has only **four recovery-stage labels**, NOT original 61 physical Plot keys. Therefore **no physical plot×host×species matrix exists in the supplied ZIP**, and the originally proposed conditional species-composition Y2 LOPO remains strict **SOURCE_NON_IDENTIFIABLE_HOLD**. Never turn the 4-stage pooled abundances into 59 invented independent plot responses.

## Frozen model and actual one-pass response score

Follow [source-grain adapted source-count-only freeze](FOREST_FALCONI2026_59_PLOT_COMPLETE_HOST_EMERGENCE_EXPLORATORY_FREEZE_20261122.md), distinct from the earlier [full-cohort 62/306 admission that did not pass](FOREST_FALCONI2026_BEETLE_HOST_TWO_STAGE_PROTOCOL_FROZEN_20261122.md).

Response per recorded source log: **any observed adult emergence** = `Indiv>0`; explicit `Indiv=0` is a recorded no-emergence observation, not proof that colonization failed. Hold out each full original physical Plot in turn, never split its five host logs across train/test. Logistic regression L2 C=1.0, training-only source factor one-hot and numeric scaling, no post-outcome penalty/variable/taxon tuning.

- E0: source Category4 + History + latitude/longitude/elevation.
- E1: E0 + the exact five-level offered Host factor.
- E2: E1 + source Category4×Host interaction (exploratory secondary).

| Original matched-plot heldout metric | Actual |
| --- | ---: |
| E0 log loss, 59-plot-equal | **0.66111654** |
| E1 + Host log loss | **0.63049244** |
| **E0−E1 positive gain** | **+0.03062411**, about **4.632%** lower source plot-heldout loss |
| Positive / adverse plot-level gain | **37 / 22** of 59 |
| 4,000 resampled plot-bootstrap 95% interval | **[-0.00520422, +0.06438977]** |
| 9,999 random plot-signflip, two-sided conditional p | **0.0906** |
| E2 + Stage×Host log loss | **0.65676261** |
| **E1−E2 interaction gain** | **−0.02627017** (harmful, ~4.17% relative) |
| E1−E2 bootstrap 95% | **[-0.04251452, −0.01037466]** |
| E1−E2 conditional plot signflip p | **0.0028**; 24 positive / 35 negative |

**Primary decision:** E0→E1 point estimate favors host identity, but the predeclared uncertainty includes zero, and conditional p>.05. **Not established as a robust host-factor predictive gain**, let alone broad forest generality. E2 is an over-complex predictor within this cohort; its out-of-plot performance is worse than E1. This is **NOT evidence for the ecological absence of host×recovery effects**, because shrinkage, limited physical plot count and source-level study design limit power/transport.

**Predeclared sensitivity (retain BOTH partial plots):** all **61 physical plots / 300 included log rows**, E0 loss **0.65877926**, E1 **0.62445838**, gain **+0.03432088** (~5.210%); 39/61 plot gains positive; 4,000-plot bootstrap 95% **[-0.00112766, +0.06762692]**, conditional p **0.0588**. Direction agrees, **still not positive support under the uncertainty gate**. These are reweighted observations from the SAME parent study, not independent replication.

## Original source matched-host descriptive counts (no extra post-hoc tests)

Positive adult-emergence logs / recorded log opportunities in **59 complete plots**:

| Recovery stage | CACAO | FERNAN SANCHEZ | GUABA | MASCAREI | SAPANILLO |
| --- | ---: | ---: | ---: | ---: | ---: |
| Agri (n=11 plots) | 4/11 | 6/11 | 4/11 | 4/11 | 4/11 |
| Reg1 (n=21 plots) | 14/21 | 16/21 | 5/21 | 12/21 | 13/21 |
| Reg2 (n=12 plots) | 9/12 | 10/12 | 3/12 | 8/12 | 7/12 |
| Old (n=15 plots) | 12/15 | 12/15 | 7/15 | 11/15 | 8/15 |

`FERNAN SANCHEZ` has comparatively high recorded emergence across strata and `GUABA` comparatively low; these **descriptive, outcome-exposed contrasts** cannot be promoted to a new post-hoc species-pair hypothesis test. They may reflect source tree traits, observation stage, or sampling differences, not assigned host selection by an independently tracked colonist.

**Important mechanistic nonidentifiability:** source `WoodDensity` is constant within each host species in the log dataset (CACAO=0.42, FERNAN SANCHEZ=0.52, GUABA=0.57, MASCAREI=0.64, SAPANILLO=0.32). Thus host identity and this density variable are perfectly linked; their separate causal effects **cannot** be identified from these five offered host definitions. The 96% Scolytinae share cited in the original author paper also means adult abundance alone may not represent whole-beetle functional diversity; our main binary endpoint avoids treating adult totals as richness or biomass.

## Boundary, future requirement

All log-loss folds share training data and sites are within one field network; bootstrap/signflip inference is only conditional/descriptive and cannot replace spatial-region holdouts or random assignment. The source discrepancy 61/300 versus original 62/306 remains unresolved; the source inclusion and missing log reasons are NOT reconstructed. Source original data remains local and is **not** committed/re-exported; only aggregate counts and results are logged.

The next genuinely novel ecological test needs original-author physical `Plot×Host×Morphospecies` data (not four-stage pooled species tables) PLUS a recoverable 306-log source opportunity ledger, or an independent multi-forest network with standard matched hostwood, actual absence/effort recording, region blocks and a frozen species/guild endpoint. **Do not re-run the current source with a different penalty, stage subset or loss to obtain a smaller p-value.**

PR #469 remains Draft/unmerged; prior PREDICTS, Finland Host_tree, Chiu, Carpathian, BETA-FOR, NEON, BALA and mapped mammal scorers unchanged. No eBird/TinyFish.
