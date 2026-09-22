# PNW scoring implementation v0.20

This contract freezes the remaining implementation details **before the 2013 target is opened**.

## Feature sets

R0:
- 2012 lagged RACA state

R1 adds:
- elevation
- maximum pond size
- maximum depth
- wooded perimeter percentage
- fish state

R2 adds:
- nearest other 2012 pond distance
- generic pond reachability fraction
- generic pond pressure

C adds:
- occupied-source reachability fraction
- occupied-source pressure

The primary contrast remains **C − R2**.

## Preprocessing

Continuous predictors use training-fold median imputation. Each included continuous predictor also receives a binary missingness indicator.

After imputation, continuous predictors are standardized using training-fold mean and population SD. A zero-SD predictor maps to zero.

The 2012 lagged state remains binary and unstandardized.

Fish uses three fixed one-hot columns:

- fish_yes
- fish_no
- fish_missing

These are not standardized.

## Model

Frozen implementation:

- scikit-learn LogisticRegression
- solver = lbfgs
- penalty = L2
- C = 1
- intercept = yes
- max_iter = 5000
- tol = 1e-10
- no class weighting

Predicted probabilities are clipped only for log-loss arithmetic at 1e-15 and 1−1e-15.

## Fold estimability

A heldout-region fold is non-estimable for all four models if its training target contains fewer than five positives or five negatives.

A model is additionally non-estimable if one of its continuous predictors is entirely missing in training or if the optimizer fails to converge.

All models use the same applicable target rows. No post-response row rescue is allowed.

## Macro score

For each model:

1. compute heldout predictions for every estimable region;
2. calculate log loss and Brier within that heldout region;
3. average region scores with equal region weight.

No row-level common-effect pooling is the primary result.
