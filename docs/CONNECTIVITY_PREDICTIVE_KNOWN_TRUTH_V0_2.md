# Connectivity predictive known-truth v0.2

## Question

Does the typed connectivity representation recover held-out information only when its biological operator matches the endpoint-generating process?

## Frozen synthetic design

Each synthetic unit has:

- a local-state reference variable;
- pollen connectivity;
- whole-individual connectivity;
- a collapsed scalar equal to the mean of the two connectivity coordinates.

Two endpoint worlds are generated from the same predictor distribution.

### Pollen endpoint

Outcome = 0.45 × local state + 1.10 × pollen connectivity + bounded noise.

### Whole-individual endpoint

Outcome = 0.45 × local state + 1.10 × whole-individual connectivity + bounded noise.

The deterministic held-out split is fixed before scoring.

Five models are compared:

1. reference only;
2. reference + pollen connectivity;
3. reference + whole-individual connectivity;
4. reference + collapsed mean connectivity;
5. reference + both typed coordinates.

## Pre-result expectations

For each endpoint:

- the matching operator should recover nearly all missing held-out information;
- the mismatched operator should add essentially no held-out information;
- the collapsed scalar may recover some signal because it contains half of the matching coordinate, but should remain clearly inferior to the matching typed coordinate;
- the two-coordinate typed state should perform approximately as well as the matching operator, because the irrelevant operator can receive a near-zero fitted coefficient.

The key falsification is operator reversal:

- pollen should win for the pollen endpoint;
- whole-individual connectivity should win for the whole-individual endpoint.

A universal scalar connectivity interpretation would not predict this reversal.

## Interpretation

v0.1 established that equal collapsed connectivity can conceal different operator-specific transition states.

v0.2 adds held-out prediction: even when a collapsed scalar contains useful information, it is not the same object as the operator-matched connectivity state.

This produces the Structural↔EGWE development sequence:

    scalar insufficiency
        ↓
    typed connectivity
        ↓
    operator-matched held-out gain
        ↓
    operator portability test
        ↓
    residual origin/history test

## Claim boundary

This is a deterministic synthetic known-truth benchmark. It does not show how often these conditions occur in nature, does not identify a real dispersal kernel, and does not add an empirical endpoint to the frozen Structural manuscript.
