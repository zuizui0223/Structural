# SW Finland plant colonization pre-intake v1.162

## Why this is the strongest non-eBird temporal candidate found

Aikio et al. (2020) paired historical and recent vascular-plant inventories on **471 islands** in the SW Finland archipelago, spanning roughly **70 years** and **587 species**.

The published study already established two important baseline facts: historical range size and distance to the nearest historically occupied island are strong predictors of colonization. The new Structural question is deliberately harder:

> **After source count and nearest-source distance are already supplied, does the exact configuration of historical source islands retain additional information about which islands are colonized decades later?**

This is the temporal colonization counterpart to the global-mammal ultrarare occurrence result. It is complementary to BALA, which tested later contraction after source loss and did not support source leverage.

## Evidence class

This is **not pristine fresh confirmation**. The original paper already reports broad colonization patterns. Structural classifies it as an **independent-geography, temporal, literature-outcome-aware mechanism stress test**.

A favorable result can strengthen a colonization-process interpretation; an adverse result can constrain it. Neither direction may be presented as a pristine preregistered replication.

## Response firewall

The Zenodo mirror documents one mixed file, `colonization_select.csv`, containing:

- `outcome`: later colonization failure/success;
- `spp.name`: focal species;
- `holmkod`: focal island;
- original EUREF-FIN coordinates;
- `Historical_total_log`: historical source breadth;
- `Dist_to_historical_log`: nearest historical occupied source;
- recipient-island environment, species traits and `Gowdis_traits`.

Access is staged:

1. v1.166 may download the exact MD5-bound file and read the header only;
2. v1.167 must separately freeze that header identity;
3. a byte-level v1.164 router may then copy only prospectively safe t0 fields while **never decoding or persisting the protected `outcome` field bytes**;
4. the t0 projector may operate only on that safe projection.

## Critical complete-case boundary

The archived table should not be assumed to contain every historical absence. The published modelling workflow dropped observations with missing explanatory data.

Therefore a missing archive row is never interpreted as historical presence.

A species becomes topology-eligible only if its historical source count can be recovered response-independently and

    archived historical-absence row count + historical source count = 471.

Only then may the complement of its known historical absences define the exact occupied source islands. Species with incomplete accounting are excluded before future outcome access. At least **30 exact-source species** are required; otherwise the route stops without opening recent colonization outcomes.

The first source-count attempt uses the documented `log10(x+1)` transform only if inversion is exact within the frozen tolerance. If the archived value is on a later standardized scale, Structural does not guess the transformation. It instead remains HOLD pending a separately frozen t0-only lookup such as the published Supplementary `Potential_islands` field.

## Intended test after the t0 gate

Only after exact-source support qualifies may Structural:

1. build a response-independent graph from historical island coordinates;
2. freeze spatial heldout blocks and 20 matched rewired topology nulls;
3. build a strong reference containing recipient state, species/pair state, exact source count, nearest source and diffuse Euclidean source pressure;
4. add graph-path historical-source information only in C;
5. compute finite-source configuration sensitivity from t0 state only;
6. freeze all pilot/confirmatory prediction rules;
7. open the future endpoint under a separate one-shot authorization.

## Hard boundaries

- eBird is not used.
- No BALA rerun or rescue is involved.
- Boreal beetle results remain final and unchanged.
- Published AIC variable selection is not reused as a response-independent Structural reference.
- Missing archive rows never become historical sources by default.
- No future `outcome` value may be opened until exact-source eligibility, graph, spatial partition, reference and prediction protocol are frozen.
