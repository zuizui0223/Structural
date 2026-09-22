# Structural ↔ EGWE methodological mainline

## Core unifying question

Structural and EGWE are linked by a shared inferential problem:

> When systems differ in spatial origin or history, which currently measured state or structural representation is sufficient for the endpoint, and what residual information remains after that representation is supplied?

The common axis is **not fragmentation alone**. Two distinct spatial origins must remain separate:

1. **pre-existing / original isolation** — for example oceanic or continental islands whose separation is part of the biogeographic setting;
2. **habitat fragmentation** — a formerly more continuous habitat or interaction system becomes subdivided.

These histories are not ecologically equivalent and must not be pooled as one treatment. They can, however, be tested with the same adequacy logic.

## Shared adequacy logic

Let:

- `O` = origin/history/context label (e.g. island isolation, recent fragmentation, urbanization);
- `R` or `S` = declared present-day reference/state representation;
- `C` = candidate structural coordinate not yet included in the reference;
- `Y` = held-out endpoint or future state.

The shared test is:

```
origin/history
     ↓
declared present state/reference R or S
     ↓
held-out/future endpoint Y
     ↓
does C or origin/history retain residual information?
```

### Outcome A — residual information remains

If a structural coordinate or origin/history still improves held-out prediction after the declared state/reference is supplied, the current representation is **incomplete for that endpoint**.

Interpretation:

- search for a missing process coordinate, memory term, cohort, source configuration, alignment, or connectivity representation;
- do not conclude automatically that the residual variable is causal;
- do not promote a habitat/origin label to a mechanistic state merely because it predicts.

### Outcome B — residual information disappears

If origin/history or the candidate structural coordinate adds no held-out information, the supplied state/reference is **adequate relative to that endpoint and comparison**.

Interpretation:

- this does not make the origin/history biologically irrelevant;
- it means the currently measured state has absorbed the endpoint-relevant information carried by that label under the declared test;
- adequacy is endpoint- and reference-specific, never universal.

## Structural role

Structural asks the spatial version:

> After a declared reference has already represented local support, source proximity and generic landscape context, does occurrence-conditioned configuration retain additional held-out information?

Its empirical systems deliberately span two spatial origins:

### A-Islands — original biogeographic isolation

The islands are not treated as fragments of a recently continuous habitat.

The original benchmark found conditional structural ordering beyond climatic support and nearest-source distance.

The prospectively frozen strong-reference test then asked whether species-conditioned EOG connected frequency added predictive information beyond a richer island reference R3.

It did not: the mean `C - R3` log-loss increment was adverse.

This is a test of **reference-conditioned structural adequacy under long-standing island isolation**.

### Tanzania — habitat fragmentation

The forest-fragment system represents a different spatial origin.

The strong reference already contained patch area, training-selected matrix-aware current flow, their interaction and nearest source distance.

Adding EOG was adverse in the primary LOSO analysis, while the spatial-block sensitivity was uncertain.

This is a test of **reference-conditioned structural adequacy under fragmented terrestrial habitat**.

The two systems therefore support a shared method without implying a shared fragmentation mechanism.

## EGWE role

EGWE asks the dynamic state version:

> After a candidate eco-genetic state is supplied, does origin/history still improve prediction of future fate?

The EGWE sequence is:

```
candidate-state adequacy
        ↓
residual origin / history test
        ↓
only then: cross-system regime comparison
```

This is the dynamic analogue of Structural's declared-reference test.

Structural asks whether a spatial representation adds information beyond `R`.

EGWE asks whether origin/history adds information beyond `S`.

Both reject the assumption that a biologically plausible label or statistic is automatically an adequate state variable.

## The combined methodological spine

```
SPATIAL ORIGIN / HISTORY
    ├── original isolation
    │     islands / archipelagos
    └── habitat fragmentation
          forest fragments / urban fragments / other subdivisions
                    ↓
DECLARE PRESENT REPRESENTATION
    Structural: R = ecological + geographic reference
    EGWE:       S = candidate future-relevant state
                    ↓
HELD-OUT / FUTURE TEST
                    ↓
RESIDUAL INFORMATION?
    yes → representation incomplete
          search for missing coordinate / memory / process
    no  → representation adequate for this endpoint/reference
                    ↓
ONLY THEN
compare systems, origins or regimes
```

