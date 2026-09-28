# Boreal pre-confirmatory model freeze v0.85

v0.85 freezes the complete predictive surface before any confirmatory beetle
occurrence can be opened.

## Strong reference ladder

R0 contains the frozen local habitat reference plus time since fire.

R1 adds classical island state: area and direct mainland distance.

R2 adds generic response-independent network context from the v0.83 kNN graph.

R3 adds training-only species source context in ordinary geography:

- global pilot occupancy breadth;
- nearest Euclidean occupied source;
- diffuse Euclidean source pressure.

C adds the genuinely structural source terms:

- nearest graph-path occupied source;
- graph-path occupied-source pressure.

The primary comparison is C versus R3.

## No confirmatory leakage

All model fitting uses the compact v0.84 pilot-only matrix. For a pilot training
row, the focal island is excluded from its own source set. For a confirmatory
prediction, all and only pilot islands can act as occupied sources.

The full prediction surface is frozen for every confirmatory island × fixed
species before a target is opened.

## Numerical contract

v0.85 uses pooled ridge logistic regression with ridge λ=1 and a deterministic
pure-Python IRLS solver. All non-intercept coefficients are penalized.

Response-independent island-state predictors are population-standardized over
the frozen 42-island universe. Species-conditioned source predictors are
standardized from pilot training rows only. Zero variance in any frozen feature
is a STOP before confirmatory response.

## Primary scoring contract

After future one-shot confirmatory access, calculate binary log loss for R3 and
C. First average C−R3 within each confirmatory v0.75 spatial block, then average
blocks equally.

Support requires:

- point estimate < 0; and
- 95% cluster-bootstrap upper bound < 0.

The bootstrap unit is the confirmatory spatial block, with 10,000 replicates
and seed 20260928.

External-isolation interactions are not part of the primary and cannot rescue a
failed overall C−R3 result.
