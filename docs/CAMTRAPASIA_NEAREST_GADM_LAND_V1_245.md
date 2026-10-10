# v1.245 why off-land island centroids need polygon IDs: source geographic sensitivity

Original mammal response-safe centroids were calculated during a separate island-polygon compilation and 10/15 source target centroids lie outside the pin-verified GADM3.6 country MULTIPOLYGON, even though ALL 15 camera study center points lie within land polygons. The off-land distances range from 0.14 to 2.48km (v1.244), as might occur for complicated coastal island shapes or differing polygon vintages.

Instead of retroactively declaring the 10 unknown study pairs either on or off the same island, v1.245 runs one explicitly posthoc geographic SENSITIVITY: compare the nearest GADM3.6 source Polygon to an off-land original heldout centroid with the unique land Polygon actually covering the camera study center. If both polygons are the same, this is a **plausible candidate** for geographical alignment, not a verified original source island polygon identity. There is NO snap of the original model coordinate, no distance cutoff selected after the fact, no inference about source viability, mammal dispersal, recruitment or published 529-species performance. Tied nearest polygons remain unresolved.

The GADM3.6 files and 15 study centers are identically fixed to v1.243. No CamTrapAsia species detections or IUCN heldout responses may be opened. Original GEB scientific HOLD remains.
