# Ecuador forest beetle host effects: emergence versus conditional detected richness — actual second-stage result (2026-11-22)

## Scientific decision

**Within the already-published Falconí-López et al. 2026 Ecuador field experiment, host-tree labels show a strong retrospective matched-plot association with observed adult emergence but did NOT add held-physical-plot predictive information for per-log detected species richness after conditioning on positive adult counts and plot environment.**

This is a **separate outcome-exposed exploratory result** and **no evidence of a zero ecological host effect, equivalence, causal host filtering, colonization failure or multi-region transfer**. The original paper's richness/abundance/wood-density results are PRIOR ART. The source's original 4-stage pooled morphospecies data cannot become per-plot species composition.

## Frozen-before-this-score method and source label erratum

- Frozen protocol: FOREST_FALCONI2026_POST_EMERGENCE_RICHNESS_LOPO_FREEZE_20261122.md
- Pre-Spec-value codebook correction: FOREST_FALCONI2026_POST_EMERGENCE_RICHNESS_LOPO_SOURCE_LABEL_ERRATUM_20261122.md
- Original author ZIP (user-provided, publisher-authenticated): **11,201 bytes**, SHA256 **8c6e822866207a3398d6ce32fd35b6786713472ea87c2c1f3267984ebb79500d**.
- The first source-gated executable attempt stopped before the new Spec response values were read because the protocol used informal title-cased host labels instead of the exact author CSV uppercase names. Exact source labels, verified from Plot/Host only before the score: **CACAO, FERNAN SANCHEZ, GUABA, MASCAREI, SAPANILLO**. Literal spelling was corrected without changing any population, endpoint, covariate, model, hyperparameter, loss, seed, or uncertainty criterion.
- Source table: 61 unique physical Plot/Plot_IDs, 300 Plot×Host logged rows; only **59 complete physical plots × five source hosts = 295 recorded logs** entered the matched-cohort analysis. **169** logs had Indiv>0 and per-log Spec>0, and **126** had explicit zero Indiv/Spec. Both two source-incomplete plots were excluded based on original sampling opportunity before scoring this conditional richness endpoint. Each of 59 complete plots had at least one positive log.
- Original journal paper describes **62 plots / 306 recovered logs**, unresolved versus the released 61/300. The four-stage morphospecies table is not plot-grain data. A new species-composition analysis remains SCIENTIFIC HOLD.
- Original source quality gates passed: integer nonnegative Indiv/Spec on all 300 records; **Spec<=Indiv for every record**, Spec positive iff Indiv positive; exact 59-plot support, no missing numeric environmental covariates, **0 source plots with unrecorded History**.

## One frozen independent-plot predictor comparison

Response = **log1p(Spec)** on the **169 logs with recorded adult emergence**. Both models include log1p(observed adult Indiv), forest original Category4 recovery class, History, Latitude, Longitude and Elevation. E1 additionally includes exact Host categorical labels; WoodDensity is deliberately excluded because exactly one source density maps to each Host. Fixed Ridge alpha=10, training-fold-only one-hot encoding and numeric standardization. **Leave-one-physical-plot-out** 59 folds, average squared log-richness error within plot, then plot-equal average across plots. No stage subgroup fitting, feature selection, host pair, density model or hyperparameter change.

| Prespecified scored metric | Actual result |
| --- | ---: |
| Original heldout plots | **59** |
| Original conditional-positive log rows | **169** |
| E0 mean plot-equal squared log-richness error | **0.09558101005** |
| E1 (E0 + Host) mean plot-equal squared log-richness error | **0.09629291330** |
| **Primary E0−E1 gain** (positive would mean Host helps) | **−0.00071190325** |
| Relative loss change after Host added | **+0.7448% worse** |
| Plot improvements versus harms | **29 positive / 30 adverse** |
| Fixed 4,000 physical-plot-bootstrap percentile 95% | **[−0.00363818, +0.00220438]** |
| Fixed 9,999 plot signflips, two-sided Monte Carlo p | **0.6333** |
| Frozen support rule | **NOT SUPPORTED** |

