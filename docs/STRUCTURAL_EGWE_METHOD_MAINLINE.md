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
        → future empirical scoring only after qualification

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
