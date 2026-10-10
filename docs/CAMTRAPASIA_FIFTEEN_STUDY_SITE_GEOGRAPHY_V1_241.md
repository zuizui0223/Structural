# v1.241 fifteen geographically proximate camera studies, without biological observations

The already-executed v1.240 source-locked study-centre distance screen found 15/239 CamTrapAsia study centers closer than 25 km to their nearest original heldout island center; these correspond to 10 nearest islands and 7 original heldout geographic blocks.

This response-opaque geography-only run keeps exactly those 15 records, without retuning the radius, and reports published study country/site/landscape text, WGS84 camera-study **centres**, nearest original heldout island ID/block and geodesic separation. The source metadata CSV and original 5,592 physical coordinate table and 4,126 heldout routing must pass their previously fixed byte hashes and sizes. Only geographic/study-name attributes are parsed; source camera detections, taxon incidence, original IUCN heldout 0/1 values and graph model predictions are never read.

**A point within 25 km of an island centroid is not identified as occurring on that island.** The next gate must use independently downloaded **land polygon geometry** at a declared version, and confirm camera-study centre and original island centroid within the same contiguous physical land polygon; this may also fail for a large island whose station-to-centroid distance exceeds 25km. No species prediction validation is automatically authorized.

GADM v3.6 historically supplied Barreto source geometry; country-specific GADM3.6 Shapefiles are publicly available at https://geodata.ucdavis.edu/gadm/gadm3.6/shp/ under the provider's research/redistribution license. No spatial outcome adjustment or eBird.
