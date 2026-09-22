# Structural

Standalone repository for the structural/reference-adequacy paper formerly developed inside `zuizui0223/eog`.

## Scientific question

> After a declared reference model has already represented local support, source proximity and generic landscape context, does occurrence-conditioned landscape configuration retain additional held-out information?

## Central claim

Structural information is **reference-conditioned**. An occurrence-conditioned landscape signal can be detectable under a restricted reference yet fail to provide incremental held-out predictive value beyond a richer reference. Structural adequacy must therefore be earned relative to an explicitly declared reference and endpoint.

## Two origins of spatial separation

The paper deliberately spans two different origins of spatial separation:

- **pre-existing isolation** — A-Islands are naturally separated by ocean from the outset;
- **habitat fragmentation** — Tanzania forest fragments represent habitat that is partitioned within a terrestrial matrix.

These origins are not assumed to be biologically equivalent. The shared question is narrower and more general:

> **After the best declared description of the current ecological/geographic state is supplied, does an additional structural representation retain endpoint-relevant held-out information?**

Thus the framework does not require “island isolation” and “fragmentation” to be the same process. It tests whether their different histories leave residual predictive information beyond the state/reference already represented.

This creates a direct conceptual bridge to EGWE: **origin/history should not receive explanatory status merely because it is plausible; it must retain future-relevant information after an adequate current state is supplied.**

## Frozen empirical boundary

- **A-Islands original:** conditional concordance = **0.6177466** across 845 estimable taxa under climatic support + nearest-source conditioning.
- **A-Islands strong reference:** `C - R3 = +0.0034852` log loss, 95% CI **+0.0024664 to +0.0045082**; 341 taxa favourable, 545 adverse. Positive is adverse because lower log loss is better.
- **Tanzania:** adverse primary LOSO increment beyond a matrix-aware strong reference; spatial-block sensitivity remains uncertain.

The original A-Islands endpoint and the strong-reference endpoint are different estimands and must not be pooled as one effect size.

## Separation from EOG-WF

This repository has a **separate empirical denominator** from EOG-WF. Azores yellow eel, Louisiana King Rail, Tampa seagrass, STOC, Glanville and the post-closure NCRN programme are not replications of this paper and are intentionally excluded.

Shared EOG terminology/code provenance does not merge the scientific claims.

## Relationship to EGWE

Structural and EGWE share a higher-level principle: a candidate variable or representation must demonstrate **endpoint-relevant residual information after an explicit reference/state has been supplied**.

- Structural tests this principle for **landscape configuration under pre-existing isolation and habitat fragmentation**.
- EGWE tests it for **future-relevant eco-genetic state, origin/history and process representation**.

EGWE is conceptual/methodological context, not empirical evidence for this manuscript.

## Post-closure connectivity development

The frozen paper remains unchanged. A separate development lane now asks whether connectivity can be promoted from a generic spatial label to a future-relevant typed state.

The v0.1 object is:

    C^(level, operator, endpoint, origin | reference)

The current implementation distinguishes structural geometry, process models and realized observations; keeps pre-existing isolation separate from habitat fragmentation; tests incremental adequacy relative to the declared current state/reference; and treats operator portability as a separate gate.

A constructive known-truth counterexample shows that two states can share the same collapsed mean connectivity while having different operator-specific next-state support. Therefore a single scalar connectivity value is not assumed transition-sufficient.

Canonical development files:

- `docs/CONNECTIVITY_ADEQUACY_V0_1.md`
- `docs/CONNECTIVITY_CROSSWALK_V0_1.md`
- `docs/CONNECTIVITY_PREDICTIVE_KNOWN_TRUTH_V0_2.md`
- `docs/CONNECTIVITY_STATE_LADDER_V0_3.md`
- `docs/CONNECTIVITY_EMPIRICAL_ADMISSION_V0_4.md`
- `docs/CONNECTIVITY_EMPIRICAL_ADMISSION_CLI_V0_5.md`
- `docs/CONNECTIVITY_RETROSPECTIVE_PILOTS_V0_6.md`
- `docs/DAVIS_2026_RETROSPECTIVE_ADAPTER_V0_6.md`
- `docs/DAVIS_SCHEMA_AUDIT_CLI_V0_7.md`
- `docs/FRESH_CONNECTIVITY_CANDIDATE_TRIAGE_V0_8.md`
- `docs/FRESH_CONNECTIVITY_CANDIDATE_TRIAGE_V0_9.md`
- `docs/USGS_METADATA_RESOLUTION_V0_10.md`
- `docs/CONTENT_BLIND_ARCHIVE_INVENTORY_V0_11.md`
- `docs/FILE_ROLE_FIREWALL_V0_12.md`
- `docs/PNW_PHYSICAL_SCHEMA_V0_13.md`
- `docs/TEMPORAL_RESPONSE_FIREWALL_V0_14.md`
- `docs/PNW_TEMPORAL_CONNECTIVITY_PROTOCOL_V0_15.md`
- `docs/PNW_REFERENCE_STATE_V0_16.md`
- `docs/PNW_STAGE1_AUTHORIZATION_V0_17.md`
- `docs/PNW_STAGE1_RESULT_V0_18.md`
- `docs/TRANSITION_PILOT_PROTOCOL_V0_31.md`
- `docs/TRANSITION_PILOT_RUNNER_V0_32.md`
- `docs/CONFIRMATORY_FREEZE_GATE_V0_33.md`
- `docs/STRUCTURAL_EGWE_METHOD_MAINLINE.md`
- `development/connectivity_adequacy_contract_v0_1.json`
- `src/structural/connectivity_adequacy.py`

