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

**Structural Slovak Carpathians:** 116 original physical plots, 18 source-authored stands; a separately frozen one-pass exploratory **Weiss170 trophic-guild** deadwood prediction was actually executed and **NOT SUPPORTED** (stand-equal ΔHellinger² = −0.00106793, conditional p = 0.1121). The original exact-name guild admission remains HOLD: 170/309 matched taxa relied on an exploratory post-header underscore-format sensitivity; stand nesting within nine ranges and complete observation/zero frame remain unresolved. This result is **not** a strict replication or contradiction of the Finnish Host_tree-guild positive because endpoints, guild ontologies and references differ. [Original result](https://github.com/zuizui0223/Structural/blob/analysis/forest-macro-plot-environment/docs/FOREST_MACRO_CARPATHIAN116_WEISS170_GUILD_DEADWOOD_LOSO_ONEPASS_ACTUAL_RESULT_20261118.md).

**Structural England NFI2026:** original canopy/Malaise sampling metadata yielded 83 candidate plot-years and 77 sequenced matched pairs, but the frozen region×year label exchangeability required for its stated endpoint fails due to singleton strata. Original OTU data rows were **not** opened for that test; this is a **scientific estimability STOP**, not zero community information. [Source/OTU header gate](https://github.com/zuizui0223/Structural/blob/analysis/forest-macro-plot-environment/docs/FOREST_NFI_ENGLAND_2026_OTU_EXACT_JOIN_AND_REGIONYEAR_GATE_ACTUAL_RESULT_20261119.md).

**New SDMR forest-source admission interface:** [source-only five-lineage contract](https://github.com/zuizui0223/sdmr/blob/method/structural-context-closure-v1-20261118/docs/SDMR_STRUCTURAL_FOREST_SOURCE_GATE_V1.md) audits verified physical sampling frames, independent blocks, taxon ontology, detection effort, survivor attrition, and prior biological outcome exposure without fitting models. This is a stricter *new study* admission rule and must not retroactively reclassify historical Structural outcomes.

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


## New SDMR synthetic prospective method evidence (independent of forest sources)

The separately source-locked **2026-11-19** SDMR known-truth programme opened unused seeds 96001–96010 across eight fixed synthetic worlds (80 cases). Its prespecified all-carrier plus source-audit rule recovered **30/30** known-positive process-information targets, with **0/50** false favorable calls in null/unsafe targets. The single-variable spatial comparator recovered 20/30 with 29/50 false calls; all-carrier without the observation-quality gate recovered 30/30 but retained 4/50 false calls. Selection-confounded 10/10 remained unresolved, omitted-driver 10/10 unavailable, shared-carrier 10/10 recovered. All registered gates passed.

[Original single opening](https://github.com/zuizui0223/sdmr/actions/runs/44432358638) and [independent saved-score no-refit audit](https://github.com/zuizui0223/sdmr/actions/runs/44432841484), with exact digests and limitations in [SDMR's terminal record](https://github.com/zuizui0223/sdmr/blob/method/structural-context-closure-v1-20261118/docs/SDMR_STRUCTURAL_KT_PROSPECTIVE_V1_TERMINAL.md).

**Do not convert this to Structural biology confirmation.** The synthetic generator supplies its own observation-selection quality indicator; this is not a learned unknown-bias detector. Strong performance across random draws from the same predeclared eight world families does not prove species, biome, movement-operator or data-source portability. The connection to Structural is a **method interface to test**, not a pooled ecological effect or permission to open its old sealed responses.

## Current handoff

**No request to merge datasets or original empirical effects.** Structural can consume SDMR's typed evidence schema as an optional future adapter after its own response/source gates pass; the immediate handoff is methodology and synthetic tests. The existing Structural forest PR #469 remains draft and its source seals unchanged. A later, independent Structural ecology manuscript remains an orthogonal project, not evidence for SDMR's frozen M5 positive results.
