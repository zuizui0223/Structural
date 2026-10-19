# Structural v1.252 — BioTIME repeated detection pilot result

**2026-10-19 — Completed source-locked biological pilot; 19 burned studies, 76 response-unopened studies.**

## Verified source and replay
BioTIME 2.0 exact April 15, 2025 RDS (DOI https://doi.org/10.5281/zenodo.15222193) matched publisher MD5 2fed9f6c8028d4c44d80769c594be056; 173,851,491 source bytes.
Prospective endpoint and 19/76 split authority: development/biotime_v2_burned_pilot_detection_protocol_v1_252.json and development/biotime_v2_pilot_confirmatory_split_v1_251.json.
[GitHub Actions run 39211305878](https://github.com/zuizui0223/Structural/actions/runs/39211305878) succeeded: artificial 9-cell regression, source integrity, RDS pilot extraction, transition identities, 19-study scope and artifact upload all passed. Artifact 12167208910, SHA256 0df9894a1aeb16f0c0418469287442852659fd604431f4f2a655c61037a33534. Biological source records are NOT published by this workflow; only per-study aggregate and result summary.

## Observed detection table (never call 0 a verified biological absence)

| t→t+1 | Matched species-site-month-year cells |
|---|---:|
| 0→0 | 91,967 |
| 0→1 | **6,274** |
| 1→0 | 8,584 |
| 1→1 | 16,759 |
| Total | **123,584** |

Strict physical frame: **6,838** coordinate-proxy × calendar-month × consecutive-year pairs, with two distinct source-defined sampling events per month-year at both ends. Of 19 studies, **14** have eligible biological cell pairs and five have none. Thirteen studies contain any apparent 0→1. At t+1, 2,266/6,274 0→1 cells have ≥2 separate positive sample-event detections (36.1%). Another 3,172 t+1 positives lack any t-study-month regional species pool and were excluded from the 0→1/0→0 universe, rather than imputed as a true colonization. All 19 studies contribute 945,936 valid raw records, of which 822,927 meet the declared species-resolution and positive abundance/biomass gate.

## Source count and re-detection
Here source count = the number of sampled coordinate proxies in that same study-year-month detecting the species in year t; this is a prevalence proxy, not proof of viable migratory populations. The focal recipient is t-undetected in the 0→1 denominator.

| t source sites | 0→0 | 0→1 | 0→1/(0→0+0→1) | 1→0 | 1→1 |
|---|---:|---:|---:|---:|---:|
| 1 | 25,324 | 1,236 | 4.65% | 1,225 | 630 |
| 2 | 11,949 | 797 | 6.25% | 897 | 615 |
| 3–4 | 11,884 | 971 | 7.55% | 1,292 | 1,000 |
| 5+ | 42,810 | 3,270 | 7.10% | 5,170 | 14,514 |

All 14 eligible studies have comparison support for both 1 and 5+ source tiers; **13/14** show a higher within-study 0→1 rate for 5+, and **1/14** is tied at zero, with **none negative**. The same 13/1/0 direction obtains using the 0→1 with ≥2 t+1 sample detections. This is an outcome-exposed **pilot descriptive result**, not a preregistered inferential primary test.

## Heterogeneity and evidence ceiling
Marine study 110 contributes 2,979/6,274 (47.5%) 0→1 observations. The three largest contributing studies 110, 693 and 377 jointly contribute 4,670/6,274 (74.4%). Source count, species prevalence/detectability, spatial extent, habitat and sampling effort are highly confounded. The pooled 0→1 percentage is not monotone (3–4: 7.55%, 5+: 7.10%), whereas within-study 1 vs 5+ differences are predominantly positive. The result is not evidence for directional migration, dispersal kernels, viable donors, population rescue or colonization. The biological records are already public; the heldout is within an existing database and is not a pristine independent field replication.

BioTIME has marine/freshwater/terrestrial study sites, not a verified sample of 95 separate literal oceanic archipelagos. A polygon-based island and archipelago crosswalk, harmonized study effort, and observed movement would be necessary before island-specific source mechanisms could be claimed.

## Next scientific gate
Keep the 76 reserved studies' taxa sealed. First determine strict same-month paired-event estimability in those 76 from physical metadata ONLY; this is necessary because five of 19 pilot studies dropped out under stricter monthly rules. Then freeze a study-blocked calibration-only reference versus geometry-added C contrast, and ensure target-study/time support gates before species-response scoring.

eBird off. No original global mammal heldout reopening, no BALA/Helgeland/Hopson/Gawecka reruns, no movement or demographic effect measured, zero newly admitted pristine confirmatory systems. GEB scientific HOLD unchanged.
