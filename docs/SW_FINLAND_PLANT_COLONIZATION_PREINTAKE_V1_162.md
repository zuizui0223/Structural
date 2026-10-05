# SW Finland plant colonization pre-intake v1.162

## Why this is the strongest non-eBird temporal candidate found

Aikio et al. (2020) paired historical and recent vascular-plant inventories on **471 islands** in the SW Finland archipelago, spanning roughly **70 years** and **587 species**. The archived analysis table contains one row per potential colonization event: a species absent from a focal island historically, followed by a later binary colonization outcome.

The published study already established two important baseline facts: historical range size and distance to the nearest historically occupied island are strong predictors of colonization. That makes this dataset unusually well matched to the current Structural question, because the new test is deliberately harder:

> **After source count and nearest-source distance are already supplied, does the exact configuration of the historical source islands retain additional information about which islands are colonized decades later?**

This is the temporal colonization counterpart to the global-mammal ultrarare occurrence result. It is also complementary to BALA, which tested a different endpoint—later contraction after source loss—and did not support source leverage.

## Evidence class

This is **not pristine fresh confirmation**. The original paper reports colonization results, including the strong effects of historical range size and nearest historical source. Structural therefore already knows broad outcome-level summaries.

However, Structural has not opened the row-level archive for this route, and the published analysis did **not** test exact source topology beyond source count and nearest source. We classify the route as an **independent-geography, temporal, literature-outcome-aware mechanism stress test**.

A favorable result can strengthen a colonization-process interpretation; an adverse result is equally informative. Neither direction may be presented as a pristine preregistered replication.

## Response firewall

The Zenodo mirror documents a single 129.2 MB file, `colonization_select.csv`, with:

- `outcome`: later colonization failure/success;
- `spp.name`: focal species;
- `holmkod`: focal island;
- original EUREF-FIN island coordinates;
- `Historical_total_log`: historical range size;
- `Dist_to_historical_log`: nearest historical occupied source;
- recipient-island environment and species traits.

The next step is **header only**. If the header matches the frozen metadata, a separate projector may open t0/static columns while treating `outcome` as an opaque token.

Because every archived row is documented as a species-island pair that was historically unoccupied, the t0 occupied source set can in principle be reconstructed as the complement of row keys within the frozen island × species universe. That reconstruction must pass response-independent consistency gates before any future outcome is opened.

## Intended test after the t0 gate

The final protocol is not yet authorized, but its target is fixed conceptually:

1. build a response-independent island graph from historical island coordinates;
2. freeze spatial heldout blocks and matched rewired topology nulls;
3. represent recipient-island state and published simple source controls in a strong reference;
4. add exact graph-path historical-source information only in C;
5. compute finite-source configuration sensitivity from t0 state only;
6. freeze every heldout prediction;
7. open `outcome` once and score colonization.

The primary scientific contrast will ask whether exact historical source topology predicts later colonization **beyond historical source count and nearest-source distance**. A topology-null comparison and the precomputed configuration-sensitivity index will distinguish a true arrangement effect from generic source availability.

## Hard boundaries

- eBird is not used.
- No BALA rerun or rescue analysis is involved.
- Boreal beetle results remain closed and unchanged.
- Published AIC variable selection is not reused as if it were response-independent.
- No `outcome` value may be opened until the t0 source state, graph, spatial partition, reference and prediction protocol are frozen.