## Connectivity-aware development

The shared method now treats connectivity as a **typed state candidate**, not a scalar label.

The active post-closure object is:

    C^(level, operator, endpoint, origin | reference)

with four explicit axes:

- **level** — structural geometry / process model / realized observation;
- **operator** — what actually propagates (for example pollen, whole individuals, alleles, demographic recolonisation, interaction continuity);
- **endpoint** — which held-out or future quantity the coordinate is supposed to inform;
- **origin** — pre-existing isolation, habitat fragmentation, or another spatial history.

The adequacy sequence becomes:

    spatial origin/history
            ↓
    declared current state/reference R or S
            ↓
    typed connectivity C^(level, operator, endpoint, origin | reference)
            ↓
    held-out/future endpoint Y
            ↓
    does C retain residual endpoint-relevant information?
            ↓
    if yes: candidate state remains incomplete without C
    if no: C is redundant/adverse/indeterminate for this endpoint
            ↓
    only then: test operator portability

This adds a second test beyond ordinary structural adequacy.

### Adequacy is not portability

A connectivity coordinate may be useful for one operator and fail for another.

Therefore:

- success under pollen flow does not establish whole-individual movement connectivity;
- success under gene-flow representation does not establish demographic recolonisation;
- success of structural geometry does not identify a process-specific movement probability;
- a shared scalar value does not establish state equivalence.

A portability claim must be earned independently across the declared operator set. Shared-reference substitutions are legitimate operator tests but do not become independent baseline replications merely because the operator changes.

### Constructive scalar-insufficiency result

The v0.1 synthetic known-truth fixture contains two states:

- state A: pollen connectivity 0.9, whole-individual connectivity 0.1;
- state B: pollen connectivity 0.1, whole-individual connectivity 0.9.

Both collapse to the same scalar mean connectivity of 0.5.

Under a declared pollen-specific transition, however, the next-state support differs by 0.8.

Thus a universal scalar connectivity summary is not transition-sufficient for that declared operator. This is a constructive software/representation result only; it is not a natural prevalence claim.


### Operator-matched predictive known-truth

v0.2 adds a held-out predictive test. The same synthetic predictor distribution is scored under two known-truth endpoints:

- pollen endpoint: future outcome depends on pollen connectivity;
- whole-individual endpoint: future outcome depends on whole-individual connectivity.

The operator-matched coordinate recovers more than 0.10 MSE relative to the local-state reference in both endpoint worlds, while the mismatched operator changes held-out MSE by less than 0.001. The collapsed mean-connectivity scalar recovers only part of the missing information. A typed two-operator state performs approximately as well as the matching coordinate because the irrelevant operator receives negligible fitted weight.

The winning coordinate therefore reverses when endpoint truth reverses. This is the required synthetic behavior before any future empirical portability claim is admitted.

### State closure requires equivalence, not a null

v0.3 extends the sequence beyond operator-matched prediction:

    structural geometry
        → process-model connectivity
        → realized connection
        → residual origin/history test

A residual origin/history coefficient that merely fails to exclude zero does **not** establish that the present state is sufficient.

A state-adequacy claim is allowed only when the origin/history confidence interval lies completely inside a smallest-meaningful-effect margin frozen before outcome access.

Therefore the final gate has three distinct non-positive outcomes:

- residual origin/history **earned** → current state remains incomplete or history proxies a missing coordinate;
- residual origin/history **indeterminate** → no closure claim;
- residual origin/history inside the predeclared equivalence margin → **state adequacy earned for this endpoint/reference only**.

This keeps the Structural framework aligned with EGWE's precision-bounded null logic.

### Relationship to the frozen Structural paper

The frozen EOG connected-frequency term is retained as **structural_geometry**. It summarizes scenario-robust occurrence-anchored configuration and is not retroactively interpreted as demographic movement, pollen flow, gene flow, or realized dispersal.

