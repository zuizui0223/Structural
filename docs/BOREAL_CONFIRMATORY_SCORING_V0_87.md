# Boreal one-shot confirmatory scorer v0.87

v0.87 freezes the final irreversible test of the prospective v0.55
dual-isolation hypothesis.

## Primary estimand

For every fixed-species confirmatory target, compute binary log loss under the
already-frozen R3 and C probabilities and form:

    loss_C - loss_R3

Then:

1. average those row differences within each frozen v0.75 confirmatory spatial
   block;
2. average the block means with equal block weights.

Negative is favourable.

This is deliberately not a row-weighted mean. A large block with more islands
or more target rows cannot dominate the fresh system-level result.

## Uncertainty

The cluster bootstrap resamples confirmatory spatial blocks with replacement.
It is fully deterministic:

- 10,000 replicates;
- seed 20260928;
- draw index = first 8 bytes of
  SHA256(`seed|replicate|draw`) interpreted big-endian modulo the number of
  confirmatory blocks;
- linear type-7 2.5% and 97.5% quantiles.

Primary support requires both the point estimate and the 95% upper bound to be
strictly below zero.

## Response firewall

Pre-access size/SHA or binding failures do not consume the v0.86 authorization.
Once the confirmatory router begins, the authorization is consumed permanently.

The router decodes only fixed-universe species on confirmatory islands.
Pilot occurrence cells and non-focal confirmatory species remain opaque.

Any post-access domain, firewall or prediction-target join failure is terminal
for that protocol version. There is no rerun.

## Interpretation ceiling

A valid completion contributes exactly one fresh confirmatory system whether
the primary is supported or not.

A failed primary cannot be rescued by an external-isolation tail, subgroup or
secondary moderator. The result is predictive structural evidence only and does
not authorize a dispersal, colonization, rescue or historical-mechanism claim.
