# Burned-pilot input/output surface v0.39

## Purpose

v0.38 binds queue admission to exact replay of the raw burned-pilot CSV.

That makes the raw CSV itself part of the evidence boundary. v0.39 therefore closes its schema rather than allowing ignored columns to travel through the replay path.

## Exact input surface

The burned-pilot CSV header must be exactly, in this order:

```
partition_unit,block,target
```

No additional column is allowed.

This matters because an ignored column could otherwise carry a confirmatory response, fitted effect, candidate ranking, or another post-outcome quantity even though the runner did not use it computationally.

Reordered columns are also rejected so the committed raw-pilot object has one canonical tabular surface.

## Output evidence ceiling

Every runner exit, including protocol STOPs and invalid input, explicitly preserves:

```
effect_size = null
prediction_score = null
predictive_denominator_contribution = 0
```

A pilot failure therefore cannot accidentally become predictive evidence through a different output branch.

## Relationship to v0.38

The active queue remains v0.38.

Its replay now means:

```
exact three-column raw pilot
    -> v0.32 execution
    -> exact stored result replay
    -> v0.37 block/arithmetic recomputation
    -> v0.33 freeze gate
    -> confirmatory-protocol queue
```

The only successful downstream action remains:

`freeze_confirmatory_protocol_only`

Confirmatory response access is still not authorized.

## TTF

TTF remains outside the Structural admission chain and cannot motivate adding columns, changing the endpoint, or relaxing the pilot surface.