The next development question is not whether to rescue the frozen A-Islands or Tanzania outcomes. It is whether future systems with process-identified connectivity can distinguish:

1. geometry-only residual information;
2. process-model residual information;
3. realized-connection residual information;
4. operator portability across endpoints and histories.

## Prospective empirical admission

The connectivity programme now has a response firewall before any new real-system validation.

A candidate system may proceed only after outcome-blind freezing of:

- source snapshot identity;
- spatial origin/history;
- held-out ecological unit;
- endpoint and metric;
- present-state/reference model;
- geometry coordinate;
- biological operator and exact process semantics for process/realized connectivity;
- process-model and/or realized connectivity coordinate;
- scale/radius/kernel selection rule;
- shared-reference dependence;
- residual origin/history variable;
- equivalence margin when state adequacy is requested.

If the response has already been opened, the candidate connectivity was response-derived, or the biological operator cannot be specified, the system stops before scoring.

These STOPs are protocol-integrity evidence, not ecological nulls.

The active development sequence is therefore:

    scalar insufficiency (v0.1)
        → operator-matched held-out prediction (v0.2)
        → state/reference ladder with equivalence closure (v0.3)
        → response-blind real-system admission (v0.4)
        → executable protocol qualification (v0.5)
        → retrospective adapter pilots kept permanently non-fresh (v0.6)
        → schema-only adapter audit before retrospective fitting (v0.7)
        → metadata-only fresh candidate triage (v0.8)
        → longitudinal fresh-candidate prioritization (v0.9)
        → file-level physical-schema resolution (v0.10)
        → content-blind archive inventory (v0.11)
        → SHA-pinned file-role firewall (v0.12)
        → future empirical scoring only after qualification

## Retrospective engineering lane

Published systems whose outcomes are already visible are not discarded, but they are assigned a different evidence role.

They may be used to:

- exercise source and schema adapters;
- test whether structural, process-model and downstream genetic objects can be typed without ambiguity;
- verify ecological-unit joins and repeated-measure structure;
- replay the state ladder as software/inference engineering.

They may **not** be used to:

- count as fresh confirmation;
- change the frozen Structural paper;
- tune a candidate and later re-label it as prospective;
- select favorable operators for a confirmatory portability claim.

The primary v0.6 engineering pilot is the 2026 Heliconia tortuosa dataset, which contains landscape structure, hummingbird-movement-informed connectivity and contemporary pollen-mediated genetic endpoints in the same fragmented tropical landscapes. Because its publication already exposes the biological result, it is permanently marked `counts_as_fresh_evidence=false`.

## Fresh-candidate discovery boundary

The project now distinguishes candidate discovery from protocol admission.

Fresh candidates are screened using metadata only. A candidate advances only when source identity, ecological units, reproducible geometry, response firewalling, temporal design and operator semantics can be established without opening response values or inspecting a published connectivity result.

If the project sees the response result during discovery, the candidate is permanently removed from the fresh lane. It may still be used as a retrospective engineering system.

The priority-1 fresh candidate is now the USGS Rocky Mountain National Park amphibian release (1986–2022). It is **pending**, not qualified. Public metadata establish a long repeated occupancy design, but the physical release must still verify per-waterbody geometry and response firewalling before feature/split freezing. The Pacific Northwest montane-pond release (2012–2013) remains a priority-2 pending candidate.

## Physical-schema boundary

A DOI, landing page, catalog spatial extent or metadata XML is not sufficient to qualify a connectivity candidate.

Before protocol freeze, the project must physically verify:

- the actual file inventory;
- the ecological-unit geometry or coordinate key;
- the response firewall;
- all joins needed to construct geometry/reference features without reading response values.

The user-supplied Pacific Northwest USGS XML resolves the DOI landing and original metadata but does not expose file-level data URLs on the catalog surface. The candidate therefore remains pending.

Rocky Mountain NP also remains pending because the current access path resolves the catalog metadata but not the underlying ScienceBase file inventory.

