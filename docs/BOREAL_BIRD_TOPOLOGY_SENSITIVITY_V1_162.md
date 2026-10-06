# Boreal bird topology-sensitivity test v1.162

## Why this lane exists

The completed 19-island beetle primary asked whether graph-path occupied-source information improved held-out occurrence prediction on average beyond a strong Euclidean/source-aware reference. It did not.

That negative result is final and is not reopened here.

The newer mammal result suggests a narrower mechanism: exact topology may matter mainly when occupied source sets are sparse enough that source identity is not averaged over. A response-free finite-source identity gives the corresponding configuration-sensitivity term:

S_i(n) = [(M-n)/(n(M-1))] × (sigma_i^2 / mu_i^2),

where M is the fixed number of possible pilot sources, n is the species-specific number actually occupied, and mu_i / sigma_i^2 describe the target-specific source-weight field.

The bird matrix in the same boreal study was prospectively registered as a secondary taxon and remains unopened in Structural. It therefore provides a separate taxonomic response on the same frozen geography.

## Evidence class

This is **not** a new independent geographic system.

It is a prospective same-geography, different-taxon mechanism replication.

A positive result can support taxonomic transfer of the scarcity/configuration mechanism. It cannot establish geographic generality, dispersal, rescue, or temporal persistence.

## Frozen geography

The test reuses the already committed response-independent 19-island geometry and spatial split:

- pilot islands: DN, FD, HU, IL, IS, PP;
- confirmatory islands: BB, BT, DF, EB, HF, MI, NH, OS, PR, SF, SK, WD, WF;
- pilot blocks: 3;
- confirmatory blocks: 7.

No bird response was used to choose these islands or blocks.

## Topology nulls

The observed source operator is the already frozen minimal connected symmetrized 3-nearest-neighbour graph:

- 19 nodes;
- 35 edges;
- fixed graph-pressure kernel scale;
- fixed degree sequence.

Twenty null graphs are generated response-independently.

Each null:

- preserves the exact node degree sequence;
- preserves five actual-edge length-quintile counts at 7/7/7/7/7;
- remains connected;
- receives exactly 80 accepted degree-preserving double-edge swaps;
- is generated from a frozen SHA-256 choice stream and seed.

All 20 frozen null fingerprints are distinct.

## Response-free sensitivity surface

There are exactly six possible pilot source islands, so M = 6.

For each of the 13 confirmatory islands, the actual graph fixes six source-access weights to the six pilot islands. From these we freeze mu_i, sigma_i^2, H_i = sigma_i^2 / mu_i^2 and every possible S_i(n) for n = 2,...,6 before any bird response.

The surface shows a useful feature of this local network: most confirmatory islands have similar H_i, whereas HF and NH are lower. Thus much of the prospective variation in S_i(n) will come from species-specific pilot occupancy count n rather than post-response geographic subgroup selection.

## Pilot gate

Only the six pilot-island bird cells may be opened first.

A bird species enters the fixed universe if it occurs on at least two distinct pilot islands.

The lane continues only if:

- at least 10 bird species qualify; and
- at least three distinct pilot occupancy counts n are represented.

If either fails, the bird lane stops before confirmatory bird response.

No eligibility rule may be loosened after pilot access.

## Prediction freeze

After a clean pilot gate, and still before confirmatory bird response:

- R0 uses the already frozen habitat PCs and disturbance history;
- R1 adds island area and mainland isolation;
- R2 adds actual-graph generic response-independent context;
- R3 adds pilot-only occupancy breadth plus Euclidean occupied-source distance and pressure;
- actual C adds actual-graph path source distance and pressure;
- each of 20 null-C models replaces only those graph-path source features with the corresponding frozen null topology.

All 21 candidate prediction surfaces are frozen for every confirmatory island × fixed bird species before any confirmatory outcome opens.

## Primary test

For each realized confirmatory presence after the one permitted confirmatory read:

D = logloss(actual C) - mean(logloss(null C_1), ..., logloss(null C_20)).

Negative D means the observed topology assigns higher probability to that realized presence than the matched null ensemble.

Each cell already has a pre-response S_i(n_species).

The primary estimand is the slope beta_S of D on z-standardized S, with each frozen spatial block contributing equal total weight.

Prediction:

> **the observed topology should outperform matched null topologies more strongly where source-configuration sensitivity is higher.**

Support requires:

- beta_S < 0; and
- the deterministic block-bootstrap 95% upper bound < 0.

At least four confirmatory spatial blocks must contain realized presences for the primary to be estimable.

## Why this is different from the beetle primary

The beetle test asked for an average C−R3 gain across all cells.

The bird test asks for a predeclared **interaction with configuration sensitivity** and uses observed-vs-rewired topology as the target contrast.

Therefore:

- bird support does not reverse the beetle result;
- bird non-support does not make the beetle result “more negative”;
- the two answer different questions.

## Project boundary

eBird remains disabled by project decision.

BALA remains the independent temporal conservation boundary and is not rerun.

This bird lane is static occurrence mechanism work only.
