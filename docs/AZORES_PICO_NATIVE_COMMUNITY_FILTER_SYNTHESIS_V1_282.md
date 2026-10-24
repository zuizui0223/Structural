# Pico: native-community filtering, not demonstrated focal-specific refuge (v1.281–v1.282)

**2026-10-23 · Executed published-source, nonconfirmatory ecological analysis. This interpretation supersedes any unadjusted "alien plants exclude the focal taxa" language.**

## The substantive positive result

The original published 2013 MOVECLIM survey was restricted to relatively intact indigenous Azorean vegetation. Among the 20 species fixed as well-supported island-level historic local-loss taxa in CSIC S1, five native species were detected in Pico's 24 independent plots. Original S1 and original MOVECLIM source fingerprints and 58/232/2539 and 20/24 denominators were verified again.

The frozen v1.279–v1.280 exact equal-plot-effort finding remains: the enrichment of focal taxa in **Pico's sampled intact vegetation** relative to three other sampled islands cannot be removed simply by reducing Pico from 24 to ten uniformly randomly selected *existing* plots. It says nothing by itself about island-wide abundance or extirpation risk.

The **new v1.281 original-source ecological result** adds habitat condition:
- Of Pico's 24 plots, **19** contained at least one focal native taxon and **5** contained none.
- 19 focal-positive plots had **15** introduced species×plot incidences = **0.7895 introduced taxa per plot**, while the 5 focal-negative plots had **12** = **2.4000 introduced taxa per plot**.
- Focal taxon equal-weight introduced exposure: **0.7400** versus **1.1882** in 49 other native taxa, **−0.4482**, retaining a negative sign after crude two-half elevation standardization **−0.5035**.
- All four island frames had negative *plot-presence* contrasts, but Flores, São Miguel and Terceira had only one detected focal taxon apiece, and the taxa are not independent island replicates. Only Pico clears the pre-frozen taxon-weighted comparison gate.

## The decisive competing explanation is general native community richness

