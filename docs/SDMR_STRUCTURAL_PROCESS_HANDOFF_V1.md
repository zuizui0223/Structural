# Structural ↔ SDMR process-information handoff v1 (development)

**Status 2026-11-19:** Method-alignment document ONLY. No amendment to Structural A-Islands/Tanzania, BALA, global forest macro, beetle response, or any prior sealed manuscript result. No new biological analysis. SDMR Product-A/M5 frozen and Product B blocked.

## Shared inferential question

After an adequate, declared reference R for a particular held-out endpoint Y is supplied, does a structurally typed coordinate C retain predictive information? Is that information also available through *other representations*, and does it transfer across independent geographic/temporal contexts?

**Important**: Structural already asks the incremental-adequacy question for typed landscape connectivity and prior history. SDMR extends that question to a many-to-many **process-information carrier closure**, with explicit unresolved/unavailable states and synthetic error-control evaluation.

### Distinct stages

| Stage | Structural native concept | SDMR native concept | Scientific ceiling |
|---|---|---|---|
| Reference adequacy | R0/R1/R2/C; endpoint- and operator-specific reference | full-system adequacy before process questioning | Predictive sufficiency is conditional on declared candidate/reference, not mechanistic cause |
| Incremental information | C-R reference conditioned heldout loss | R vs R+C block-equal paired additive loss | One variable's incremental value is NOT full ecological process importance |
| Carrier substitution | landscape, resource, origin and state representations that overlap | many-to-many process registry, all-carrier ablation | A single predictor may be redundant when a whole process is not |
| Space/time separation | current configurations versus future changes / observed detection | spatial block versus same-interval within-site change and future-lag gate | Temporal change association is NOT a prior-to-future forecast |
| Observation | sampling method, zero frame, detection and attrition eligibility | observation/survivor-selection audit; unresolved/unavailable states | Recording/detection artifacts can mimic both spatial and temporal signals |
| Portability | explicit connectivity level/operator/endpoint, source families | cross-source, across-taxon/environment process identification | Tree growth effects are not beetle composition effects |

## Relevant observed forest results (separate, NOT pooled)

**SDMR FIA:** Five previously fixed tree taxa have positive *within-county spatial* stand-basal-area predictive increments under equal-plot weighting: P. strobus +2.503%, A. rubrum +1.095%, Q. alba +0.823%, Q. rubra +1.521%, Q. velutina +0.825%. In the *same* selected survivor cohort, a stricter within-plot observed change comparison retained only 2/5 positive point increments, and 1/5 nominal postfit intervals excluding zero. **Independence limit:** These are repeated plots/trees within one FIA data lineage; not independent samples or evidence of causal crowding.

**Structural Finland:** 142 original field sites, nine geographic cells; including source-measured deadwood VD10 yields +0.00024237 in cell-equal out-of-cell Hellinger² composition error (conditional p=.0150, retrospective). **Structural Germany:** six parent plots in one Steigerwald forest, shade+offered host identity versus shade only improves Hellinger² by +0.019699892; 6/6 plot effects positive (conditional p=.03125). These are not equal endpoints to FIA tree-growth RMSE, and do not establish universal host-resource causality. Original literature had already studied host wood preferences.

**Structural Slovak Carpathians:** 116 original physical plots, 18 source-authored stand clusters, original environment variables complete; organism-response and reliable feeding-guild ontology remain on HOLD. **No new biological effect inferred**.

## Method prototype and known-truth falsification

SDMR development PR [#286](https://github.com/zuizui0223/sdmr/pull/286) contains the cross-endpoint bookkeeping in `src/sdmr/contextual_structure_evidence.py` and a synthetic eight-world benchmark `src/sdmr/structural_known_truth_v1.py`.

Worlds cover true structure, measured site proxy, redundant shared information carrier, outcome-dependent sampling, pure spatial stand association, time-varying structure, endpoint/operator mismatch, and an omitted driver. Burned developer seeds are 1201–1203; prospective ecological conclusions are not licensed. Crucial method contrast: individual-variable add/drop can be zero even with true whole-process carriers, while sample selection can spuriously improve spatial **and temporal** prediction when the true within-site effect is zero.

A future independent method validation must compare:
- declared strong hierarchical/reference models and grouped/conditional variable-importance baselines;
- **all-carrier** process exclusion versus individual-variable exclusion in spatial and same-interval temporal validation;
- explicit observation/selection process adequacy and falsification, rather than relying on p-values or two-learner consensus;
- correct process information on fresh known-truth seeds against false/over-sharp calls;
- later *distinct* external forest cohorts. No historical Structural or FIA response may be reopened and relabeled prospective.

## Adapter requirements (enforce before any response access)

1. **Identity & grain:** original-source archive SHA, physical forest/stand/plot identity; nested traps, sessions, trees, years and multi-guild rows never become independent geographic units.
2. **Response/effort:** exact original sampling dates, methods, effort, true zero-catch/absence frame, survival/harvest/attrition states and organism ontology, with non-estimable as a valid outcome.
3. **Reference & information-carrier registry:** predeclare process taxonomy (e.g. `stand_structure`, `deadwood_amount`, `host_resource_identity`, `thermal`, `moisture`, `site_history`) and many-to-many proxy links; a shared canopy/resource proxy must be removed from *every* declared route for the corresponding process closure.
4. **Holdout & scale:** freeze source-independent region/stand/site/time folds, overlap/positive-support gates, additive loss metric and exact source/response-blind unit fingerprint before outcomes; fit preprocessing only in train blocks.
5. **Interpretation:** separately report variable increment, all-carrier information closure, data adequacy, missingness/observation audit and true out-of-region transfer. Do not infer causal tree competition, resource limitations or cross-forest universality from an observational predictive increment.

## Current handoff

**No request to merge datasets or original empirical effects.** Structural can consume SDMR's typed evidence schema as an optional future adapter after its own response/source gates pass; the immediate handoff is methodology and synthetic tests. The existing Structural forest PR #469 remains draft and its source seals unchanged. A later, independent Structural ecology manuscript remains an orthogonal project, not evidence for SDMR's frozen M5 positive results.
