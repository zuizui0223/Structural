# Connectivity adequacy v0.1 — post-closure development contract

## Status

Exploratory post-closure development only. This line does not reopen, retune, or reinterpret the frozen Structural manuscript.

Frozen paper evidence remains the A-Islands original conditional-ordering result, the A-Islands strong-reference C - R3 result, and the Tanzania strong-reference result with its spatial-block sensitivity.

## Why connectivity needs a new representation

The Structural paper established that a graph-derived structural coordinate earns scientific value only relative to a declared reference and endpoint.

EGWE adds a second boundary: a shared connectivity label does not identify a transportable biological operator. Allele mixing, whole-individual movement, pollen flow, demographic recolonisation, and interaction continuity act on different entities and life-cycle stages.

The next Structural development therefore rejects a single universal connectivity scalar.

The working object is:

    C^(level, operator, endpoint, origin | reference)

where level distinguishes structural geometry, a process model, or a realized observation; operator identifies the biological process represented by connectivity; endpoint identifies the held-out/future quantity being scored; origin records whether spatial separation is pre-existing isolation, habitat fragmentation, or another history; and reference is the already-supplied ecological/geographic state against which residual value is tested.

## Core question

> After the current state/reference is supplied, does a process-typed connectivity coordinate retain endpoint-relevant held-out information, and does that result transport to another operator?

This creates two distinct gates.

### Gate A — adequacy

For a frozen reference R and typed connectivity coordinate C^p:

    Delta_p = score(R + C^p) - score(R)

For loss metrics, negative is favorable.

The coordinate is earned when its frozen interval is wholly favorable, adverse when its frozen interval is wholly unfavorable, and indeterminate when the interval crosses the null. This is a reference- and endpoint-specific statement, not a causal label.

### Gate B — operator portability

A result for C^p does not automatically become a result for C^q.

Portability across a declared operator set requires each target operator to earn incremental information under its own held-out test.

- any adverse operator -> not portable in the declared set;
- any indeterminate operator -> portability not established;
- all operators earned -> supported within the declared operator set.

Even then, the claim is finite. It is not universal connectivity equivalence.

Shared-reference substitutions are permitted as operator tests, but they must be marked as sharing a reference and must not be counted as independent baseline replications.

## Spatial-origin axis

The same audit logic is allowed across different origins without equating their histories.

### Pre-existing isolation

Example class: oceanic or continental islands. The question is whether current source configuration, stepping-stone structure, and process-typed connectivity retain information after the declared island reference.

### Habitat fragmentation

Example class: forest or urban fragments. The question is whether matrix/process-specific connectivity retains information after current patch state, source proximity, and other declared present-state variables are supplied.

The method compares adequacy logic, not a common biological fragmentation effect.

## Connectivity representation levels

Three levels are kept distinct:

1. **structural_geometry** — adjacency, source network position, stepping-stone configuration, graph connectedness or other geometry-derived structure without a declared biological transport operator;
2. **process_model** — resistance/current-flow, dispersal kernel, pollen-flow model or another representation that declares what biological entity/process is propagated;
3. **realized_observation** — observed movement, pedigree/gene-flow, pollen transfer, recolonisation or another directly measured realized connection.

Moving upward in this list does not automatically mean "better". Each level must still earn endpoint-relevant information relative to the declared reference.

The frozen Structural paper's EOG connected frequency remains a **structural_geometry** object. It must not be retroactively relabelled as realized movement or a process-specific probability.

## Development objects

v0.1 introduces ConnectivityCoordinate, ConnectivityEvidenceLevel, IncrementalEvidence, classify_incremental, and audit_portability. These objects force operator, endpoint, origin, reference, evidence-family identity, and shared-reference dependence to remain explicit.

## Synthetic known-truth role

Synthetic fixtures only test software semantics: one matched operator can earn information while another operator is indeterminate or adverse, so a scalar label fails portability even when one operator succeeds. This is not ecological prevalence evidence.

## Future empirical admission rule

A real connectivity test may enter a future protocol only if, before outcome access, origin/history class, endpoint, operator semantics, reference/state variables, candidate connectivity representation, held-out ecological unit, metric, and shared-reference dependence are frozen.

Post-outcome operator relabeling, scale retuning, and candidate swapping are forbidden.

## Relationship to Structural and EGWE

    Structural: reference-conditioned residual spatial information
        +
    EGWE: operator-specific future-relevant state
        =
    typed connectivity adequacy

The combined principle is:

> Connectivity is not a state variable by name. It earns state status only for a declared biological operator and endpoint after the relevant present-state reference has been supplied.

## Non-claims

v0.1 does not claim one operator is universally best, island isolation and habitat fragmentation are the same process, a structural graph is a movement probability, predictive gain proves mechanism, transport across two operators implies universal transport, EGWE is an empirical replication of Structural, or the frozen Structural manuscript needs another endpoint.
