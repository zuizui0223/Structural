# Connectivity empirical admission v0.4

## Purpose

v0.4 is the response firewall for any future real-system test of the Structural↔EGWE connectivity framework.

The current Structural manuscript is closed. A new empirical system may enter a future protocol only if the connectivity question can be specified without using the response.

## Mandatory response-blind declarations

Before outcome access, the protocol must fix:

1. system identity and immutable source snapshot;
2. spatial origin/history class;
3. held-out ecological unit;
4. endpoint and scoring metric;
5. current-state/reference model identity;
6. geometry connectivity candidate, if used;
7. biological process operator and its exact semantics, if a process or realized coordinate is used;
8. process-model connectivity candidate, if used;
9. realized-connection coordinate, if used;
10. scale/radius/kernel selection rule;
11. shared-reference dependence;
12. origin/history residual variable, if tested;
13. equivalence margin if a state-adequacy claim is requested.

## Hard STOPs

A candidate stops before outcome access when:

- the response has already been opened;
- the connectivity candidate used outcome information;
- no connectivity coordinate is declared;
- a process/realized coordinate lacks an identified biological operator;
- operator semantics are unspecified;
- source/reference/held-out unit/metric/scale rule are incomplete;
- shared-reference dependence has not been declared;
- a state-adequacy claim is requested without a frozen origin/history variable and equivalence margin.

These are protocol STOPs, not adverse ecological results.

## Geometry-only admission

A geometry-only test may qualify without process semantics, but its claim ceiling is geometry-level structural adequacy only. It cannot later be relabelled as pollen, demographic, genetic or realized movement connectivity after seeing the outcome.

## Process and realized admission

A process-model or realized-connection test must declare what entity moves or couples and at what biological stage. A label such as connectivity, dispersal or gene flow is insufficient by itself.

## State-adequacy admission

A protocol requesting the v0.3 state-adequacy claim must predeclare a smallest meaningful residual-origin effect.

Without that margin, the protocol may still test residual origin/history, but a null result cannot be promoted to state sufficiency.

## Sequence after qualification

    response-blind admission
        → source/schema verification
        → freeze candidate/reference/split/metric
        → one-shot outcome authorization
        → held-out scoring
        → v0.3 ladder interpretation
        → operator portability only if separately tested

No failed or adverse result is repaired and rerun as independent confirmation.
