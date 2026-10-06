# Boreal birds topology-sensitivity replication v1.162

## Why this route exists

The completed 19-island boreal beetle primary asked a broad question: does graph-path occupied-source information improve held-out occurrence prediction beyond a strong Euclidean/source-aware reference?

It did not.

That result is final and is not reopened here.

The global mammal work subsequently yielded a narrower hypothesis: exact topology may become informative specifically when few source populations remain and their spatial contributions are heterogeneous. The bird matrix from the same boreal study was registered prospectively as a secondary taxon but has no scoring/execution record in Structural.

This creates a clean **same-geography, different-taxon mechanism replication**.

It is not:
- a rerun of the beetle primary;
- geographically independent replication;
- temporal validation;
- a management-effect test;
- an eBird route.

## Frozen geography

The route reuses only response-independent objects that predate any bird response access:

- 19 exact island coordinates;
- the fixed 6-pilot / 13-confirmatory island split;
- the fixed state reference;
- the actual minimal connected symmetrized kNN source graph;
- the frozen graph kernel scale.

The six pilot islands are DN, FD, HU, IL, IS and PP.

## New response-independent null

Before opening any bird value, v1.162 freezes 20 connected rewired graphs.

Each null:
- has the exact actual-graph degree sequence;
- has exactly 35 edges;
- preserves the actual graph's geographic edge-length quintile counts exactly (7 edges in each quintile);
- is produced by 100 accepted degree-preserving double-edge swaps;
- is distinct from the actual graph and from all other nulls.

Only candidate-C graph-path source features change across nulls.

R0-R3, Euclidean source features and generic actual-graph context remain fixed.

## Sparse-source sensitivity

For target island i, let the six frozen pilot islands be the possible sources. With actual-graph kernel weights w_ij:

H_i = Var(w_ij) / Mean(w_ij)^2.

After the one burned bird pilot, let n_s be the number of occupied pilot islands for species s. For 2 <= n_s <= 6:

S_i(n_s) = [(6-n_s)/(5 n_s)] H_i.

n=1 is excluded prospectively because focal exclusion would leave no source on the species' sole occupied training row. n=0 is source-inestimable.

The finite-source identity predicts that relative sensitivity to *which* sources are occupied rises as n falls whenever source weights are heterogeneous.

## Confirmatory prediction

After the bird pilot passes an estimability-only gate, but before any confirmatory bird response opens:

1. fit R3 on bird pilot rows;
2. fit actual-topology C;
3. fit 20 null-topology C models under the identical response and fitting rules;
4. freeze all confirmatory probabilities;
5. freeze S_i(n_s) for every eligible species x confirmatory island.

For a held-out positive cell define:

Delta = logloss(actual C) - mean(logloss(null C_1 ... null C_20)).

Negative Delta means the observed topology assigns more probability to the realized presence than the matched rewired ensemble.

The primary prediction is:

> **as pre-response S_i(n_s) increases, Delta becomes more negative.**

The exact primary is the standardized-S coefficient from

Delta ~ confirmatory spatial-block fixed effects + standardized S

among positive held-out cells.

Support requires a negative point estimate and a 10,000-replicate frozen spatial-block bootstrap 95% upper bound below zero.

## Why this differs from the beetle primary

The beetle primary averaged C-R3 across the full held-out target surface.

v1.162 instead predicts **where topology should matter**.

Therefore a null overall beetle average and a supported bird sensitivity gradient are logically compatible. The bird test cannot change the beetle primary status.

## Claim boundary

Even if supported, this would show only that a theoretical topology-sensitivity predictor transfers to another taxon under the same 19-island geography.

It would not establish:
- geographic generality;
- realized dispersal paths;
- colonization or rescue;
- future demographic consequence;
- source-priority management value.

BALA remains the independent temporal boundary, and its source-loss leverage primary remains non-supportive.
