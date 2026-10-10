# v1.247 CamTrapAsia external-validation support STOP before biological response

A different biological source than the earlier 39-island Zhoushan survey, CamTrapAsia (Mendes et al. 2024, DOI 10.1002/ecy.4299; Zenodo 10.5281/zenodo.10780971) has 239 camera study centers, 38 taxa with exactly matching source-original 529 binomials under Structural's preexisting name schema. This is promising as independent observation-method material, but almost all camera survey centers are far from the original 4,126 heldout island centroids.

A response-free geometric cascade was executed (not response-fitting):
- v1.240 fixed 25km radius yielded 15 studies / 10 nearest original heldout island IDs / 7 blocks.
- v1.241 identified those site names and candidate original island IDs; only Pulau Bawean, Buton, etc appeared likely marine-island names, whereas Ujung Kulon, Sarawak, Bukit Barisan, Leuser are mainland or giant-landmass habitats.
- v1.242 independent Natural Earth10m coastline found 4 strict same-component and 10 unresolved, requiring source-vintage GADM.
- v1.243 GADM3.6 raw point-in-polygon found 2 strict same, 3 different, 10 centroid-offland unknown.
- v1.244 showed ALL 15 camera centers are on mapped land; original heldout centroids are offland by 0.14–2.48km in ten cases, requiring careful centroid semantics.
- v1.245 explored nearest polygon for offland centroids, giving 9 additional apparent same-land candidates.
- **v1.246 measured original source island Area versus selected nearest GADM component WGS84 ellipsoidal area**. All nine newly 'rescued' nearest-country-land candidates had extreme area mismatch: e.g. source original Ujung-Kulon-adjacent island only 4.94km² vs Java land polygon 126660km², Buton-adjacent original islands only 2.14/2.70km² vs 4524km² Buton, and Sumatra-adjacent original island 3.38km² vs 429241km². At the frozen primary factor-2 area agreement gate, ONLY the **two Pulau Bawean surveys** remain. The original Bawean island Area 206.7 km² and GADM land polygon area 207.24 km² agree to 0.3%.

Those two surveys share **exactly one original frozen heldout island ID (65489) in one original heldout geographic block (GB_09dd5f7909bd)**. Even if all 38 taxon overlaps were actually sampled there, the maximum distinct-island ×taxon check would be 38 cells and there is ZERO validated direct site-species incidence. This source CANNOT independently establish the frozen 529-species model's global external skill or graph dispersal topology. Do not open species/camera captures to rescue this already failed specific GEB confirmatory question.

**Ecological message:** A single shared landscape NAME or nearby island centroid is not equivalent to sampling the exact same island. The area mismatch explicitly illustrates continental/main-island camera studies being accidentally assigned to tiny offshore target islands. Existing original mammal prediction gain remains a within-map result. No biological effect estimates changed; GEB remains scientific HOLD.