v0.2 additionally verifies in held-out synthetic prediction that the winning connectivity coordinate reverses when the endpoint-generating operator reverses; a collapsed connectivity scalar recovers only partial information. v0.3 adds the prospective geometry → process model → realized connection → origin/history ladder and permits a state-adequacy claim only when a predeclared equivalence margin is satisfied; non-significance alone is indeterminate. v0.4 adds a response-blind admission firewall: future real systems must freeze source identity, reference, held-out unit, endpoint, operator semantics, connectivity scale rule, shared-reference dependence, and any equivalence margin before outcome access. v0.5 makes that firewall executable as a JSON CLI with distinct qualified / scientific STOP / invalid-schema exit codes. v0.6 adds a permanently separate retrospective engineering lane for public datasets whose outcomes are already exposed; these datasets can exercise adapters and typed-connectivity bookkeeping but can never be promoted to fresh evidence. v0.7 adds a schema-only Davis audit CLI that checks files, headers, identifiers, years and fingerprints while fitting zero models and summarizing zero endpoint values. v0.8 adds metadata-only fresh-candidate triage so datasets are stopped or held pending before any response-value access. The only pristine-fresh candidate is the USGS Rocky Mountain National Park amphibian release (1986–2022). Its physical file/geometry/firewall gate is now resolved response-blindly; the selected transition is 2021→2022 with 92 geometry-valid evaluation sites. Biological protocol freeze is the next gate. The Pacific Northwest montane-pond release (2012–2013) has now resolved its physical schema but is permanently classified as `response_unopened_design_exposed` because the legacy analysis code was inspected before the new connectivity protocol was frozen. v0.10 formalizes that DOI/catalog resolution is not enough: file-level distribution, geometry, and response-firewall verification are separate gates. v0.11 adds a content-blind ZIP/directory inventory that records only paths, extensions, sizes and SHA-256 while keeping semantic/response parse counts at zero. v0.12 pins every file to a SHA-verified role and permits semantic opening only for files explicitly marked safe_schema or metadata; response, code and unknown files remain closed. v0.13 adds a `mixed` file role and a column-level firewall for the PNW master table, freezes a 2012-only baseline geometry for 150 sites observed in both years, and permanently separates PNW from the pristine-fresh lane. v0.14 distinguishes legitimate lagged/current biological state from forbidden future-target leakage: lagged state may open first under a frozen temporal contract, connectivity features are then fingerprinted, and only afterward may the future target open. v0.16 freezes the 2012 response-free 219-site reference state and its SHA-256 before Stage 1 lagged-state access. v0.15 freezes the PNW 2012→2013 Rana cascadae holdout before lagged-state access: a response-independent 250/500/1000/1500/5000 m movement worldset, a fixed R0/R1/R2/C ladder, leave-one-region-out evaluation, and C−R2 as the sole primary contrast. PNW remains permanently `response_unopened_design_exposed`, not pristine fresh evidence. PNW Stage 1 is now complete under the design-exposed evidence class: 2012 RACA state and the complete R0/R1/R2/C feature table are fingerprinted, while every 2013 target value remains sealed. PNW has now closed as terminal non-estimable: after the one-shot 2013 target opening, only 3 negative targets existed among the 150-site universe and every frozen heldout-region training set failed the predeclared negative-class gate, so model fits = 0 and C−R2 has no predictive direction. RMNP is now closed as system-context-exposed terminal non-estimable: 2022 AMMA contains only 3 positive vs 66 negative targets, so every frozen block-training set fails the predeclared positive-class gate and model fits remain zero. The connectivity lane now has two real dynamic attempts and zero scored predictive endpoints: PNW collapsed toward positives (108/3), RMNP toward negatives (3/66). Both terminate at the frozen endpoint-variation gate before fitting, so neither provides favorable or adverse predictive evidence. v0.30 therefore moves future validation upstream: a disjoint burned pilot must first demonstrate that the declared transition/heldout design can produce enough estimable blocks before any fresh confirmatory target is spent. v0.31 now makes the pilot/confirmatory split itself a fingerprinted pre-response object: disjoint partitions, endpoint semantics, heldout design and class/test-row gates must all be frozen before pilot access. v0.32 adds a pilot-only execution firewall: confirmatory rows are forbidden at input, pilot output contains estimability accounting only, and effect/score fields are structurally null. v0.33 then permits only confirmatory-protocol construction after a clean pilot pass; fingerprint mismatch, predictive pilot output, or any confirmatory exposure is a STOP. This development is not an additional empirical endpoint for the current paper.

## Current state

Science and presentation are closed. Remaining work is author/admin/release/live-policy only: author metadata and declarations, tagged release, archived DOI, release-fingerprint replay, and submission-day *Ecological Informatics* checks.

## Provenance

Initial standalone migration source: `zuizui0223/eog@d7d18be0d34ba28065a947df59338e4d660a4b4c`.

The frozen scientific hard stops from the original boundary remain in force. Authoritative A-Islands outcomes must not be rerun, R3 must not be weakened, graph scales/taxa must not be retuned, and no favourable dataset may be added to rescue the result.
