# Global island mammals — source-pool handoff pre-intake v0.1

## Status

**HOLD before v0.11 intake.**

The current Dryad file identities are frozen from metadata only. The presence/absence matrix has not been downloaded or parsed by Structural in this lane.

## Why this is a strong island-biogeography test

The source dataset contains an explicit mammal presence/absence matrix for **5,592 islands** worldwide. Island IDs link to a separate island table containing physical, climatic and historical-isolation variables.

The source construction is unusually useful for a prospective response firewall:

- the ecological response domain is explicitly binary **0/1** before access;
- introduced mammals were removed by the source;
- fully aquatic and marine semi-aquatic mammals were removed;
- the source analysis distinguishes bats from non-volant mammals;
- the island table contains present and past isolation covariates;
- published analysis code uses centroid-coordinate fields in the island analysis object.

This directly avoids the endpoint-code ambiguity that terminated the Indo-Pacific atoll pilot.

## Important population boundary

The database excludes islands on which the source found zero mammal species.

Therefore this is **not** a test of the probability that an arbitrary island is colonized by mammals.

The estimand is conditional on the source-curated universe of mammal-occupied islands.

The source also restores native mammals lost through human-driven extinction. The endpoint is therefore best interpreted as **native/historical occupancy state**, not contemporary detection or contemporary colonization.

## Primary ecological hypothesis

The primary question remains the A-Islands source-pool-handoff hypothesis:

> On the most presently isolated mammal-occupied islands, species-conditioned continuity with occupied insular source islands should retain occurrence information beyond current isolation, past land-bridge isolation, island area, climate, generic island-network context and direct/diffuse occupied-source proximity.

A-Islands remains discovery evidence only.

The terminated Indo-Pacific atoll system contributes no direction and no confirmation.

## Reference ladder

### R0 — environment and realm
- zoogeographic realm;
- mean temperature;
- temperature variation;
- mean precipitation;
- precipitation variation;
- elevation variation.

### R1 — classical/historical island state
R0 plus:
- island area;
- current isolation (source SLMP-based isolation);
- past isolation / LGM mainland connection state;
- climate-change velocity.

### R2 — generic physical island network
R1 plus response-independent generic network context derived only from frozen island centroids.

### R3 — direct/diffuse occupied source context
R2 plus:
- nearest occupied source distance using training islands only;
- multi-source pressure using training islands only.

### C — source-conditioned network continuity
R3 plus species-conditioned multi-hop source connectivity using training occurrences only.

Primary loss contrast:

    C - R3

Negative held-out log-loss difference is favourable.

## Extreme-isolation prediction

The primary regime is the upper 25% of the frozen **current-isolation** distribution in the model-target universe.

Prediction:

    (C - R3)_extreme < (C - R3)_non-extreme

q70 and q80 may be directional sensitivity checks only and cannot rescue a failed q75 primary.

## Dispersal-mode secondary

The source paper reports different relationships with isolation for bats and non-volant mammals. Before opening the response matrix, this motivates a secondary mechanistic prediction:

- **bats** should retain relatively more information in the present occupied-source network;
- **non-volant mammals** should retain relatively more information in the past-isolation state.

This is secondary and cannot rescue the primary source-pool-handoff test.

A taxonomic-order mapping must be frozen from an external source before this secondary can be scored.

## Exact Dryad identities

Current Dryad version: **6**, modified **2024-06-17**.

- `Appendix_1_presence_absence.csv`
  - 60,486,843 bytes
  - SHA-256 `32bf3f077af7e66ddcbf05fc675d6c51656f59111c27cd37129e14c658430fa6`
  - role: **response**
- `Appendix_2-dryad.xlsx`
  - 1,066,391 bytes
  - SHA-256 `fdcfc92bfa67e1ccf4d468fe2c7222bcb5919a1bce56d272b19d42525c234960`
  - role: **mixed**
- `mammal_insularity_from_IUCN.csv`
  - 182,298 bytes
  - SHA-256 `705576b9ddb5de369c8f87e37f5fb47ed83e12e4f9dc6946443630034062f314`
  - role: response-blind species metadata candidate
- `README.md`
  - 8,720 bytes
  - SHA-256 `1766a64daf93e4367fea19e2b395883ac7d6acd29bdc490bfe8131d98fecde68`
  - role: documentation

The metadata probe made **zero file-content requests**.

## Mixed-file firewall requirement

Appendix 2 is not globally safe because it contains both response-independent island predictors and response-derived mammal richness/endemism summaries.

Before any island covariate value is read, a schema-only audit must prove that safe columns can be isolated.

Intended safe columns include:

- island ID;
- centroid latitude/longitude;
- area;
- current isolation;
- past isolation;
- climate velocity;
- temperature mean/variation;
- precipitation mean/variation;
- elevation variation;
- zoogeographic realm.

Forbidden columns include all richness, SIE and pSIE summaries.

If safe and response-derived columns cannot be separated mechanically, this candidate stops before response access.

## Next step

Only the following is authorized next:

1. resolve the Appendix 2 Dryad download link through metadata;
2. verify exact bytes against the frozen SHA-256;
3. inspect workbook sheet names and header cells only;
4. emit no row values;
5. freeze a column-level mixed-file firewall.

v0.11 intake, pilot response and confirmatory response remain unauthorized.
