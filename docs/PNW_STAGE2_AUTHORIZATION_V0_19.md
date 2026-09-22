# PNW Stage 2 authorization v0.19

## Authorization

Stage 1 is merged and CI-green, with both the 2012 state table and the complete R0/R1/R2/C feature table fingerprinted.

Stage 2 is therefore authorized **once** for the 2013 RACA future target.

## Allowed opening

Only 2013:

- year
- site
- species
- obs1–obs6
- survtype1–6

may be opened for target construction.

The same Stage 1 normalization is locked:

- valid survey types = full / partial;
- dry is excluded;
- missing RACA rows are zero-filled on valid survey occasions.

## Applicability frozen before target access

A row may enter held-out scoring only if:

1. it belongs to the frozen 150-site feature table;
2. its 2012 lagged state is estimable;
3. its 2013 target is estimable.

No additional response-dependent filtering is allowed.

## Frozen scoring

All four models are scored on the same applicable site rows:

- R0
- R1
- R2
- C

The sole primary contrast remains **C − R2**.

Held-out split remains leave-one-2012-region-out. A fold is estimable only if the training set contains at least 5 positive and 5 negative 2013 targets.

Primary metric: region-macro held-out log loss.

Secondary metric: region-macro Brier score.

## No rescue

After the 2013 target is opened:

- scales cannot change;
- source anchors cannot change;
- normalization cannot change;
- reference variables cannot change;
- splits cannot change;
- model family cannot change;
- adverse/null results are retained.

PNW remains design-exposed and non-pristine regardless of outcome.
