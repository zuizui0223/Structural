# RMNP scoring implementation v0.27

This file freezes the remaining model implementation details **before any 2022 AMMA value is opened**.

## Feature ladder

R0:
- 2021 lagged AMMA state

R1 adds:
- fish
- site length
- site width
- max-depth ordinal

R2 adds:
- nearest other 2021 source pond distance
- generic reachability across 500/1000 m
- generic pond pressure across 500/1000 m

C adds:
- occupied-source reachability across 500/1000 m
- occupied-source pressure across 500/1000 m

The sole primary contrast remains **C − R2**.

## Preprocessing

Continuous numeric variables are imputed using the training-fold median and receive an unstandardized missingness indicator.

After imputation, continuous variables are standardized with training-fold mean and population SD. Zero-SD variables map to zero.

The 2021 lagged state remains binary and unstandardized.

Fish uses fixed three-column one-hot encoding:

- fish_yes
- fish_no
- fish_missing

## Model

Frozen learner:

- scikit-learn LogisticRegression
- lbfgs
- L2
- C = 1
- intercept
- max_iter = 5000
- tol = 1e-10
- no class weighting

## Fold gate

A 15-km heldout block is scored only if:

- it contains at least 3 applicable target rows;
- the training target has at least 5 positives and 5 negatives.

All four models use the same applicable rows.

## Scoring

Primary: block-macro heldout log loss.

Secondary: block-macro Brier score.

Probabilities are clipped at 1e-15 only for finite log-loss arithmetic.

No solver, feature, missingness, block or regularization change is allowed after 2022 target access.
