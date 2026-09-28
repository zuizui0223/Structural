# Boreal response-independent spatial partition v0.75

## Why freeze this before coordinates are opened

The boreal candidate needs real spatial transfer. v0.70 showed that six lake
labels are not enough for the already-frozen minimum of 3 pilot plus 6
confirmatory spatial blocks.

v0.75 removes the next degree of freedom before exact coordinates are projected:
the distance metric, candidate graph scales, component rule and pilot split are
all fixed now.

## Geometry

Distances use great-circle haversine distance between the published decimal
degree plot centers, with Earth radius fixed at **6371.0088 km**.

For each of the 42 islands, compute its nearest-neighbor distance. Candidate
radii are q25, q50, q75 and q90 of those 42 distances using Hyndman-Fan type 7
(R default) linear quantiles. Each radius is rounded **upward** to 0.1 km.

At a candidate radius, two islands share an undirected edge when their distance
is less than or equal to that radius. Spatial blocks are connected components.

## Scale selection

Candidate order is:

1. q90
2. q75
3. q50
4. q25

The first candidate retaining at least **9 connected components** is selected.
This is the coarsest allowed scale with enough support for the frozen evidence
split. If even q25 has fewer than 9 components, the system stops before v0.11.

No species response, richness, habitat value or pilot result participates in
scale selection.

## Disjoint pilot/confirmatory split

Each connected component gets a stable ID from its sorted island IDs.

Blocks are ranked by SHA-256 using the fixed salt
`boreal-v0.75-pilot-split`.

Pilot block count is:

`max(3, ceil(0.20 * number_of_blocks))`

The remaining blocks are confirmatory and must number at least **6**.

The first ranked blocks are pilot; all others are confirmatory. No reassignment
after seeing pilot outcomes is allowed.

## Claim boundary

A successful v0.75 partition only clears the spatial-support part of pre-intake.
It does not authorize v0.11 until the response-independent local habitat
reference is also frozen, and it contributes zero empirical evidence.
