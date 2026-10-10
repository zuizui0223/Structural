# CamTrapAsia georeferenced survey centers versus original 4126 heldout island location tiles

v1.238 found 38 exact published camera-mammal names overlapping the source original 529 pilot species, after applying the PREEXISTING source name separator rule. This does not mean those species were seen at any particular site.

v1.239 is a separate, geographic-only intake gate: verify and read ONLY survey_id, country, landscape, site, effort, Y_lat, X_long and survey years from the exact public CamTrapAsia_Metadata_20231031.csv whose 245677-byte length and MD5 2b50c534... are frozen. Do NOT read capture event or species×study presences, abundance, conservation status, or any original mammal species outcome.

Compare geocoded study center POINTS at fixed 10°/5°-shifted tile grain against the previously frozen 4,126 original heldout island coordinates and distinct original geographic block counts (v1.235). Return only aggregate study center counts, distinct surveys and original heldout geographic availability in coincident tiles; no camera station coordinates, survey_ID-level rows, taxon detections or original island IDs are uploaded.

**Tile co-occurrence is NOT island matching**: an inland Borneo camera study could fall in the same 10° bin as offshore marine-island centroids, while a camera array on a giant island may have its center hundreds of kilometres from the island centroid. Site level matching will require independently unified coastline polygons, original island IDs and uncertainty handling in a *separate pre-outcome workflow*.

If no tiles overlap, the original model external field validation is geographically implausible for this survey format; if some overlap, suitability remains conditional and cannot score external 0/1 detection until verified species, site island identity, native status, survey effort and detection models. The nine-archipelago Hébert source remains closed. GEB scientific HOLD, no eBird/ALA/BALA and no graph retuning continue.
