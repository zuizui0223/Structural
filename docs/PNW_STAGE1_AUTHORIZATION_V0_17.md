# PNW Stage 1 authorization v0.17

## Authorized opening

The PNW design has passed the v0.15 protocol freeze and v0.16 response-free reference freeze.

Stage 1 is now authorized for **2012 lagged Rana cascadae state only**.

Allowed fields are limited to:

- year
- site
- species
- obs1–obs6
- survtype1–6

Only rows from 2012 may contribute to the Stage 1 state, and only the RACA species token may contribute after projection.

## What Stage 1 may produce

Stage 1 may construct:

1. the 2012 observed site-use state;
2. the set of 2012 occupied source ponds;
3. generic and occupied-source connectivity under the already-frozen 250/500/1000/1500/5000 m worldset;
4. the full R0/R1/R2/C predictor table.

## What remains sealed

All 2013 response values remain sealed.

Stage 1 may not change:

- species;
- movement worldset;
- local-reference variables;
- feature definitions;
- held-out region split;
- model family;
- primary or secondary metric.

## Endpoint rule

The declared endpoint is **observed site use**.

For a 2012 site:

- positive if any RACA observation across valid visits is >0;
- negative if at least two valid visits occurred and no positive RACA observation was recorded;
- otherwise non-estimable.

This is not a latent-detection-corrected occupancy estimate.

## Next gate

After 2012 state is opened, the resulting state and complete feature matrix must be fingerprinted and committed. Only then can Stage 2 authorization open the 2013 target.
