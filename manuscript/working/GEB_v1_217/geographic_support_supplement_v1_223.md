# GEB working geographic-support supplement v1.223

The source Barreto et al. (2021) dataset excludes IUCN-mammal-zero islands and has range-polygon-derived, partly historically restored mammal-positive island labels. Structural's selected 5,401 islands are not a universe of all physical islands.

| Geography-only audit | Executed result | Not established |
|---|---|---|
| v1.219 numeric ID equality | 796/5,401 common numbers; no verified island identities; STOP | Numeric same-ID geographic match |
| v1.220 unpaired area profiles | Median area 6.40 km² (5,401 Structural) versus 4.08 km² (17,883 Weigelt) | Mammal-zero exclusion causing size differences |
| v1.221 strict geographic matching | 3,878/5,401 (71.8%) unique reciprocal candidate pairs, within 5 km and area ratio ≤1.5; median coordinate discrepancy 0.659 km | Survey-verified same-island identity |
| v1.222 matched-only near-neighbour comparison | 26.8% of accepted 3,878 focal islands had a nearest other Weigelt namepoint outside the 3,878 strict subset | 26.8% of physical islands actually absent from original 5,401-node Structural graph |
| v1.223 full-5,401 original-centroid check | 21.3% of matched focal islands had a nearest other Weigelt namepoint with no within-5-km / 1.5-area-compatible OTHER selected original centroid; 13.7% had an alternative geocoded point at least 5 km nearer than nearest other original selected centroid | These named islands are IUCN-mammal-zero, historically empty, occupied by the focal species, or valid dispersal stepping stones |

The v1.223 geometry check uses **all 5,401 original selected coordinates**, unlike the v1.222 restricted matched-subset comparator, though focal islands still have to be among the 3,878 accepted matches. Weigelt has 6,337 island rows without usable namepoint coordinates. A named point is not guaranteed to equal an island centroid or polygon, and geographic versions differ. Geographic candidate matchability is size-dependent: 66.2% for source islands below 10 km², 84.6% at 10–100 km², and 70.3% for 100+ km².

**These are response-safe geography diagnostics, not any test of source-to-island mammal movement, population dynamics, or recolonization.** Original v1.119 heldout results, model parameters and geographic graph nulls were never rerun. This supplement cannot change GEB's SCIENTIFIC HOLD.

Independent biological validation would require ex-ante unified physical island polygons and credible species-specific survey response including mammal-zero islands, plus disjoint burned-pilot estimability gates. Consumed original mammal, ALA and other closed biological response lineages cannot be reopened to rescue an ecological claim.
