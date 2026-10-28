# Structural v1.296 — Why an island-forest native/alien gradient changes sign across sampling units

**2026-10-24 · Original independently sourced plant-field result retained; new computations are source-free posthoc arithmetic, NOT a new independent ecological confirmation or a causal experiment.**

## 1. Scientific question

When forest trail edges are compared to matched forest interiors, does a positive change in **relative native-versus-introduced plant composition** necessarily mean an increase in **absolute native plant richness**? Can the mean direction of the contrast change solely because the four physically independent trails have different numbers of nested sampled area×year groups?

The [v1.295 actual published-source ecological result](https://github.com/zuizui0223/Structural/actions/runs/40074317603) was produced from the 2017–2019 Azorean trail survey DOI 10.15468/ysbzk7 on **Terceira (three trails)** and **São Miguel (one trail)**. It originally opened 210 Event and 2,733 Occurrence records (full original Event-to-Occurrence source join, zero ambiguous species-rank native/alien classifications). The response-blind physical design admitted **17 matched trail×year×area groups** represented by **147 Event lines** using the common 50, 100 and 150 cm sampling positions; the edge-only 25 cm line was omitted. These Event line rows are **not** independent ecological replicates.

The physical v1.292 strict protocol had previously STOPPED on original Event identifier vocabulary. The v1.294 revised frame was independently declared after seeing only original Event metadata, before opening any native/alien plant response; the experiment remains retrospective, not pristine-confirmatory.

## 2. Four original independent trail summaries (immutable)

The response for each matched area group was: average interior-plot log((native richness+0.5)/(introduced richness+0.5)) minus edge-plot log of the same ratio. Groups were averaged **within** each original trail, retaining original source forest sampling identities.

| Source island & anonymized trail | Matched groups | Native/alien log ratio: interior − edge | Native richness: interior − edge | Introduced richness: interior − edge |
|---|---:|---:|---:|---:|
| Terceira T1 | 1 | **−0.2554** | +0.500 | +1.000 |
| Terceira T2 | 7 | **+0.2935** | +0.786 | +0.143 |
| Terceira T3 | 6 | **+0.1306** | **−1.250** | −0.333 |
| São Miguel T1 | 3 | **−0.3063** | **−6.000** | −0.833 |

*Native and alien richness differences in this table are descriptive mean counts per matched physical plot. They are not probabilities of native persistence or effect sizes from a randomized tourism intervention.*

The positive relative-log-ratio direction occurred on **2/4 trails**, negative on **2/4**; the observed original trail effects ranged from −0.3063 to +0.2935. There is no uniform island-wide forest interior advantage.

## 3. Exact aggregate-only weighting sensitivity (v1.296)

The original **four equally weighted independent trails** remain the sole immutable primary estimate. v1.296 uses exactly those four frozen log-ratio contrasts and their matched group counts (1, 7, 6, 3); it neither reopens plant rows nor fits a model.

### All possible requested weighting summaries

1. **Equal original trails**, n=4: (−0.2554128 + 0.2934918 + 0.1305564 − 0.3062973)/4 = **−0.0344155**.
2. **Equal island means**, n=2 island contexts: average of the original Terceira three-trail mean **+0.0562118** and São Miguel one-trail mean **−0.3062973** = **−0.1250428**. Two islands do not provide replicated archipelagos or a standard inferential island test.
3. **Matched group-count-weighted trails**, n=17 nested area-year groups: weighted average of the four frozen means with weights (1,7,6,3) = **+0.0978515**. This is a deliberately **nonindependent posthoc sensitivity**, not a valid replacement primary. The 7- and 6-group Terceira trails dominate this arithmetic and both have positive relative log-ratio effects.

**The sign reverses between the original equal-trail estimate (negative) and the pseudo-replicated group-count-weighted sensitivity (positive), despite using identical field observations and no new model.** This is a verifiable *aggregation/estimand-dependence* result, not confirmation that a positive interior vegetation effect exists.

## 4. Ecologically important metric disagreement within original trails

The source yields **two nontrivial contrasting examples**:

- **Terceira T3** shows a **relative native/alien composition improvement** inside the forest (log ratio +0.1306), but **absolute native richness decreases** (−1.25 species per matched interior plot, with introduced richness −0.333). This is consistent with fewer introduced taxa shifting the relative ratio even while native richness declines.
- **Terceira T1** shows **absolute native richness increasing** (+0.5), but the **relative native/alien composition worsens** (log ratio −0.2554); introduced richness increases by +1.0.
- **Terceira T2** gains both absolute native richness (+0.786) and relative native composition (+0.2935), while introduced richness also increases modestly (+0.143).
- **São Miguel T1** shows less absolute native richness (−6.0) and a lower relative native/alien ratio (−0.3063), even though the introduced richness is also lower (−0.833).

This is an observed **decoupling of an assemblage composition ratio from absolute indigenous richness** in the sampled forest trail network: improving the ratio cannot by itself be classified as ecological recovery or increasing native plant diversity.

## 5. Island ecology and conservation interpretation

This analysis strengthens a narrow, empirically observed proposition:

> **Forest edge-to-interior plant community contrasts vary among individual trails, and the sign of relative native/alien composition is not interchangeable with the sign of absolute native plant richness. Unequal sampling within trails can reverse a pooled apparent gradient.**

For habitat monitoring, report native richness and introduced richness separately **alongside** their ratio, with physically independent trail counts. A natural-forest management interpretation should not be based only on a relative share, particularly when absolute indigenous diversity can fall while introduced species fall faster.

This does NOT identify causal trampling/visitor effects; no experimental tourism exposure was randomly assigned. It also does not transfer the original 2013 Pico local-loss-focal species response or establish a universal law of isolation/connectivity, colonization, survival or rescue. Source context differences (trail use, habitat conditions, elevation, microclimate and detection) are unmeasured alternatives. One São Miguel trail does not identify a population-level island effect; two islands are not replicated archipelagos.

## 6. Reproducibility and strict evidence ceiling

- Original published biological result: [v1.295 original GitHub Actions run 40074317603](https://github.com/zuizui0223/Structural/actions/runs/40074317603), original aggregate artifact ID **12552592439**, original ZIP artifact SHA256 **61e9cc24615bec1f1e79af6a4b04ac773dca90739a883c39c0ddd478569bfa31**.
- V1.296 fixed source: `development/azores_trail_native_alien_field_aggregate_freeze_v1_295.json` and the frozen contract `development/azores_trail_weighting_sensitivity_protocol_v1_296.json`.
- Only original independent-trail aggregate means and frozen repeated-area group counts were read, not the original 2017–2019 plant/Event values, nor any 2013 MOVECLIM/2018 ForestEco2 or protected response.
- Exact source-free solver: `scripts/azores_trail_weighting_sensitivity_v1_296.py`.
- Regression suite: `tests/test_azores_trail_weighting_sensitivity_v1_296.py`.
- The exact fixed primary is checked to 1e−12, plus 4 trail identifiers, 14+3 repeated groups, original source SHA and freeze metadata; any mismatch is a hard failure.
- Report no p-value or confidence interval; sample-unit sensitivity is **posthoc** and the group-weighted estimate is **nonindependent**. Older v1.292 STOP remains in force; GEB main manuscript scientific HOLD remains; zero new confirmatory systems; no eBird; originally protected GEB-mammal, BioTIME/RLS and Macaronesia S2–S4 observations have not been reopened.

**Executed regression verification:** [GitHub Actions v1.296 run 40078222645](https://github.com/zuizui0223/Structural/actions/runs/40078222645) **SUCCESS, 5/5 tests** after correcting a test-only field-name mismatch (no source result or threshold changed). Uploaded exact full-result artifact **12554480698**, ZIP SHA256 `7c08f0e097bed6a3e570195fe091e76f91973f2a5f4e552fd1f830fb4cb178d5`, inner JSON SHA256 `c65f9edd7162e8cefa0b012ff7ec3e83d229ec73e9a88e1868be2af61c80f738`. A compact permanent repository receipt is `development/azores_trail_weighting_sourcefree_result_freeze_v1_296.json`. All results derive only from four original frozen trail aggregates; original Event/Occurrence rows reopened **0**.

**Follow-up scientific gate:** A new externally sampled island/fragment set with multiple independently sampled edge/interior landscapes and measured native *and* introduced detection denominators is needed to assess if the within-trail heterogeneity and ratio–absolute-richness disagreement generalize. No further outcome-selected subgroup refitting on these same four trails is authorized.
