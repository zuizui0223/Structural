# eBird same-byte SED support chain v1.156

The eBird candidate is not waiting for a scientific model. It is waiting for an official checklist-level Sampling Event Data file.

v1.156 closes the remaining provenance gap before that file arrives.

When an official SED extract is supplied, the chain:

1. hashes the SED bytes;
2. runs the response-independent v1.154 schema/coverage audit;
3. requires the SED hash to remain unchanged;
4. runs the v1.155 shared-checklist deduplication, USGS Global Islands point-in-polygon mapping and island-year survey-support build;
5. requires the same SED hash again;
6. requires both child gates to agree on the detected modern/legacy eBird protocol schema;
7. freezes the SED SHA, island-geometry SHA, child receipt SHAs and annual survey-surface SHA.

No species name, detection, nondetection, annual occupancy or source-loss event is opened or constructed.

A successful chain still contributes zero empirical evidence. Its only scientific consequence is to authorize the next response-independent design step: selecting eligible three-wave windows and freezing disjoint burned-pilot and confirmatory partitions.

## Current external blocker

The official eBird Sampling Event Data extract is not present in Structural.

The candidate therefore remains on HOLD. The Dryad observed-species archive must remain unopened.
