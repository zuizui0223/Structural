# BioTIME v1.254 — corrected biological-pilot replication unit

**Science correction, 2026-10-19. Original 19-study biological pilot outcomes and counts remain frozen; no pilot/holdout response was reopened.**

Earlier `docs/BIOTIME_BURNED_PILOT_DETECTION_RESULT_V1_252.md` reports the valid study-ID description: 13 of 14 response-estimable STUDY_IDs have higher sampled 0→1 rate at 5+ compared with 1 observed source sites, and 1 is tied. Those 14 study IDs, however, cannot automatically be counted as 14 spatially independent replicated networks.

The later response-opaque GIS-key audit [run 39217432431](https://github.com/zuizui0223/Structural/actions/runs/39217432431) examined only physical study, site, year and month identities. Two pairs among the 14 pilot-estimable study IDs share a study geography under the prospectively fixed >=80% site-containment and >=5 shared-sites rule:

- **273 / 589**: these two study IDs belong to the same high-overlap physical site/time survey-frame component; both had positive 5+-versus-1 observed 0→1 rate differences.
- **376 / 377**: these two study IDs overlap geographically even without meeting the full >80% time-frame duplicate definition; both had positive 5+-versus-1 differences.

Study ID **558** is the earlier tied 0→1 group and has no other of the 14 response-estimable pilot studies in its physical network component. Collapsing within-pilot geographic components yields **12 conservative pilot geography proxies**: **11 with a positive directional gradient** and **1 with an apparent zero tie**, rather than 13 / 14 independently replicated studies.

These are counts of observational direction, not a formal spatially independent sign-test or migration effect. High detection prevalence and study-level sampling organization remain competing explanations. We have *not* recomputed the underlying ecological transition values or opened the reserved 76-study species responses.

Implication: the first inference must be conditional on survey-network identity, not arbitrary database STUDY_ID, just as the 76 reserved study IDs reduce to 33 prospective physical-network representatives after screening and duplicate control. Even these 33 cannot be called literal island archipelagos without an independent polygon-based site-origin crosswalk.

Frozen original empirical result remains 00=91,967; 01=6,274; 10=8,584; 11=16,759 from 6,838 eligible matched site-month-year samples and 123,584 taxon-site pairs. The separate source-independent v1.254 audit can change the estimated effective *replication denominator*, not the original fixed detection counts.

Evidence class: retrospective burned-pilot description with response-free later metadata correction. eBird unused; original mammal and reserved BioTIME response firewalls intact; GEB scientific HOLD.
