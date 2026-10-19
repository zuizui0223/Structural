# Structural v1.256 — The global BioTIME sample frame is not a global archipelago sample

**Date: 2026-10-19. Verified GIS-only result; no reserved species outcomes opened.**

## Biological research question
Can BioTIME 2.0, selected without looking at future species outcomes, provide independently replicated **literal multi-island terrestrial networks** in which to test whether occupied-source geometry predicts future detection beyond a strong prevalence/calibration reference?

## Independent sources and exact reproduction
- BioTIME 2.0 2025-04-15 RDS, 173,851,491 bytes, source-author MD5 `2fed9f6c8028d4c44d80769c594be056`.
- GSHHG 2.3.7 high-resolution, shoreline level L1 polygons, official GitHub source archive 149,157,845 bytes, SHA256 `8dbbe7e071e77e9e75f2d639239099ebca8d5c16d6a07df8169729d49f15cf41`.
- Exact protocol frozen before GIS exposure: `development/biotime_v2_gshhg_island_crosswalk_protocol_v1_256.json` (also mirrors source version named in `zuizui0223/island/config/island_source_gshhg.yml`).
- [GitHub Actions successful source-locked run 39220652038](https://github.com/zuizui0223/Structural/actions/runs/39220652038), four synthetic tests passing, original RDS checksum, GSHHG source geometry and point-in-polygon checks passing.
- Artifact 12171453422, ZIP digest `sha256:7b28a2dfb10b2c7d86f3672fa42b7e61afa5b0c8cf4cff4d41ef26a41e8d7089`.
- Machine-readable freeze: `development/biotime_v2_gshhg_island_feasibility_result_freeze_v1_256.json`.

## Selection was fixed *without* 33 reserved species responses
Original 708 BioTIME STUDY_ID records → 226 metadata candidates → 95 with enough initial physical repeated survey support → 19 burned pilot + 76 reserved study IDs → 47 strict sample-frame candidates → 44 with five active sites → 40 after pilot-sharing geography exclusion → **33 conservative study-network proxies**. These steps were determined using study/time/coordinate/event metadata, not a favorable ecological response.

## Results

| Realm | Physical study proxies | At least one interior island point | On 2+ distinct island polygons | Strict multi-island terrestrial network |
|---|---:|---:|---:|---:|
| Freshwater | 5 | 0 | 0 | **0** |
| Marine | 11 | 3 | 2 | **0** (marine excluded) |
| Terrestrial | 17 | 4 | 3 | **2** |
| **Total** | **33** | **7** | **5** | **2** |

A total of **2,127** unique source-frame coordinates were classified against **144,749** original GSHHG L1 polygons; only 50 polygon bounding boxes intersected eligible site locations. Island classification requires source polygon area >=5 km² and <7 million km² and a point >=1 km landward of mapped shoreline, with no substitution of offshore or ambiguous coastal points.

Two terrestrial study IDs pass the prospective source-frame requirements:

| Study ID | Strictly repeat-surveyed sites | Island polygon interior sites | Distinct island polygons | Islands with >=3 strict sampled sites |
|---|---:|---:|---:|---:|
| **373** | 30 | 28 | 4 | 3 |
| **375** | 31 | 30 | 7 | 2 |

Terrestrial 597 had 10 sites on two island polygons but only *one* island with >=3 strict sites; 678 had 12 eligible sites but all on one island polygon. They were not rescued by loosening geography after inspection.

## Scientific outcome

**The BioTIME subset does NOT establish a globally replicated oceanic-island connectivity effect.** Only two physically plausible terrestrial multi-island study IDs survive conservative source-independent eligibility; these do not yet prove two geographically independent archipelagos, matched taxonomic communities, a fresh independent temporal validation, geological oceanic origin or actual dispersal. Their geographic names and methods will be checked with source-author metadata only before any reserved taxon or incidence values.

The positive 19-study pilot association between more prior within-study detected locations and subsequent detection remains a general *community sample-detection* pattern, confounded by local prevalence and detection probability. It cannot be presented as evidence of immigration or demographic rescue on islands.

## Next decision

Before reserving study 373/375 for island-specific temporal hypotheses, use the original published BioTIME metadata checksum to recover official title, region, taxon, method, sampling period and field replicate semantics for the two fixed IDs; document whether they represent separate island geographies. If geography/method criteria fail or only one archipelago remains, **STOP a universal island connectivity claim** and keep the global BioTIME analysis separately focused on detection and spatial context; seek an independently repeated island survey database with measured detection and ideally natal movements instead of treating generic study sites as islands.

eBird remains excluded; original 529 mammal/GEB heldout and 76 reserved BioTIME taxon outcomes remain unopened, GEB scientific HOLD.