These are access/schema boundaries, not ecological nulls.

## Content-blind physical inventory

Once archive bytes are available, the first allowed operation is v0.11 inventory.

The tool may record only:

- relative file path;
- file extension;
- file size;
- SHA-256.

It may hash opaque bytes but may not decode text, inspect table headers, summarize response values or fit a model.

This creates an immutable source snapshot before files are assigned to safe-schema / response / unknown roles.

## File-role firewall

After the opaque v0.11 inventory, every physical file must be assigned exactly one SHA-pinned role.

Only `safe_schema` and `metadata` may be semantically opened before protocol freeze.

`response`, `code`, and `unknown` remain closed. Code is deliberately closed by default because original scripts may reveal response definitions, tuned scales, candidate rankings or other post-outcome decisions.

This makes the response firewall a property of the immutable file snapshot rather than a naming convention.

## PNW physical-schema resolution and evidence-class downgrade

The uploaded Pacific Northwest package resolves the physical geometry and response-firewall questions.

The master table contains 275 unique sites and 425 site-year combinations. Exactly 150 sites occur in both 2012 and 2013. For those sites, the connectivity geometry is frozen to the median 2012 UTM coordinate per site under NAD83 / UTM Zone 10. This predictor-time rule avoids repairing or using inconsistent 2013 coordinates.

Because the master CSV mixes geometry and focal response values, it is assigned a `mixed` file role. Only a SHA-pinned ten-column geometry/identifier allowlist may be projected before response authorization; focal species/life-stage/observation columns remain protected.

However, the legacy R analysis code was semantically inspected before this new protocol was frozen. That design exposure means PNW is permanently classified as:

`response_unopened_design_exposed`

rather than pristine fresh evidence.

PNW can still support a strong prospective-like response holdout, but it may not enter the pristine fresh denominator and legacy code may not justify species, reference-covariate, or dispersal-scale choices.

Rocky Mountain NP remains the only current pristine-fresh candidate.

## Temporal state is not future-target leakage

For dynamic connectivity questions, a response-like variable can be legitimate predictor state when it occurs **before** the target.

The v0.14 contract therefore separates:

1. lagged/current state opening;
2. source-conditioned connectivity construction;
3. feature fingerprint freeze;
4. future-target opening.

A 2012 occupied pond may therefore act as a 2012 source anchor for a 2013 forecast after Stage 1 authorization. The 2013 target may never inform source anchors, scale selection, reference variables, feature construction or splits.

This distinction is essential for the Structural↔EGWE idea: current biological state is part of the state representation; future state is the prediction target.

## Frozen PNW dynamic connectivity test

v0.15 freezes the first real dynamic test before opening the 2012 lagged biological state.

The taxon is **Rana cascadae** and the biological operator is whole-individual dispersal among breeding ponds. The movement worldset is fixed response-independently at 250, 500, 1000, 1500 and 5000 m; no scale is selected from the PNW responses.

The 2012→2013 ladder is:

    R0 = 2012 target-site state
        ↓
    R1 = R0 + frozen local pond state
        ↓
    R2 = R1 + generic 2012 pond geometry
        ↓
    C  = R2 + 2012 occupied-source connectivity
        ↓
    2013 observed site-use target

The sole primary contrast is **C − R2** under leave-one-2012-region-out scoring. Thus the test asks whether occurrence-conditioned source connectivity contains held-out information beyond current state, local habitat and generic pond geometry.

The protocol is a real response holdout but remains `response_unopened_design_exposed`; it cannot become pristine fresh evidence regardless of result. Rocky Mountain NP remains the pristine-fresh lane.

## Frozen PNW pre-response reference

v0.16 freezes the response-free 2012 reference before any RACA state is opened.

The 2012 safe projection contains 219 sites; 150 of them also occur in 2013 and define the evaluation-site universe before endpoint applicability is known. Numeric site variables are aggregated as the median of distinct nonmissing values so biological row multiplicity cannot weight the physical/current-state reference.

