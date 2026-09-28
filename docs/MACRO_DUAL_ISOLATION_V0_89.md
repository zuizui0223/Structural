# Two-taxon macro dual-isolation design v0.89

## Macro core

The primary evidence base is now:

1. the pristine 5,592-island native-mammal occurrence system; and
2. GIFT v3.2 native angiosperm island checklists.

The 42-island boreal lake system is retained only as a possible local-scale contrast. It no longer controls progress of the macro paper.

## Primary ecological question

External isolation from major landmasses and internal isolation from a focal species' occupied insular source pool are different ecological axes.

The confirmatory question is whether species-conditioned internal source continuity adds held-out occurrence information after a strong reference already represents environment, island area/state, external isolation, generic archipelago context, global occupancy breadth, **species × regional-pool structure**, and direct/diffuse occupied-source proximity.

The primary estimand is equal-weight block mean `loss_C - loss_R3`. Negative values favour the candidate.

## Leakage control

Every source-derived predictor is leave-block-out.

For each held-out archipelago/regional block, the entire block is removed before computing global occupancy breadth, species × regional-pool prevalence/membership, nearest occupied-source distance, diffuse source pressure, and candidate continuity. A held-out island can never be a source for itself or another target in the same held-out block.

## Mammal transport

v0.64 closed unauthenticated URL-variant retries after three 401/403 failures before any response byte was read.

v0.89 opens one new route only: authenticated Dryad API access using the already implemented v0.73 short-lived bearer-token mechanism. The current 2024 matrix remains pinned to 60,486,843 bytes and SHA-256 `32bf3f077af7e66ddcbf05fc675d6c51656f59111c27cd37129e14c658430fa6`.

Before the independence gate, only the first CSV field of the header and each of the 5,592 rows may be decoded. Species headers and all 0/1 cells remain sealed. Raw response bytes are deleted before artifact upload.

## Historical overlap gate

A raw numeric ID collision test between the 318-island and 5,592-island systems is **diagnostic only**. The two sources do not have a frozen common identifier namespace, so non-collision cannot establish independence.

The final overlap decision must use only response-independent island identity metadata/geography. Any matched historical island is removed from the 5,592 target population before partitions or models are frozen.

Species overlap is audited separately with response-blind species metadata; shared species do not by themselves create shared response units.

## GIFT freeze

The plant lane is frozen to GIFT database version 3.2 and native Angiospermae island checklists.

The first call is metadata-only:

- `complete_taxon = TRUE`
- `floristic_group = "native"`
- `complete_floristic = TRUE`
- `geo_type = "Island"`
- `suit_geo = TRUE`
- `remove_overlap = FALSE`
- `list_set_only = TRUE`

No species composition, richness, source feature or C−R3 value may be requested until the returned metadata and final archipelago eligibility are separately committed.

## Evidence accounting

A-Islands, Tanzania and the completed 318-island mammal system remain discovery/motivation only. They do not count toward the confirmatory denominator.

No ecological result is produced by v0.89 itself.
