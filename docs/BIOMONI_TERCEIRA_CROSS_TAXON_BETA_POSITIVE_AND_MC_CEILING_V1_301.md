# Structural BioMonI v1.300–v1.303: cross-taxon information, not proven causal community coupling

**2026-10-28 — scientific status after original biological source scoring and source-free numerical audit.**

## Observed source-backed positive result: one island, ten physical plots

Two published and independently identified taxon inventories on the **same ten Terceira 50×50m forest plots** were joined by exact original author physical plot IDs, not by nearest-point guessing. Tree original v1.7 archived 30 Event and 402 Occurrence rows; the beetle original v1.3 archived 308 Event and 539 Occurrence rows (the latter were method subevents within 16 original plots, not independent locations).

The original full beetle sampling programme was NOT equal effort between sites (13–27 original Events per plot). Strict original v1.298 was **TERMINAL**, and is still not validated. New v1.299, frozen *after seeing Event sampling design but before reading any plant/beetle species*, restricted each of the ten matching Terceira plots to **three shared source sampling methods at 1/1/4 Events, exactly six per plot; 60 beetle sampling Events**. These 60 selected Events had 120 beetle Occurrence records and 19 operational beetle taxa. 11 original woody taxa were detected. This is an exploratory alternative target, **not restoration of the failed full-programme claim**.

Original v1.300 source-locked [GitHub Actions run #40081020518](https://github.com/zuizui0223/Structural/actions/runs/40081020518) scored ten leave-one-plot-out splits (45 plot pairs are dependent, **n=10 independent plots**), each training a fixed ridge predictor of woody taxon Jaccard dissimilarity from log geographic distance and then comparing the same baseline after adding paired beetle Jaccard dissimilarity.

| Frozen original observation | Measured value |
|---|---:|
| Geography-only LOPO squared-error mean | **0.0113032821** |
| Geography plus beetle turnover | **0.0107459614** |
| Absolute LOPO-MSE gain | **+0.0005573207** |
| Relative error reduction | **4.9306%** |
| Observed > original 999 plot-label-permutation null 95th percentile | yes (null threshold **0.0004365421**) |
| Original corrected one-sided plot-label exceedance rank | **0.040** |

Original source-output ZIP artifact #12555172261 SHA256 `5a6926ecba21876c1cee72404de9d1eed39de9c7646acc2bdc267ef5be8a2107`, inner JSON SHA256 `df577a6cf44c70defcd5c675ab1ff8dc6bab810d2f11434bcadd2ed2eadb4954`. Sources [Borges et al. 2025 tree survey](https://doi.org/10.3897/BDJ.13.e158423) and [Borges et al. 2026 beetle survey](https://doi.org/10.3897/BDJ.14.e189085) are existing published data, and prior results from those authors remain prior art.

## New source-free v1.301 calculation: the 0.040 numerical rank is close to its threshold

The 999 fixed-seed sampled beetle *site-label* permutations yielded **39** null gains greater than or equal to the observed gain, giving corrected rank (1+39)/(999+1)=**0.040**. The uncorrected finite-simulation exceedance fraction is 39/999=**0.03904**; Wilson's approximate 95% interval for its finite Monte Carlo estimation error is **0.02869–0.05292**. This interval **crosses 0.05**. The observed improvement exceeds the original null's 95th-percentile cutoff by only **0.00012078 MSE units**.

**Important:** This is a numerical Monte Carlo precision interval under the *already chosen* random plot-label shuffling procedure. It is **NOT a 95% CI on the ecological effect**, and it does not repair exchangeability violations. A rank of 0.040 should not be promoted into a robust independent biological mechanism demonstration. v1.301 is an exact source-free audit; its fixed input and reproducible solver and regression suite are:
- `development/biomoni_woody_beetle_v1_300_observed_aggregate_freeze.json`
- `development/biomoni_woody_beetle_mc_precision_protocol_v1_301.json`
- `scripts/biomoni_woody_beetle_mc_precision_v1_301.py`
- `tests/test_biomoni_woody_beetle_mc_precision_v1_301.py`
- `development/biomoni_beta_precision_result_freeze_v1_301.json`

Structural full CI exposed a 0-bound floating error in the Wilson formula, which was fixed by clamping only probability endpoints to [0,1] and then **all standard standalone Python versions passed**. No biological input or empirical threshold changed.

## Ecological hypotheses and what remains open

**Supported narrowly:** at these ten original forest plots, *source-observed* beetle taxon turnover carries a small degree of out-of-plot predictive information about woody assemblage turnover beyond the specified smooth geographic-distance ridge reference.

**Still not supported:** (i) trees drive beetle communities causally; (ii) forest vegetation is a generally reliable cross-guild biodiversity surrogate; (iii) shared forest-fragment membership, habitat condition or autocorrelation does not explain the gain; (iv) island demographic donor–recipient rescue or persistence; (v) cross-archipelago generalisation.

The original 2019 plot-design literature describes Terceira plots spanning **four native forest fragments**. Since the v1.300 baseline conditions only on pairwise geographic distance, shared habitat/fragment effects have **not** been separated. Further posthoc re-scoring v1.300 on the same original ten plots to chase a favorable alternative null would be inappropriate, particularly given the small number of plots and borderline numerical precision.

Also note that the beetle composition of a new held-out forest plot is observed as a predictor in the v1.300 LOPO evaluation. This is useful for a **measured cross-taxon surrogate**, not a forecast of a completely unsurveyed plot from geography alone.

## Next disjoint biological target: spiders on these same original plots

A pre-existing **spider inventory** on the same NETBIOME/MACDIV Azores plots (Malumbres-Olarte et al. 2019, [Biodiversity Data Journal 7:e32625](https://doi.org/10.3897/BDJ.7.e32625)) offers a biologically distinct animal assemblage: if independently inventoried spider turnover also predicts woody turnover conditional on the same geographic baseline, that would distinguish a guild-specific beetle signal from one recurring across more arthropods. Neither result would establish cause or a different island.

The original spider [GBIF dataset DOI 10.15468/kcgjfr](https://doi.org/10.15468/kcgjfr) v1.8 contains **423 Event / 1,639 Occurrence** records (the earlier paper cites 121 original Events, thus version matters). Response-opaque v1.302 source admission [GitHub run #40540875769](https://github.com/zuizui0223/Structural/actions/runs/40540875769) **passed**, original ZIP SHA256 `17f65284214ae35a302fee2fa42747e2ecfabb8d04bf9ec8394b6d33c5c4f7b5`; spider Event and Occurrence *data* rows opened **zero**. Event/Occurrence keys, plot location, sampling method, date, taxon name and rank columns are present in source schema.

The frozen v1.303 next stage asks whether the original spider and tree `locationID` plot identities **exactly correspond for all ten Terceira locations**, and whether equivalent original Event effort across the shared spider sampling methods exists, before opening any spider taxon name. If the physical gate fails, no conclusion about spider–woody similarity can be scored. Note the spider and beetle COBRA protocols share a monitoring tradition and potentially some sampling opportunities; biologically distinct taxa are not fully independent collection replicates.

## Scientific conclusion for this PR

**Terceira's fragmented forest plots show tentative observational cross-taxon turnover information, not an established structural ecological mechanism.** Keep the old v1.298 full-method gate terminal; do not claim management causality or island donor rescue. GEB scientific HOLD and zero newly admitted pristine confirmatory systems continue. eBird unused. No original mammal/BioTIME/RLS or Macaronesia S2–S4 protected response reopened.
