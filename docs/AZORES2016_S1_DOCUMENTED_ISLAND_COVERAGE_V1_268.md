# Macaronesian S1 × Azores 2016 island checklist: source-version trap and documented distribution

2026-10-20, v1.268. **Executed source-locked retrospective cross-source case audit; not an independent prospective island-extinction experiment.**

## 1. Main result and source identity

The previously frozen S1 sample (Orihuela-Rivero et al., 2025, Global Change Biology, DOI `10.1111/gcb.70072`) contains 24 **Well-supported, island-level local extirpation** records for 20 Azorean taxa, including four taxa with reliable losses on two islands. All 20 literal source taxa were unambiguously matched to the official University of Azores 2016 Darwin Core checklist: [original GBIF Portugal IPT v1.2](https://ipt.gbif.pt/ipt/resource?r=uac_checklist_acores&v=1.2). Two match by the exact source scientific-name field and eighteen by a *unique* source binomial (no synonym guessing); zero ambiguous or unmatched.

Published-author CSV/DwC-A source checksum `SHA256 07be180d52f08e5051d63c5364dc856d8b0e811a83a9c26c920780138bb3fc79`, 1,603,288 bytes; original CSIC S1 XLSX `SHA256 767f9ea095660d77babb8eb74b2eb714e8cdc38cb0c6861051416a7c0039b0e1`, 332,776 bytes.

The GBIF list contains 15,256 taxon rows and 22,629 taxon-distribution rows, including 1,110 species-level vascular plant taxon keys. The frozen strict `occurrenceStatus=present` filter yields 3,940 vascular species×named-island checklist-positive pairs, of which 1,174 also have `establishmentMeans=native/indigenous/endemic`. The remaining distribution statuses include `rare`, `irregular`, `doubtful`, `absent` and missing; we did **not** posthoc reclassify these as confirmed presence or turn omitted taxa/islands into true absence. Species-specific records or names were not exported.

## 2. The crucial contradiction

**Thirteen of 24 reliably locally extirpated taxon–island cases were also labelled `present` for that exact island in the 2016-published checklist.** Twelve of those thirteen had a *last-record year earlier than 2010* in CSIC S1. The remaining one had last-record year 2010 or later.

The distribution archive actually has nonempty `eventDate` for **all 22,629 distribution rows**, but **every one is the *same nominal year `2010`***. That is not site- or survey-level verification of a population being alive in 2010 or 2016; this checklist was derived from a 2010 biota compilation. The overlapping `present` status is a **source snapshot/historical interpretation discrepancy**, not verified recolonization, proof of persistence, or evidence the reported extirpation is wrong.

Thirteen ambiguous same-island status pairs show why a georeferenced checklist cannot be assumed to provide independently observed time-ordered donor population status. The original S1 label records a last observation, not a scientifically known precise population-extinction date.

## 3. Recorded other-island footprint does not establish demographic rescue

**18/20** loss-affected Azorean taxa have a `present` label on at least one *different* island; all **4/4** taxa with two confirmed local losses have another 2010-era island checklist `present` label. However, because the atlas does not measure viable populations in a contemporary or pre-extinction demographic census, these are **documented geographic occurrence histories**, not 18 confirmed living donor taxa or four rescue opportunities.

Stratifying by count of confirmed S1 island losses, the mean number of **other islands with `present` labels** is **3.625** among 16 single-loss taxa versus **3.75** among four double-loss taxa. There is no obvious large contrast of other-island *documented footprint* in this tiny case-only crosswalk, but this does not correct for historical sampling or habitat and should not be read as a no-effect test.

| Audit | Value |
|---|---:|
| 2016 checklist taxa / island-distribution rows | 15,256 / 22,629 |
| Nominal checklist `eventDate` | 2010 for 22,629/22,629 rows |
| S1 reliably locally lost Azorean taxon-island cases | 24 |
| S1 affected Azorean taxa uniquely identified in checklist | 20/20 |
| S1 lost island also marked `present` in the 2010-era list | **13/24** |
| Taxa with other islands marked `present` | 18/20 |
| Repeated-loss taxa with other islands marked `present` | 4/4 |

## 4. What has and has not been established

- **Established:** exact cross-source taxon match, actual nine-island locality coding, precise category-preserving documented island historical footprints, and *noncontemporaneous date/status limitations*.
- **Not established:** the full historically occupied at-risk taxon–island frame, standardized observation effort, actual current survivors, viable donor populations, colonization, demographic rescue, source irreplaceability, or a cross-archipelago causal configuration effect.
- **Not re-used:** Macaronesia S2/S3/S4 response values; old Structural 529 mammal heldout and BioTIME/RLS protected biology; eBird.

## 5. Next ecological rather than methodological test

The correct next data source is **independent, dated post-2016 field records**, not another snapshot of lists carrying nominal 2010 dates. University of Azores has published documented sampling-event/occurrence archives with known island identifiers and actual observation dates: São Jorge PRIBES (DOI `10.15468/drbja9`, events July 2020), Pico PRIBES (`10.15468/vk4y7k`) and Graciosa/Santa Maria (`10.15468/hgyfh3`). Before joining any S1 labels, independently verify their dated observation event/occurrence identity and native status; non-detection within a targeted new survey is not an island extinction.

Any modern field positive may independently document a taxon on a given island at that date. But it does NOT backcast a viable source at the older S1 loss date and does NOT demonstrate immigration from another island.

## Verification and code

- Initial source DwC-A source-only preflight passed: [GitHub Actions 39385161108](https://github.com/zuizui0223/Structural/actions/runs/39385161108).
- Actual S1 × 2016 archive source-key regression and source join passed: [GitHub Actions 39387757586](https://github.com/zuizui0223/Structural/actions/runs/39387757586).
- All original biological files were SHA256 locked, no current individual species or event rows were publicly uploaded, and a synthetic regression demonstrated that the Distribution `coreid` foreign key is the original Taxon core ID (0), not merely the descriptive `taxonID` field.
- Result freeze: `development/azores2016_S1_documented_island_coverage_result_v1_268.json`. The later rerun with date vocabulary independently confirmed `eventDate=2010` for every distribution row.

Status **scientific HOLD** for the original mammal GEB mechanisms and for any assertion of contemporary source–sink rescue. Zero new confirmatory island-dispersal systems admitted.