The model comparison conditions on adult count, which may be affected by the offered host; it measures additional **prediction** under that conditioning, not a direct/indirect causal decomposition or proof that host has no effect on post-emergence richness. Training folds overlap and plots are within one field network: the plot-based bootstrap/signflip is only conditional exploratory uncertainty.

**Independent numerical reproduction succeeded**: sklearn pipeline results were reproduced by a separate training-fold-only closed-form normal-equation Ridge implementation with intercept unpenalized and alpha=10, matching both plot-equal losses to floating-point tolerance <1e-9. A full repeated source calculation generated identical output JSON (SHA256 **9f10c20905dbfb9a07d54f1c4897afdecf3062a587cf72aab912bea895cfb1a6**). The latter hash refers to the local aggregate JSON result, not raw biological data.

## Descriptive two-part view (NO additional significance tests)

From the same **59 complete original plots**, each host has 59 offered log rows:

| Original Host label | Observed adult-emergence-positive logs | Mean Spec among emerged logs | Mean detected Spec per offered log |
| --- | ---: | ---: | ---: |
| CACAO | 39/59 | 2.513 | 1.661 |
| FERNAN SANCHEZ | 44/59 | 3.841 | 2.864 |
| GUABA | 19/59 | 2.474 | 0.797 |
| MASCAREI | 35/59 | 2.771 | 1.644 |
| SAPANILLO | 32/59 | 2.281 | 1.237 |

For each host these values satisfy the arithmetic identity Mean(Spec over all offered logs) = P(recorded emergence) × Mean(Spec|recorded emergence). This separates **observed emergence opportunity** from richness **conditional on positive emergence**, but does NOT establish biological mediation. For example, Fernan also has much higher positive-log adult counts than some other hosts; conditional mean detected richness is not abundance/effort-standardized species diversity without per-log morphospecies abundance data.

## Extra independent source-integrity audit (no new ecological p-values)

Original PlotSpeciesIndiv_3.csv adult Individuals totals **10,650**, which exactly equal sums of log-level Indiv on **all 61 physical plot keys** (61/61 exact per-plot arithmetic matches). This is strong evidence that observed captured adult totals are consistently linked across the two source tables, despite the paper-vs-ZIP plot and log opportunity discrepancy.

**Seven of 61 physical plot records have the source plot-level Species richness field SMALLER than the largest source per-log Spec value in that same plot.** These two published-source richness fields therefore cannot be assumed to share exactly the same taxonomic inclusion/aggregation definition. The reason is unresolved; no taxon identity, deleted sample, reallocation or source-codebook fix was invented. The current score refers STRICTLY to original per-log Spec as supplied, not an independently validated species-richness measure of the plot or any species composition response.

## Scientific synthesis and next gate

Existing outcome-exposed matched within-plot five-host binary emergence contrast (Q=24.3014, 19,999 permutations, p_MC=.00005) remains **exploratory positive** under unverified host-label exchangeability. Earlier host-added **emergence** LOPO gain +0.030624, bootstrap [−0.005204,+0.064390], p=.0906 remains **NOT SUPPORTED**. The new **post-emergence detected richness** conditional LOPO adds no support. These are distinct estimands and do not combine into a single causal process or a global conservation recommendation.

The next scientifically admissible escalation is **original per-physical-log morphospecies identities, sampling opportunity/placement codebook, and reconciled all-306 recovered logs**, ideally in an independent multi-region forest network. Request tracked at Structural Issue #473. Do not rerun the present source with alternate penalties, host pair contrasts, arbitrary taxon subset or stage-specific p-values to seek support.

All old Forest, BALA, GEB, mapped mammal, PREDICTS, NEON, Finland, Chiu, Carpathian, BETA-FOR responses remain sealed. No eBird/TinyFish. Draft PR #469 only; no main merge or submission actions. Original source biological rows/plot IDs/taxa are NOT redistributed.
