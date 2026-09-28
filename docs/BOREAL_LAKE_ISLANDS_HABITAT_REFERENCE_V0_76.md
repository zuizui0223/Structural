# Boreal deterministic habitat reference v0.76

## Purpose

v0.68 already froze the ecological rule: use only complete prospectively safe
local habitat variables, z-standardize them, and if two or more survive use the
minimum number of PCs reaching 80% cumulative variance.

v0.76 now freezes the numerical implementation **before those safe row values
are opened**.

## Standardization

For each eligible habitat variable over the exact frozen island universe:

- mean = arithmetic mean;
- SD = population SD, denominator n;
- mean/variance accumulation uses Python `math.fsum` so row order cannot change last-bit results;
- z = (x - mean) / SD.

The constants must exact-replay those emitted by v0.74.

## One-variable case

If exactly one complete nonconstant variable survived v0.74, the habitat
reference is simply its population z-score, emitted as `HAB1`.

## PCA case

With two or more variables:

1. construct the population correlation matrix `X'X/n` from z-scores using `math.fsum` accumulation;
2. compute its symmetric eigendecomposition with deterministic Jacobi rotations;
3. Jacobi tolerance = 1e-14, maximum 10,000 iterations;
4. clamp only tiny negative eigenvalues in [-1e-12, 0) to zero;
5. orient each eigenvector so its largest-absolute loading is positive, ties by
   lowest variable index;
6. order components by decreasing eigenvalue, with oriented float-hex loading
   signature as deterministic tie-break;
7. retain the smallest number of PCs whose cumulative explained variance is at
   least 80%.

Reference scores and all machine-frozen numerical quantities are emitted in
Python hexadecimal float form.

## Evidence boundary

This is predictor construction only. It uses no species occurrence, richness or
protected mixed-file values and contributes zero empirical evidence.

Even a successful habitat freeze does not authorize v0.11 until the real v0.75
spatial partition has also passed.
