# Azores trail vegetation: independent two-island observational test and response-sealed admission (v1.291–v1.295)

**Current result (v1.296, 2026-10-24):** This older note records the original response-firewall preparation, not the latest conclusion. The later [actual field execution v1.295](https://github.com/zuizui0223/Structural/actions/runs/40074317603) scored 4 independent trails; the [source-free v1.296 synthesis](AZORES_TRAIL_WEIGHTING_NATIVE_RICHNESS_DISSOCIATION_V1_296.md) confirmed that original equal-trail and equal-island contrasts were −0.0344 and −0.1250, whereas nonindependent area-group weighting flips the sign to +0.0979. On two trails, the direction of native/alien ratio change disagreed with the direction of absolute native richness change. No causal trail effect or independent archipelago generalization was established. **Use the v1.296 document for scientific conclusions; v1.292 strict source Event design remains terminal.**


**2026-10-24 · Primary ecological question:** Within independently surveyed native forest trails, does native-versus-introduced plant composition differ between the trail edge and nearby forest interior after matching sampling line positions? This is an empirical extension beyond 2013 Pico vegetation co-occurrence, not a retest of the old rare historical-loss cohort, and **not a dispersal/rescue experiment**.

## External original source and what is new

Carvalho, Petrone, Elias & Borges (2026), Trail-based plant community monitoring in Azorean native forests (Terceira & São Miguel, 2017–2019), DOI 10.15468/ysbzk7 (University of the Azores / GBIF, CC BY 4.0). Two islands and four published trails, with three on Terceira and one on São Miguel. Original version v1.4 ZIP SHA256: **c6c6ad82e268759aade344528c3649459ed323053969c1ef8053f3f518298da7**.

The data describe transect-line observations inside original **2 × 10 m plots**: site positions 0, 50, 250 m from trailhead, best-preserved reference (max), and 50 m reference (Control_50); three perpendicular/edge physical plots per area. Plot 1 is along the trail edge and has an extra 25-cm line unavailable in plots 2/3. Thus 210 Event records are **not 210 independent forest plots**. The science must be scored at the physical plot and independent trail levels, not line rows.

## Verified original field-source sample boundary BEFORE opening any plant Occurrence value

- [v1.291](https://github.com/zuizui0223/Structural/actions/runs/40072919362) ZIP directory and Darwin Core meta.xml ONLY: PASS, 3 synthetic tests; original Event/Occurrence rows opened 0; Event has eventID/year/island, Occurrence has scientificName/establishmentMeans/taxonRank/coreid.
- [v1.292](https://github.com/zuizui0223/Structural/actions/runs/40073159920) author's documented identifier grammar was **not perfectly realized** in the official v1.4 Event values. Frozen strict physical eligibility STOPPED; 210 Event values opened, **no plant Occurrence**.
- [v1.293](https://github.com/zuizui0223/Structural/actions/runs/40073337648) safe Event-only diagnostic: source contains 127 records with 2017 Event prefix and 83 with 2019. Unexpected area suffixes 19, unexpected plot suffixes 4, year column mismatches 6 and eventDate mismatches 7 (overlap is possible). Exactly 9 records have original area code control50 rather than the published Control_50 notation. No biology opened.
- A **new, explicitly retrospective Event-exposed** (not pristine confirmatory) v1.294 physical analysis was frozen prior to opening any plant species rows. It treats control50 as the already published 50-m reference area, excludes any unknown area/plot/line code and year-mismatched row rather than reassigning site identities, and requires <=20% exclusion and complete shared 50/100/150-cm lines for original plot1 versus plot2/3.
- [v1.294 original Event-only result](https://github.com/zuizui0223/Structural/actions/runs/40073734413) PASS: 210 original Event rows, 193 structurally parseable, 17 excluded (10 unrecognized sampling areas and 7 mismatched year fields), **17 physically comparable trail×year×area groups**, 14 Terceira and 3 São Miguel. All four published trails are represented (three Terceira and one São Miguel). Exactly **147 Event lines** comprise the frozen, matched physical score opportunity. Original plant rows opened **0**. SHA256 of the original-source-Event inclusion-key set: 21f681ad97ecb08d25d21bd147cb9650f0924ab3e74ccb51145f93a2ac65fce8.

The earlier v1.292 strict gate remains permanently failed. v1.294 is a genuinely separate, lower-evidence retrospective design that excludes structurally uninterpretable original Event records **based on source metadata, not plant outcomes**. No relabel of the earlier failure as an independent confirmed score is justified.

## Next biological comparison frozen, NOT YET INTERPRETED in this note

[v1.295 protocol](../development/azores_trail_native_alien_response_contract_v1_295.json) specifies, for each matched original trail×year×area group:

1. Take only three common 50/100/150-cm line samples in original edge plot1 and in originally matched interior plot(s)2/3.
2. Join original Occurrence coreid to Event, classify strictly native/indigenous/endemic versus introduced/invasive/naturalized species from original publisher vocabulary, and de-duplicate same species within a physical plot.
3. Calculate each plot's native-to-alien log richness ratio, with fixed +0.5 stabilization; compare average interior log ratio minus edge log ratio within the *same* trail×year×area group.
4. Average matched contrasts within each original trail and report the four trail-level outcomes, with two island contexts and **no spurious independent-island p-value**. A positive contrast would indicate relative native-plant enrichment in trail interiors.
5. **STOP without a score** if original Event↔Occurrence join completeness is <95%, unclassified species-rank nativeness is >20%, or either island lacks at least three strictly native and one introduced species in the matched sampling frame. Never relax conditions or re-read exposed plant labels to rescue a preferred result.

The two islands are not independent replicated archipelagos, and the one São Miguel trail is not three independent Terceira trails. Any source result remains descriptive observational native forest biogeography, not a randomized tourism or invasive plant intervention, actual species survival or immigration.

## Relation to the standing Structural ecological evidence

The robust Pico 2013 observational pattern remains: historical local-loss flora co-occurs with more non-focal native taxa and less frequently with alien taxa in the original intact native forest plots; these are site-level co-occurrence associations with no demonstrated mechanism. The external trail study is designed to ask **whether the general native/alien habitat filter varies along a quantified human disturbance gradient**, not whether each originally S1-listed taxon is demographically rescued by another island.

GEB mammal geography/predictive mechanism scientific HOLD, fresh confirmatory admissions zero, old MOVECLIM/ForestEco2 original biological data not reopened, protected mammal/BioTIME/RLS and Macaronesia S2/S3/S4 unopened, eBird off.
