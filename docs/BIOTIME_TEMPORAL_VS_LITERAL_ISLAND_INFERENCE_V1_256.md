# Structural v1.256 — Separate global repeated communities from literal island networks

**Evidence state: 19-study historical biological pilot observed; 76 reserved taxa remain unopened; 33 conservative geographical network proxies frozen.**

## Verified temporal ecology before new geographic claims

The original BioTIME 2.0 published RDS, DOI 10.5281/zenodo.15222193 (publisher MD5 `2fed9f6c8028d4c44d80769c594be056`), was used to calculate detected/nondetected species-site-month-year transitions for **19 permanently burned study IDs**. Frozen source-locked execution: [run 39211305878](https://github.com/zuizui0223/Structural/actions/runs/39211305878). The 6,838 paired physical sampling points represented 123,584 paired species/site detection cells (00 91,967; 01 6,274; 10 8,584; 11 16,759).

Across 14 usable studies, the 5+ observed pilot-source-site group had higher sampled 0→1 probability than the one-source group in 13; one was tied. This is genuine published-data association, but **may be entirely caused by species prevalence, imperfect detection and shared sampling context rather than dispersal or rescue**. It is not an isolated proof of source-network topology.

## Actual independent ecological denominator is smaller than STUDY_ID count

The originally disjoint BioTIME 19/76 study-ID split was inadequate as a guarantee of independent survey geographies. A separate [response-opaque physical-frame audit](https://github.com/zuizui0223/Structural/actions/runs/39217432431) found 20 highly overlapping source-frame pairs, including six that crossed burned pilot and reserved study IDs; seven crossed study partitions in high shared geography. Examples: 558↔559 shared 409 physical sites and 13,469 site/year/month records; 295↔296 shared 127 sites and 552 time frames. None of the reserved studies' species outcomes was accessed.

The original 76 reserved study IDs were reduced without tuning any biological response:

| Decision gate | Remaining candidates |
|---|---:|
| Strict survey-time sampling support | 47 |
| At least five active spatial sites in strict year/month pairs | 44 |
| Remove four reserved study IDs sharing geography with burned pilot | 40 |
| Choose one quality-maximizing representative per near-duplicate source-frame component | **33** |

Distribution of the 33 conserved candidate network proxies: **17 terrestrial, 11 marine, 5 freshwater**. They are not yet 33 independent biological networks or archipelagos. Frozen representatives and source hashes: `development/biotime_v2_conservative_network_cohort_v1_255.json`, verified [GitHub Actions](https://github.com/zuizui0223/Structural/actions/runs/39218466390).

## Literal island question must be tested, not assumed

BioTIME includes mainland, marine and freshwater studies. This branch now has a response-opaque crosswalk protocol `development/biotime_v2_gshhg_island_crosswalk_protocol_v1_256.json` using the same source as `zuizui0223/island`: [GSHHG 2.3.7 high resolution L1 land polygons](https://github.com/GenericMappingTools/gshhg-gmt/releases/tag/2.3.7). The official tagged ZIP is 149,157,845 bytes. Only six physical study/site/time columns from the 33 frozen IDs may enter the GIS.

Predeclared conservative definition: landmass polygon between **5 and <7,000,000 km²**, and sample point >=1 km inside the shoreline. At least two **separate island polygons** with >=3 strictly repeated sites each are needed to identify a candidate inter-island study. Marine study-site points are never relabelled terrestrial island observations. Sensitivities use smaller/larger polygon cutoffs and 0.25 km interior buffer, reported without threshold search.

Even if the geographic gate passes, a polygon cannot distinguish **oceanic vs continental geologic origin** without external geology. Island locality is also not proof of directional propagule transfer or restoration/recolonization. Independent directed dispersal evidence remains absent.

## Next primary comparison, only once geographic/source scope is verified

The next meaningful ecological estimand is a **future detection probability comparison within a species**, not an after-the-fact change in class-specific mean log loss across different species. Use a training-only prevalence/calibration and sampling-effort reference (CAL), then a fixed source-proximity representation, then a fixed configuration extension C. Evaluate `C−CAL` on entirely held-out geographically disjoint study networks and time blocks with explicit sampled-zero and detection-reliability denominators. A point estimate with a matched geometry null is predictive structure, **not** measured immigration or population rescue.

Should the literal-island GIS crosswalk yield insufficient independently sampled archipelagos, the project must label BioTIME a **global repeated community** analysis and seek different island occupancy/movement monitoring data for island conservation mechanism claims. Do not silently reclassify habitats as oceanic islands to preserve a favorable manuscript.

eBird remains excluded. The original global-mammal 529 holdout, A-Islands, BALA, Helgeland, Hopson, Gawecka and SW Finland results remain frozen; no previously protected species outcomes reopened. Main Structural GEB SCIENTIFIC HOLD unchanged.