The derived 219-site table is frozen by SHA-256 `13277413ee5d4c9c30d4d8f9cb900203a92e129ccbc5ad4b6b0593dee0bbcdfd`.

Among the 150 common sites, only one frozen R1 numeric value is missing (maxdepth at Deerheart.LakeMUL9). It remains in the cohort and will follow the already-frozen training-fold median + missingness-indicator rule.

No species, observation or future-target value was used. The next irreversible gate is Stage 1 authorization for 2012 lagged RACA state only.

## PNW Stage 1 complete

The design-exposed PNW lane has now completed its first irreversible biological-state opening.

Only 2012 RACA lagged state was opened. The frozen 2012 source state contains 134 positive, 19 negative and 66 non-estimable sites among 219 source ponds. The 150-site 2012→2013 evaluation universe contains 113 positive, 12 negative and 25 non-estimable lagged states.

The occupied-source set is fixed at 134 sites. The complete 150-row R0/R1/R2/C feature table is frozen by SHA-256 `f2e85764d736ee069c5805e6a808b7e434bbb2930cfa0808e7ff723927af4ce6`.

The raw-table normalization required one explicit post-authorization adjudication: valid surveys are `full/partial`, `dry` is excluded, and missing RACA site×species rows are zero-filled on valid visits following source metadata/source-processing semantics. This is recorded as a caveat and does not raise the PNW evidence class.

All 2013 response values remain sealed. Stage 2 is not allowed until the Stage 1 receipt is merged and CI-green.

## PNW terminal result

PNW has completed the full two-stage access sequence and is now closed.

The one-shot 2013 target contains 117 positive, 3 negative and 30 non-estimable sites in the frozen 150-site feature universe. After requiring an estimable 2012 lagged state, 111 sites remain: 108 positive and 3 negative.

Every frozen leave-one-region-out training set therefore has only 2–3 negative targets, below the predeclared minimum of five. DaggerTwisp and Hwy20 additionally contain no applicable heldout target rows.

Consequences:

- estimable regions = 0 / 10;
- R0 fits = 0;
- R1 fits = 0;
- R2 fits = 0;
- C fits = 0;
- primary C−R2 = non-estimable.

This is not adverse evidence for connectivity. It is a target-variation/estimability boundary.

No gate lowering, species swap, endpoint swap, split change or replacement-candidate rescue is allowed for PNW.

The only pristine-fresh active lane is now Rocky Mountain National Park.

## RMNP physical-schema resolution

The RMNP source package is now physically resolved without opening amphibian response values.

The selected dynamic transition is **2021→2022**. It is the only audited large transition that satisfies the response-independent geometry rule: at least 80 common sites, at least 95% source-year coordinate coverage, at least 95% explicit NAD27/NAD83 datum coverage, and UTM Zone 13.

There are 93 common sites; 92 have convertible 2021 geometry. Coordinates are converted to NAD83 / UTM 13N and collapsed to the median transformed 2021 coordinate per site. 2022 geometry is forbidden for predictor construction.

Safe survey-effort metadata identify 70 sites with at least one 100% survey in both years; 69 of those also have valid source geometry. This 69-site universe is the current response-independent high-effort candidate set.

The fresh-evidence class has been downgraded from pristine. External literature triage exposed prior RMNP occupancy/connectivity results for PSMA and LISY, so those taxa are permanently STOP for this lane. No RMNP-specific AMMA response direction has been inspected. The remaining focal class is therefore:

`focal_response_unseen_system_context_exposed`

The source metadata contain conflicting tiger-salamander nomenclature, but the current USGS data-release page for DOI `10.5066/P9EX70L7` identifies the tiger salamander as *Ambystoma mavortium*. The protocol binds the physical token `AMMA` to that current release identity while retaining the nomenclatural caveat.

## RMNP terminal result and empirical denominator closure

The focal-response-unseen RMNP AMMA lane has completed its full two-stage response firewall and is now closed.

The 2022 target contains 3 positive and 66 negative sites across the frozen 69-site evaluation universe. Every leave-one-15-km-block-out training set therefore contains only 1–3 positives, below the predeclared minimum of five. No R0/R1/R2/C model is fitted.

