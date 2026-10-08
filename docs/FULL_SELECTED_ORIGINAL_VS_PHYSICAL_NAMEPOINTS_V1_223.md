# v1.223: do extra mapped physical namepoints remain near original 5,401 islands?

v1.222 found that, for 26.8% of confidently crosswalked 3,878 focal islands, the nearest other Weigelt geocoded *namepoint* lay outside the subset of 3,878 strictly matched islands. This **does NOT** prove exclusion from the original Structural graph, since 1,523 original Structural islands were not strictly matched. The v1.223 design addresses that exact inferential mismatch.

For every one of the 3,878 high-confidence matched focal original islands, use its **original Barreto centroid** as the origin. Compare its nearest neighbor among **all other 5,400 originally selected Barreto centroid nodes** with the nearest other Weigelt 2013 geocoded namepoint (11,546 total reference namepoints, excluding the v1.221-identified corresponding namepoint for the focal). The geographical area and latitude/longitude are response-safe artifacts. For the nearest Weigelt namepoint, search for **any other** original selected Barreto centroid within the already frozen 5-km/1.5-area-ratio threshold, including the 1,523 previously unmatched originals. Skip other namepoints within 0.2 km of the focal centroid as ambiguous potentially duplicate records.

This new audit reports coverage, candidates with no close/area-compatible selected original centroid, and distances by area class. It DOES NOT reconstruct the original regionally-connected kNN graph, infer that unmatched namepoints were in fact mammal-zero, model colonization, or rescue existing v1.119 effects. The discrepancy between Weigelt named points and Barreto centroids and differing source vintages remains a limitation.

No focal species values, original model predictions, or eBird. GEB scientific HOLD persists.