The separately frozen, source-replayed **v1.282** sensitivity used a two-covariate *descriptive* fixed-ridge correction for (1) continuous within-Pico ranked plot elevation and (2) the number of all native plant species per plot. There was no lambda tuning; fixed slope L2 penalty = 1.0. Exact execution [run 39905350435](https://github.com/zuizui0223/Structural/actions/runs/39905350435) passed all 8 targeted tests.

| Measure | Observed contrast |
|---|---:|
| v1.281 focal minus reference alien species exposure, unadjusted | **−0.44817** |
| v1.281 coarse elevation-half residual exposure | **−0.50347** |
| v1.282 after native richness and continuous elevation fixed-ridge residualization | **−0.10459** |

The magnitude attenuated **76.66% as a descriptive ratio of absolute point estimates**, not as a percentage of causal effect or variance explained. The remaining adjusted difference is still negative but very small relative to the original exposure scale, and no confidence interval, independently replicated experimental system or causal mediator model is available.

Native richness was dramatically unequal:
- Across **19 focal-positive** plots, mean total native richness = **14.3158**.
- Across **5 focal-negative** plots, mean total native richness = **4.0000**.

Importantly, this is *not* only a tautology caused by counting the focal plants themselves. Using **only frozen aggregate counts** without reopening any taxon rows:

- Focal-positive plots contain 19×14.315789… = **272 native plot×species incidences**, of which **26** are focal species. Thus **246 other-native incidences**, or **12.9474 other native taxa per plot**.
- Focal-negative plots contain 5×4 = **20 other-native incidences**, or **4.0000 other native taxa per plot**.
- The other-native totals reconcile exactly: **246+20=266**, matching the original reference-native incidence denominator.
- Other-native species richness therefore is **3.237 times greater** in focal-positive compared with focal-negative plots, even after removing all focal taxa from the comparison.
- The respective introduced species plot-incidence totals **15+12=27** also reconcile to the SHA-verified original.

This yields an actually interpretable ecological pattern: **the historical-loss-affected focal taxa co-occur with a richer indigenous assemblage, not merely with absence of alien species in otherwise equivalent plots**. It makes whole-community habitat composition a serious competing explanation for a taxon-specific invasive-exclusion mechanism.

## Inference boundary: why this is not yet a "refugium mechanism"

1. Focal-positive plot grouping is defined by focal presence, so any native richness metric *including* focal taxa has mathematical self-inclusion. The aggregate-only 12.947 vs 4.000 nonfocal richness comparison checks that the difference is not *entirely* self-inclusion; it does not establish independent habitat causation.
2. Introduced richness, native richness, elevation, cover and native-forest sampling selection can be downstream of unobserved habitat quality, climate, human pressure and history. Fixed ridge residualization can remove signal or adjust for shared outcomes/mediators; 76.7% attenuation is not an ecological pathway contribution.
3. Single 2013 plots reveal co-occurrence only. No experimental invasion, contemporaneous complete whole-island flora, pre-loss donor viability, observed among-island movement, actual colonization, survival or demographic rescue was tested.
4. Historical local extinction cases are a case-only source and do not include the universe of historically occupied and persisted taxon-island populations. Checklist nominal 2010 dates are not independently surveyed current population status.
5. Comparability beyond the surveyed native-vegetation frame remains unknown: Pico had 24 sampled plots, while the other three had 10–12, with unequal habitat, area and elevation coverage. Exact random rarefaction removes *count* alone, not habitat selection.

## Current preferred *testable* ecology hypothesis, not supported mechanism

**Shared habitat filter hypothesis:** Island populations of Azorean native plants with recorded local losses elsewhere are associated with structurally intact, indigenous-rich plant communities. Their apparent aversion to introduced plants largely reflects the same landscape filter affecting other indigenous species, rather than an exclusive "remnant donor" identity.

A rival **focal-specific vulnerability** hypothesis predicts a substantial negative invasive-pressure contrast even after matching native richness, vegetation, elevation, climate, island area and historical range footprint. The v1.282 data are more compatible with a general community filter than with a large special contrast, but the result is too small, retrospective and confounded to choose causally between them.

## Next independent ecological evidence gate

**STOP further fitted alternative predictors on these same 24 exposed Pico plots.** No rescues by data-derived habitat bins, posthoc invasion indices, thresholds or pseudo-replication.

A new ecological design must prospectively fix a surveyed **habitat/disturbance/elevation sampling frame** across several islands, record indigenous richness and alien-plant incidence per permanently identified plot (with true non-detections and repeated visits), align native species and historical range eligibility *before* inspecting target outcomes, and compare future plot detection/persistence separately from historically documented loss cases. Only independently measured source-to-target movement with a denominator could address "Pico is a donor" or metapopulation rescue.

## Reproducibility

- v1.281 frozen exploratory protocol: development/azores_MOVECLIM_2013_introduced_pressure_protocol_v1_281.json; actual outcome [run 39904415725](https://github.com/zuizui0223/Structural/actions/runs/39904415725); aggregate artifact ID **12480152663**, extracted JSON SHA256 **135a4c5f598f686ce3691d79aa0a59b427036128d8e99760321dbc3d4f208a27**.
- v1.282 pre-reaccess retrospective sensitivity: development/azores_MOVECLIM_richness_elevation_adjustment_protocol_v1_282.json; actual outcome [run 39905350435](https://github.com/zuizui0223/Structural/actions/runs/39905350435); aggregate artifact ID **12479994959**, extracted JSON SHA256 **3ea87c240c663c9c60383c49492b03240268f8b91da313a36821264a388d476f**.
- Source-free aggregate subtraction verifies 246+20 reference incidences and 15+12 introduced incidences; no species names, site IDs or coordinates exported.
- Original 529 mammal heldout, BioTIME reserved, RLS, Macaronesia S2/S3/S4 and exhausted Pico GPS5 responses were not reopened. **GEB scientific HOLD; zero new confirmatory admissions; eBird off.**
