# Indo-Pacific atoll native vascular plants — pre-intake v0.1

## Status

**HOLD before v0.11 intake.**

No vascular-plant species inventory values from the FAIR² data package have been downloaded or parsed by the Structural project in this lane.

The candidate is being frozen from public metadata only.

## Why this system

The 2026 Indo-Pacific atoll FAIR² portal is unusually well matched to the A-Islands source-pool-handoff hypothesis.

The source article reports:

- 310 permanently emergent Indo-Pacific atolls;
- complete vascular-plant inventories for 125 atolls;
- 9,430 plant occurrence records;
- 1,253 vascular plant species;
- nativeness status by species and atoll;
- atoll-level coordinates and archipelago assignments;
- complete biogeographic descriptors for all 310 atolls, including distances to the nearest atoll, large volcanic island and continent;
- environmental descriptors including rainfall.

This gives a genuinely different island system while retaining the ecological objects needed for the same hypothesis.

## Focal biological response

The focal response is **native vascular-plant occurrence at the atoll level**.

Introduced plants are excluded prospectively.

Because the source dataset states that only complete atoll vascular-plant inventories were included, a non-record for a native focal species can be treated as a catalogue-confirmed absence only after the exact response file and completeness semantics are independently verified.

No individual motu/islet-level response will be inferred from atoll-level inventories.

## Source-pool-handoff test

The ecological question is:

> When an atoll is extremely isolated from continents and large volcanic islands, does continuity with occupied atoll source populations retain information that generic major-landmass isolation does not?

### Major-landmass isolation

Before response access:

    major_landmass_distance
      = min(distance to nearest continent,
            distance to nearest large volcanic island)

The exact upper 25% of the eligible-atoll distribution is the primary extreme-isolation tail.

The 70% and 80% cuts are directional sensitivity checks only.

## Generic versus focal-species source network

The atoll graph uses only safe geometry.

Four graph radii are generated deterministically from the eligible-atoll nearest-neighbour-distance distribution:

- q25;
- q50;
- q75;
- q90.

They are rounded upward to whole kilometres and must remain four strictly increasing values. Failure is a pre-response STOP.

For each frozen radius:

### Generic gateway connectivity

The focal atoll is generically connected when its atoll component contains an atoll lying within that radius of either a continent or a large volcanic island.

This represents a response-independent route toward a major external source pool.

### Source-conditioned connectivity

Using only outer-training occurrences, the focal atoll is source-connected when its component contains an occupied atoll for the focal plant species.

### Source decoupling

    source-conditioned connectivity > generic gateway connectivity

This is the atoll analogue of the A-Islands remote-but-linked state.

## Strong reference

The planned ladder is:

### R0
- biogeographic region;
- latitude;
- annual rainfall.

### R1
R0 plus:
- total emergent land area;
- major-landmass distance;
- nearest-atoll distance.

### R2
R1 plus:
- nearest permitted occupied-source distance;
- multi-source pressure from outer-training occupied atolls.

### R3
R2 plus:
- generic gateway connectivity.

### C
R3 plus:
- source-conditioned connectivity.

The predictive contrast remains:

    C minus R3 held-out log loss

Negative is favourable.

## Spatial transfer

The source dataset already assigns atolls to archipelagos.

After safe metadata are opened, archipelago names are normalized and deterministically hashed. The lowest 20% of archipelagos form the burned pilot and the remaining 80% form confirmation.

Minimum requirements before any response opens:

- at least 3 pilot archipelagos;
- at least 6 confirmatory archipelagos.

Within each partition the held-out design is leave-one-archipelago-out.

The response may not be used to choose the split.

## Why the candidate is still HOLD

The paper and metadata are sufficient to define the ecology, but not yet sufficient for v0.11 intake.

Still required:

1. resolve the exact downloadable FAIR² data-package identity;
2. obtain file names, byte sizes and SHA-256 content-blind;
3. assign each file one role: safe metadata, geometry, response, mixed or unknown;
4. prove that the vascular-plant response can remain unopened while atoll/archipelago metadata and geometry are prepared;
5. only then construct a formal v0.11 intake object.

If the package structure mixes plant occurrences into a file that cannot be safely separated before semantic parsing, the candidate remains HOLD or STOP rather than opening it opportunistically.

## Evidence boundary

This candidate is **not** yet empirical evidence.

No plant occurrence value, species prevalence, favourable direction, q75 outcome, source-network result or model score has been inspected.

A-Islands generated the hypothesis; it cannot count as its confirmation.
