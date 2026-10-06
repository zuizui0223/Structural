# SW Finland future-outcome protocol v1.175

This contract closes the remaining analytical freedom before any future
colonization value is opened.

The route is conditional on successful response-independent source recovery and
topology freeze. If v1.173.4, v1.174.2 or v1.172 fails, v1.175 cannot execute.

## Missing predictors

The original study reports extensive missing plant-trait data. We therefore do
not permit an outcome-dependent complete-case analysis.

Before pilot-outcome access, over the complete frozen eligible t0 predictor
surface:

- numeric missing values are replaced by the population median and accompanied
  by a missingness indicator;
- categorical missing values become an explicit __MISSING__ level;
- all category levels, medians, means and population SDs are frozen;
- zero-variance numeric predictors are dropped without reference to outcome.

## Reference ladder

R0 contains recipient habitat/environment, plant traits and Gowdis pair state.
R1 adds broad coordinates and surrounding-land buffers. R2 adds generic actual
graph context. R3 adds exact historical source count, nearest Euclidean source
distance and diffuse Euclidean source pressure. C adds only nearest graph-path
source distance and graph-path source pressure.

Actual C and every rewired-null C share the identical R3 design. Rewiring is
allowed to change only the two C source-path features.

## Outcome sequence

Pilot future outcomes are opened once, for frozen pilot-block eligible event
keys only. They fit the frozen models and freeze all confirmatory predictions.
Pilot effects are not evidence.

Confirmatory outcomes are then opened once for the already frozen prediction
keys. No model or probability may be changed afterward.

## Primary

The primary is successful colonization, the temporal analogue of the
presence-focused ultrarare mammal endpoint.

P1 asks whether actual graph-path source information improves prediction beyond
the strong Euclidean/source-aware R3 reference.

P2 asks whether the actual island graph outperforms the mean of 20 matched
rewired topologies.

Both must have a negative point estimate and a negative 95% spatial-block
bootstrap upper bound. Neither can rescue the other.

The response-free finite-source sensitivity S remains mechanistic secondary and
cannot rescue a failed primary.
