# BALA three-wave source-loss pre-intake v1.126

## Why BALA is stronger than the annual candidates

The BALA project has a design that nearly matches the v1.123 causal ordering by construction.

Its core programme repeatedly sampled the same native-forest sites in three major campaigns:

- **BALA1** — baseline;
- **BALA2** — first resurvey, defining source losses;
- **BALA3** — later resurvey, defining subsequent contraction.

The published metadata describe 30 repeatedly sampled core sites in 15 fragments across seven islands and a common BALA sampling protocol. The archive is also a sampling-event dataset with a separate Event core and Occurrence extension.

That is cleaner than trying to manufacture t0/t1/t2 from irregular annual monitoring.

## But the metadata are not internally clean enough to trust yet

The public resource contains several inconsistencies that must be resolved from the raw Event core before any species occurrence is opened:

- 30 versus 31 repeatedly sampled core sites;
- BALA2 reported as 2010–2012 in one place and 2010–2011 in another;
- BALA3/later resampling described as 2021–2022 in one section and 2019–2022 in another;
- the enriched full archive covers eight islands, whereas the repeated core panel is described as seven.

These are not minor editorial details for this analysis. They determine the exact sampling denominator and therefore whether a taxon is genuinely absent at a resurvey.

The gate is therefore simple: reconstruct one deterministic repeated core panel from Event metadata alone, or stop.

## Response firewall

Before ecological response access, only archive inventory, metadata and Event-core fields needed for site identity, fragment, island, date, phase, coordinates and method may be inspected.

The Occurrence extension remains semantically unopened.

No taxon×event table, island occupancy state, source loss or later contraction statistic may be summarized until the core panel is frozen.

## The three-time mapping

If the Event audit succeeds:

    t0 = BALA1
    t1 = BALA2
    t2 = BALA3

Exact calendar membership is **not** copied from the inconsistent prose. It must be recovered from the raw Event rows.

For each taxon, the later analysis would define t0 occupied islands from the frozen core sites, identify t0 islands no longer observed at t1, calculate the leverage of those lost external sources, and ask whether islands still occupied at t1 subsequently lose observed occurrence by t2.

The endpoint remains occurrence in standardized native-forest core sites. It is not whole-island extinction.

## One complication: pilot and confirmation cannot be split by time

There is only one biologically meaningful BALA1→BALA2→BALA3 sequence.

Therefore the burned pilot and confirmation must be disjoint in another dimension. The preferred solution is a deterministic **taxon split** frozen before semantic occurrence access.

After the archive schema identifies a stable taxon routing token, taxa can be assigned by a salted hash to pilot versus confirmatory partitions. The pilot taxa are used only to answer:

- are there enough t0 sources?
- do enough t0→t1 losses occur?
- are there enough t1 survivors?
- is there enough t1→t2 variation?
- do enough held-out clusters remain estimable?

No source-leverage effect is estimated in the pilot.

Confirmatory occurrence rows remain opaque until that estimability gate and the full v1.123 reference/operator/scoring protocol are frozen.

## Surveyed zero

BALA is useful only if a zero can be defended.

A taxon can be called absent from an island-phase only if:

1. the island belongs to the frozen repeated core panel;
2. the required core transects were sampled under the frozen BALA methodology in that phase;
3. the focal taxon has a stable cross-phase identity;
4. no eligible occurrence exists in those samples.

Missing or methodologically incomparable sampling cannot be converted to zero.

## Taxonomic boundary

The metadata explicitly state that Acari and Collembola were excluded, and that Diptera and Hymenoptera other than Formicidae were not separated to morphospecies.

Those groups cannot simply be zero-filled or treated as ordinary species-level transitions. The eligible focal universe must be frozen from stable species/morphospecies identifiers before the burned-pilot occurrence rows are opened.

## Current status

BALA is now the highest-priority **response-unopened pre-intake** candidate because it supplies the exact conceptual sequence the new hypothesis needs.

It is still not evidence. The next scientific event is purely structural:

> raw archive inventory → Event-only repeated-core-panel audit → freeze an opaque taxon partition → then and only then permit a burned-pilot occurrence surface.
