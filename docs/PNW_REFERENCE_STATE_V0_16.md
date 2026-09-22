# PNW 2012 pre-response reference state v0.16

## Decision

The v0.15 protocol is now backed by a frozen **2012 response-free reference state**.

No Rana cascadae species value, observation count, 2013 target, model fit or candidate ranking was used.

## Safe source projection

Only the already frozen v0.15 safe columns were opened:

- year
- park
- site
- region
- datum
- UTMzone
- UTMe
- UTMn
- error
- elev.m
- max.size
- maxdepth
- perc.wooded
- fish

The 2012 slice contains 542 source rows representing **219 unique sites**. Of those, **150 sites** are also represented in 2013 and therefore form the frozen evaluation-site universe before endpoint applicability filtering.

## Site-level aggregation

Row multiplicity in the master table can reflect repeated biological records. To prevent those repetitions from weighting the physical/current-state reference, aggregation is frozen as:

- numeric variables: median of **distinct nonmissing** values within a 2012 site;
- categorical variables: exactly one distinct nonmissing value is required; a conflict is a STOP.

No categorical conflicts were found.

The resulting table identity is frozen by SHA-256:

`13277413ee5d4c9c30d4d8f9cb900203a92e129ccbc5ad4b6b0593dee0bbcdfd`

The derived table bytes are held in the working evidence package rather than committed to the public repository; the source upload and its SHA remain frozen.

## Missingness

Across all 219 2012 sites:

| predictor | sites missing |
|---|---:|
| elev.m | 0 |
| max.size | 14 |
| maxdepth | 4 |
| perc.wooded | 10 |
| fish | 0 |

Across the 150 2012→2013 evaluation sites:

| predictor | sites missing |
|---|---:|
| elev.m | 0 |
| max.size | 0 |
| maxdepth | 1 |
| perc.wooded | 0 |
| fish | 0 |

The sole common-site maxdepth missing value is `Deerheart.LakeMUL9`.

This site is **not dropped**. The already-frozen v0.15 rule applies: numeric missing values are imputed using the training-fold median with a missingness indicator.

## Held-out geography

The 150 common sites span ten frozen 2012 regions:

- DaggerTwisp 3
- DeerLake 20
- Hwy20 2
- MazamaLakes 8
- Palisades 19
- Potholes 16
- SevenLakes 30
- SprayPark 10
- UpperLena 21
- WyeLakes 21

Park totals are OLYM 108, MORA 37, NOCA 5.

The endpoint-class gate will be evaluated only after Stage 2 response access. Regions are not removed now because their future class composition is still sealed.

## Next irreversible step

The pre-response reference is frozen. Stage 1 may now open **2012 lagged RACA state only** under the v0.14 temporal firewall.

Before Stage 1 opens, a separate authorization receipt must pin:

- protocol v0.15;
- source/header hashes;
- reference-table hash;
- movement worldset;
- species token;
- allowed Stage-1 columns;
- explicit prohibition on 2013 response access.

Only after that receipt is merged and CI-green may 2012 RACA state be constructed.
