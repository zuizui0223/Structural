# Boreal lake-island spatial support audit v0.70

## Result

The coordinate-free **lake-only** route proposed as a possibility in v0.69 is not sufficient under the already-frozen boreal pre-intake contract.

The study has **42 islands in 6 lakes**. The system-specific v0.65 design requires:

- at least **3 pilot spatial blocks**;
- at least **6 confirmatory spatial blocks**;
- pilot and confirmatory evidence partitions to be disjoint;
- no response-defined fallback.

Therefore the minimum disjoint spatial support is **9 blocks**, whereas lake identity supplies only **6**.

This is a pre-response design deduction. No beetle, bird, plant, richness, pilot, or confirmatory response was opened.

## Why the generic v0.31 contract does not rescue lake-only partitioning

The generic v0.31 infrastructure requires nonempty disjoint pilot and confirmatory partitions and freezes a minimum estimable-block count. It is infrastructure, not permission to weaken a stricter system-specific preregistration.

For this boreal candidate, v0.65 prospectively froze stronger spatial support: 3 pilot plus 6 confirmatory blocks. The v0.55 fresh hypothesis additionally requires spatial transfer.

The stricter pre-response system contract therefore controls.

## Consequence

A 42-island lake-membership crosswalk is still useful for physical grouping and for defining within-lake source restrictions, but it **cannot substitute for exact coordinates** in the current admission path.

Before v0.11, Structural now requires one of:

1. **Preferred:** exact response-independent Lat/Long for all 42 sampling plots, followed by the frozen graph-radius/component construction; or
2. a separately justified, response-independent spatial partition with at least nine disjoint spatial units that genuinely preserves the v0.55 spatial-transfer requirement.

The following are not allowed:

- lowering 3 pilot / 6 confirmatory minima;
- treating six lakes as enough simply because they are natural groups;
- assigning arbitrary island-ID pseudo-blocks;
- deriving partitions from biological response;
- visually digitizing exact coordinates from the published map.

## Separate habitat blocker

This audit does not remove the v0.68 local-habitat gate. A prospectively allowlisted, response-independent habitat-structure reference still has to be recovered. If it cannot be recovered under the frozen firewall, the system stops before response.

## Current state

- core external island state (area, direct mainland distance, TSF): **42/42 complete**;
- exact coordinates: **0/42**;
- safe local habitat reference: **incomplete**;
- fresh active systems: **0**;
- confirmatory-eligible systems: **0**;
- biological response opened: **no**.

## Next scientific event

Recover exact response-independent coordinates and safe local habitat structure. Only after both are frozen should Structural build the spatial graph, demonstrate at least 3 pilot plus 6 confirmatory spatial blocks, and proceed to v0.11 → v0.31 → v0.42.
