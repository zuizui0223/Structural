# Macro ecological synthesis v1.85

## The result is about occupancy constraints, not generic connectivity benefit

The global mammal analysis still supports the core distinction between external isolation and species-conditioned internal source isolation, but v1.84 clarifies **what kind of information** graph-path topology adds.

The frozen block-weighted primary is unchanged:

- 5,401 islands;
- 79 focal species;
- 4,126 held-out islands;
- 168 held-out spatial blocks;
- 325,954 held-out island × species cells;
- C−R3 = **−0.001814**;
- 95% block-bootstrap interval **[−0.002817, −0.000997]**;
- block-weighted R3 log loss = 0.048108;
- block-weighted C log loss = 0.046294;
- relative reduction = **3.77%**.

The direction remains broad: 108/168 blocks, 10/12 bioregions, and 64/79 species favour C.

## But the improvement is asymmetric

Only 5,620 of 325,954 held-out cells are presences (1.724%).

On true absences:
- R3 log loss = 0.028685;
- C log loss = 0.022884;
- C−R3 = **−0.005801**;
- 130/168 blocks favour C.

On realized presences:
- R3 log loss = 2.012778;
- C log loss = 2.129216;
- C−R3 = **+0.116438**;
- only 40/124 blocks containing presences favour C.

A class-balanced equal-block diagnostic is **+0.049412**, favouring R3. It is a post-hoc guardrail, not a replacement primary.

The correct interpretation is therefore:

> Graph-path source topology improves probability prediction over the naturally sparse island × species occupancy surface mainly by reducing overprediction of true absences. It does not improve true-presence log loss.

## This is not only a global downward probability shift

ROC-AUC increases from **0.90947** to **0.91851**, so C changes ranking as well as calibration.

Average precision decreases slightly from **0.35612** to **0.35016**, reinforcing the conclusion that C does not improve rare-presence retrieval.

The result is best described as **asymmetric occupancy-constraint information**, not improved presence detection or source rescue.

## Empty-source sentinel is not the explanation

Graph-source-empty cells are common: 255,071/325,954 = **78.25%**.

But C−R3 is:
- **−0.000799** in graph-empty cells;
- **−0.014110** in graph-source-nonempty cells.

The advantage is therefore much stronger where an occupied graph-reachable pilot source actually exists.

At block level, graph-empty fraction versus C−R3 has Spearman rho = **+0.283**. More empty support corresponds to a weaker C advantage.

This makes a sentinel-artifact explanation inconsistent with the observed pattern.

## Three attenuation axes now converge

The topological increment weakens with:

1. **external island isolation** — Current_isolation rho = +0.287 across blocks and +0.228 after within-bioregion centering;
2. **species occupancy breadth** — pilot prevalence versus species C−R3 rho = +0.276;
3. **graph-source emptiness** — block empty fraction versus C−R3 rho = +0.283.

The most useful current working principle is therefore a **source-network contrast window**. Internal topology carries information while an occupied source network exists and retains structural heterogeneity. Information declines when source support becomes too sparse, too empty, or too broadly saturated.

Formal unimodality and causal source depletion/saturation are not established.

## Cross-system status

- The 318-island mammal stress test independently points toward external-isolation attenuation, but is not reopened for class-specific post-hoc scoring.
- The GIFT fresh lane remains terminal and unscored.
- The strongly endpoint-filtered GIFT subset has the same overall C−R3 sign but cannot establish plant generality.
- Boreal beetles remain a valid fresh local non-support case.

## Central claim boundary

Allowed:

> In a global nonconfirmatory mammal macroanalysis, species-conditioned graph-path source topology added held-out information beyond external isolation, occupancy breadth, regional prevalence, and direct/diffuse source proximity. The natural-prevalence gain was geographically broad but asymmetric, primarily reducing loss on true absences, and weakened with external isolation, species breadth, and graph-source emptiness.

Not allowed:

- fresh global confirmation;
- two-taxon confirmation;
- improved presence detection;
- graph paths are realized dispersal routes;
- source topology causes rescue;
- class-balanced performance supports C;
- formal source-network unimodality.

## Future independent test

The next response-sealed system must preregister the same natural-prevalence primary **and** the class-specific/ranking diagnostics before response access, so that opportunity versus constraint signatures can be distinguished without post-hoc endpoint switching.
