# DATASAPROX: historical independent-provider surveys and publication Table 7 scope (2026-11-24)

## Decision

**Sampling-history geography PASS, species-specific accessible source pool NOT MEASURED, resource × pool effect NOT TESTED.** A past unrelated original survey near a later survey is documented source survey effort, not a known occupied beetle donor population or a forest connectivity corridor.

Original public DATASAPROX v1.6 (Bosc et al. 2026 Biodiversity Data Journal DOI 10.3897/BDJ.14.e187021), publisher IPT https://ipt.gbif.fr/archive.do?r=datasaprox&v=1.6, CC BY 4.0; pinned exact ZIP SHA256 4163a2f8f72d756e74f64319b8e199b284ecc6414196147e4465d342d7dcb6d0. All original organism taxon, abundance and scientificName values remained UNOPENED. Only event/project/time, geo position and uncertainty, survey-method metadata used.

## First actual original-data result — geographic survey support

Source-only Actions run https://github.com/zuizui0223/Structural/actions/runs/45208778779 SUCCESS. Anonymous aggregate-only artifact #14833699611 SHA256 534e45184b3b6f47c32b79eae183bacc516875d000bfb38a71a224de5802fd97.

- Original sampled occurrence rows metadata-streamed 675,525; 65,642 original producer×project×event keys; 1,133 method-contradictory keys excluded; 64,509 method-consistent retained. One further original coordinate-conflicted event excluded geographically.
- Strict WGS84 point, original declared positive coordinate uncertainty <=1000 metres and 1997–2025 source calendar year: 6,065 eligible original event keys, collapsed to **1,328 source producer×project×point×year location-years**, **899 source producer×project×point locations**, **60 projects and 5 nonblank producer IDs**.
- Among **692 later 2016–2025 source location-years**, a strictly earlier different ORIGINAL project within predeclared 100km: **561/692 (81.07%)**; within 200km: **595/692 (85.98%)**.
- Stricter earlier DIFFERENT ORIGINAL PRODUCER within 100km **139/692 (20.09%)**, within 200km **209/692 (30.20%)**. All donor dates strictly earlier than corresponding target; no same project donors. Geographic bands are arbitrary frozen *survey coverage* radii, NOT beetle dispersal distances.
- The initial source-only field gate stopped on incorrect coordinateUncertaintyInMetres spelling. Native original meta.xml field coordinateUncertaintyInMeters was verified before any original response opening and corrected without changing source counts/radii; erratum FOREST_DATASAPROX_GEODATUM_SOURCE_FIELD_ERRATUM_20261124.md documents the correction.

## Second actual source result — published author sampling-scope crosswalk

Source-only Actions https://github.com/zuizui0223/Structural/actions/runs/45209826360 SUCCESS. Aggregate-only artifact #14834772987 SHA256 9d991d3f7899eff58bee1e783c6546de7a70be92a5e8460d7589380342a7cce3. Original publisher JATS Table 7 read from https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12993481/fullTextXML with DOI identity verified, 484 rows, 482 unambiguous project identities. Original producer/project exact-match after NFKC/casefold/whitespace only, no fuzzy joins.

- Among the same **60** source projects, **40** author-classified complete, **19** partial, **1** unmatched; 40 complete-labelled projects from **four known producers**.
- Original eligible 1,328 location-years: **884 complete-labelled, 415 partial, 29 unmatched**.
- Among 884 complete-labelled source histories, **570 later location-years from 2016–2025**.
- Earlier complete-labelled DIFFERENT PROJECT survey <=100km for **410/570 (71.93%)**; earlier complete-labelled DIFFERENT ORIGINAL PRODUCER <=100km **122/570 (21.40%)**, and <=200km **190/570 (33.33%)**.

**Critical inferential limitation:** The author's complete/partial is itself derived from observed taxon/family richness and dominance. It is NOT verified complete taxonomic census or known detection-zero frame; screening on it can select observed richer samples and induce ecology-dependent selection bias. Thus 122/570 means only historical independently sourced *survey opportunity*, NOT actual species-specific occupied source populations. Source sample/location-year keys remain nonindependent of their parent source projects, 100km is not a beetle dispersal kernel, and no actual source forest wood/resource data has been joined.

## Ecological admission decision and next main goal

**PASS:** authenticated original source, time-order restriction, site coordinate/accuracy, distinct original producer versus project independence, taxonomy-scope publication metadata.
**HOLD:** independent species-by-source presence/effort and zero sampling semantics; any true absence inference; matching original field plot×actual host tree/decay/wood habitat and site sampling period; same taxon resolution; enough independent forest/region blocks; baseline E2 and resource×pool E3 genuine held-region prediction.

Do not score resource × pool or infer a general forest ecological mechanism until a NEW source supports all gates. Distinguish this metadata feasibility result from past PREDICTS 39-study reference-relative taxon replacement and existing Finland/Germany/Ecuador/Traylor original beetle outcomes, all unchanged. No eBird or TinyFish. Draft PR #469 unmerged.