This is the opposite class-collapse direction from PNW:

- PNW joint target: 108 positive / 3 negative;
- RMNP target: 3 positive / 66 negative.

Both systems reached a fully frozen feature surface, then failed the same endpoint-transition estimability principle before any predictive comparison.

The current empirical denominator therefore closes at:

- real dynamic systems attempted: 2;
- scored predictive endpoints: 0;
- favorable predictive endpoints: 0;
- adverse predictive endpoints: 0;
- terminal non-estimable endpoints: 2.

No replacement dataset may be selected as a rescue for either system.

The next valid development object is **endpoint-transition estimability** itself: before spending a fresh response, a future protocol must establish response-blind evidence that the proposed future transition can plausibly yield sufficient class/event variation for the declared heldout design, without using the focal response values to tune the endpoint.

## Endpoint-transition estimability becomes the next gate

After PNW and RMNP, the next development target is not another connectivity metric and not another opportunistically chosen dataset.

A future binary dynamic endpoint must first pass a **burned pilot**:

1. pilot and confirmatory partitions are frozen before pilot response access;
2. one endpoint definition and one heldout design are frozen;
3. pilot response is opened and permanently excluded from confirmation;
4. the exact planned test-row and training-class gates are applied to the pilot;
5. only if enough pilot blocks are estimable may a new confirmatory protocol be frozen.

A pilot pass is not predictive evidence. A pilot failure consumes that endpoint/version and cannot be repaired by lowering gates or swapping targets.

This adds a new prerequisite to the Structural↔EGWE spine:

    physical/state adequacy
        → endpoint-transition estimability
        → typed connectivity adequacy
        → operator portability
        → residual origin/history

The future target must first generate an estimable loss before any state-sufficiency claim is meaningful.

## Burned-pilot partition freeze

v0.31 makes the v0.30 estimability principle operational.

Before any pilot response is opened, a future protocol must freeze:

- the biological system;
- the partition axis;
- a nonempty burned pilot partition;
- a disjoint confirmatory partition;
- one endpoint definition;
- one heldout design;
- the exact minimum test-row / training-positive / training-negative / estimable-block gates.

The complete object is canonically fingerprinted. Any later change to the partition, endpoint semantics or gates creates a new protocol identity.

The pilot may only establish transition feasibility. It never estimates the connectivity effect and never enters the predictive denominator.

A pilot pass still does not authorize confirmatory response access; it only permits a separate confirmatory protocol to be frozen.

## Why the distinction matters

A label such as `island`, `fragmented`, `urban`, `F_ST`, `distance`, or `connectivity` is not granted mechanistic state status by name.

The same visible spatial separation can arise through different histories, and different histories can converge on a similar present state.

Conversely, systems with similar coarse labels can retain different hidden state because of source configuration, cross-layer alignment, cohort memory, interaction structure or other unmeasured coordinates.

Therefore the programme-level principle is:

> **Spatial origin tells us how a system came to be separated; state/reference adequacy tells us whether the present representation contains the information needed for the endpoint.**

## Relationship to island and izu-core

This Structural ↔ EGWE line is the methodological spine.

The `island → izu-core` line is a biological application spine:

- `island`: which floral/reproductive responses recur globally under island isolation?
- `izu-core`: why can a recurrent broad pressure generate different detailed response branches?

These are complementary but should not be merged into the Structural/EGWE empirical denominator.

## Claim boundary

Do not claim that:

- original island isolation and habitat fragmentation are the same process;
- disappearance of residual origin information proves history is biologically irrelevant;
- residual origin information proves a causal effect of origin;
- Structural A-Islands and Tanzania estimate one common fragmentation effect;
- EGWE results are empirical replications of the Structural paper;
- Structural results validate the EGWE state representation;
- one universal state representation is sufficient for all endpoints or systems.

The shared contribution is the **adequacy test itself**: a representation earns scientific status by preserving endpoint-relevant information, not by being plausible, familiar, or spatially intuitive.
