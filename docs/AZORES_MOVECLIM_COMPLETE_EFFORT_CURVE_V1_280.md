# Azores MOVECLIM: complete source-free equal-plot sensitivity (v1.280)

**2026-10-23 · Retrospective mathematical sensitivity, NOT new field observations or independent confirmation.**

## Question and immutable source

The original v1.278 standardized 2013 native-vegetation frame contains 58 independent 10×10-m plots on Pico (24), Flores (10), São Miguel (12) and Terceira (12). Against the frozen historical local-loss-affected taxon universe, Pico had 5 documented native focal taxa and 26 species×plot positives; the others had one focal taxon each (with 7, 3 and 9 positives, respectively). Reference native flora was retained for composition normalization.

The v1.279 primary comparison was **10 equal randomly drawn plots** within each *original, nonrandom* island plot frame. It gave Pico expected focal richness at least 8/3 versus at most 1 on every other island, and a conservative ratio of expected focal to total native richness of at least 5.346% on Pico versus at most 2.927% elsewhere.

This v1.280 continuation reads **only the committed v1.278 four-island count aggregates**, checks the frozen SHA, survey totals and existing v1.279 m=8/m=10 invariants, then extends the same exact hypergeometric analysis to **every integer common plot effort m=1,...,10**. It does not download or reopen MOVECLIM records, species labels, dates, plot coordinates or protected ecological holdouts.

## Full-range result

For each m and species occupancy k in N source plots, a simple random m-plot sample contains the species with probability 1−C(N−k,m)/C(N,m). The same concavity-based extrema as v1.279 yield sharp lower and upper expected richness bounds using only N plots, T focal taxa, and P positive species×plot cells. Ratio bounds divide the minimum focal expectation by minimum focal plus maximum reference expectation (or the converse for the upper bound).

| Equal plots m | Pico minimum expected focal taxa | Largest other-island maximum | Pico minimum focal fraction of expected native richness | Largest other-island maximum | Certified dominance: richness / fraction |
|---:|---:|---:|---:|---:|---|
| 1 | 1.083 | 0.750 | 8.904% | 6.338% | yes / yes |
| 2 | 1.330 | 0.955 | 6.231% | 6.495% | yes / **not certified** |
| 3 | 1.500 | 0.995 | 5.240% | 5.778% | yes / **not certified** |
| 4 | 1.667 | 1.000 | 4.844% | 5.085% | yes / **not certified** |
| 5 | 1.833 | 1.000 | 4.708% | 4.528% | yes / yes |
| 6 | 2.000 | 1.000 | 4.710% | 4.082% | yes / yes |
| 7 | 2.167 | 1.000 | 4.798% | 3.715% | yes / yes |
| 8 | 2.333 | 1.000 | 4.943% | 3.409% | yes / yes |
| 9 | 2.500 | 1.000 | 5.129% | 3.150% | yes / yes |
| 10 | 2.667 | 1.000 | 5.346% | 2.927% | yes / yes |

**Positive robust result:** Even under the most unfavorable unknown per-taxon plot incidence distribution consistent with the original survey counts, Pico's *expected focal species richness* exceeds the most favorable bound for each other island at **every** common sample size m=1..10. The proportional enrichment bound is robust for m=5..10 (and m=1), not for m=2..4. Thus the v1.279 m=10 conclusion is not an isolated choice of plot effort.

**Important negative qualification:** “Not certified” at m=2..4 is not evidence of a reversal in actual resamples: broad adversarial composition intervals overlap. All numbers concern an *expectation over random subsampling of already chosen plots*. They are neither realized-subsample guarantees, confidence intervals, p-values, nor proof of a Pico refugium or dispersal route. m=1 is a different, highly plot-local incidence contrast and should not be advertised as a stronger ecological replication.

## Ecological ceiling and next appropriate test

The descriptive pattern is an enrichment of historical-loss-affected native plants in sampled, relatively intact Pico vegetation. Equal plot counts remove one narrow sampling-effort explanation, **not** differences in habitat sampling, elevation gradients, island area, historical focal-taxon ranges, vegetation preservation or detection. The earlier within-Pico elevation rank contrast was only +0.0336. No historical full taxon×island at-risk frame, viable pre-loss donor populations, colonization/rescue or site-based survival interval has been estimated.

A genuinely biological step beyond these bounds would require independently dated and repeat-identified plots across *matched vegetation and disturbance/elevation strata*, including island-specific sampling effort and historical at-risk range. The present source-free sensitivity does not authorize opening any reserved raw biological outcome or tuning the already consumed original mammal/BioTIME/RLS data.

## Reproducibility and firewall

- Verified count source: development/azores_MOVECLIM_2013_native_plot_field_result_freeze_v1_278.json (original MOVECLIM SHA256 612dad4edc1a5fb8e9fd057167320144d8a7791a02d1245513d58fd6c8cdabc4).
- Original m=10/m=8 contract and exact hypergeometric solver: scripts/azores_MOVECLIM_2013_rarefaction_bounds_v1_279.py.
- This full-grid recomputation: scripts/azores_MOVECLIM_full_effort_curve_v1_280.py.
- Focused regression: tests/test_azores_MOVECLIM_full_effort_curve_v1_280.py. Local independent count-fixture check passed 3/3; repository CI status must be checked separately.
- No raw field rows re-accessed; no eBird; Macaronesia S2/S3/S4, original mammal/BioTIME/RLS protected outcomes unchanged; GEB scientific HOLD; zero new confirmatory admissions.
