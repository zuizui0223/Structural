# UK NFI canopy/subcanopy arthropods: original 83 plot/year method-pairing source VERIFIED, ecology not yet tested (2026-11-19)

## Current mainline result — source opportunity, not an arthropod effect

The original publisher [NFI Canopy & Subcanopy Arthropod Communities](https://environment.data.gov.uk/natural-capital-ecosystem-assessment/search/2b8a8f17-3745-43d1-bb32-0d509230f158), UK Forestry Commission (2026 update), actually contains a geographically wider England **source survey panel of 83 candidate `NFI_region × Plot_ID × Year` contexts in 8 source NFI regions with simultaneously deployed `Canopy` and `Malaise` method classes in ALL 83 contexts**. In **77 of 83** contexts both source methods have at least one DNA-sequenced sample with an overlapping original deployment interval. This is a new, original-data **sampling support result**, not a new forest biodiversity response, formal physical independence, common-method vertical beta, or thermal refuge mechanism.

### Immutable publisher and audit chain

- Original archive: `eDNA Woodland Canopy Subcanopy Data 2023-26.zip`, **486,883 bytes**, SHA256 `ce3a21377238cc87bde7683917f59a771d20f8e24e81ddf47915362b92281ff4`; original two CSV headers of **24** sample-metadata fields and **328** response-bearing wide-table fields.
- [First publisher archive/header CI #44305867348](https://github.com/zuizui0223/Structural/actions/runs/44305867348), and [original 24 author field names CI #44306484671](https://github.com/zuizui0223/Structural/actions/runs/44306484671), verified exactly `Plot_ID`, `NFI_region`, `Trap_type`, `Trap_height_m`, `Tree_species`, `DBH_cm`, `Sample_ID`, `Sample_sequenced`, sample date fields. No original CSV body rows read then.
- [Original sampling metadata-only CI #44446862855](https://github.com/zuizui0223/Structural/actions/runs/44446862855), artifact **#14493387656**, ZIP SHA256 **`ae93b060540d0c4ce45efd111a7c562cb18fe6b980445658b112e2f22b160fb8`**: **331** unique `Sample_ID` records, 83 `(NFI_region,Plot_ID)` candidates, 8 NFI region codes; sample rows 2023 **95**, 2024 **116**, 2025 **120**, 2026 **0**; 316 `Sample_sequenced=yes`; 885 source-valid deployment intervals from the 1–3 original date rounds. `Delocation_unique_ID` counted **81** masked geography categories and is not the original physical plot key. Conservative unambiguous lexical `Lindgren` token 0 / `Malaise` 165 / other 166: this was a **classification vocabulary issue**, NOT no canopy traps.
- [Response-blind literal author `Trap_type` categorical-only CI #44447401005](https://github.com/zuizui0223/Structural/actions/runs/44447401005), artifact **#14493921908** ZIP SHA256 `e68396b81c9d934fb4baed8a0e9e6a5229a61ab7ac94a9525ddbd67f2dd27d0c`, fixed original values **`Canopy` 166** and **`Malaise` 165**. Publisher independently describes **Lindgren (canopy) and Malaise (subcanopy)**. The earlier token-gate 0 literal Lindgren remains historically true; no biology was opened to select a favorable alias.
- [New original paired source-method metadata CI #44447949840](https://github.com/zuizui0223/Structural/actions/runs/44447949840) **SUCCESS**, artifact **#14494207564**, ZIP SHA256 **`72f948186ec7c0997d9dda124b97d5b4f80b1deeb52462373b216bdcd7ee17d2`**; preregistered [one-pass source method](FOREST_NFI_ENGLAND_2026_ORIGINAL_CANOPY_MALAISE_PLOT_YEAR_PAIRING_PRESPEC_20261119.md) before rerunning sample-data calculations; all 328-column OTU/species biological data rows **0 opened**.

## Exact original-source denominator and paired design

| Source field unit or metadata diagnostic | Confirmed original-data aggregate |
|---|---:|
| Original `Sample_ID` values, all unique | **331** |
| Source trap classes `Canopy` / `Malaise` | **166 / 165** |
| Candidate `NFI_region × Plot_ID` (site independent NOT certified) | **83** |
| Original `NFI_region` categorical regions | **8** |
| `NFI_region × Plot_ID × Year` candidates | **83** |
| Both source methods, same candidate plot × year | **83/83** |
| Both original method deployments overlap | **83/83** |
| Both original methods have sequenced sample and overlapping dates | **77/83** |
| Original site/year with `Surveyor_station` label shared across both methods | **83/83** |
| Original site/year with at least one `Tree_species` label shared across methods | **59/83** |
| Both method heights finite nonnegative | **3/83** |
| All recorded Canopy heights strictly above recorded Malaise heights | **0/3** |

All 83 annual source candidate plot contexts contain **two `Canopy` sample records**; **82** contain two `Malaise` sample records, and **one** contains one `Malaise` record. Thus the 331 rows are NOT 331 forests, and the 885 trap-round intervals are NOT 885 independently sampled sites. Annual region×plot matched-pair counts: **2023 24**, **2024 29**, **2025 30**, **2026 0**; across eight unnamed regions, candidates per region **[5,6,7,8,11,14,14,18]**. Publisher program title covers 2023–26, but this **actual archive** has only original `Year` values 2023–25.

Strict observed height availability differs by method: original `Canopy` **122/166** sample rows with finite height, `Malaise` **6/165**; source both-method plot/year measured heights only **3**. Do NOT impute missing height, use categorical layer as a meter axis or describe all source `Canopy` traps as physically above `Malaise` within the same plot.

## Scientific interpretation

A genuinely new England geographically spread forest **source survey opportunity** exists, with 77 paired-date and both DNA-sequenced annual plot contexts. It provides a credible candidate for **method-conditional community composition and tree-type/environmental association** when original `Sample_ID` ↔ response columns, exact taxonomy, source sequence quality, physical sample unit and regional independence are separately verified.

**Do NOT** directly contrast `Canopy` vs `Malaise` read counts or observed richness as evidence of vertical niche partitioning, because layer and trap technology are inseparable. OTU read counts are sequence counts, not arthropod individual biomass or numbers; incomplete sample counts and trap effort remain sampling covariates. The associated `Tree_species`/sample-tree DBH is not a stand-level inventory of host resource availability; there is no independent source microclimate/deadwood field in this 24-column sample table. No activity-based movement, forest resilience, causal resource selection or three-dimensional thermal refuge follows from this source audit.

**Next frozen technical gate:** before the first 328-column biological response row, compare the 328-table FIRST HEADER labels against the 331 original `Sample_ID` values (including 316 source `Sample_sequenced` yes) via exact source-name matching in private runner memory, returning only count-based anonymous membership and corresponding 77 candidate plot/year both-method cohorts. If sample header orientation does not match, STOP and inspect author source codebook without opening response. Verify original NFI sampling framework/evidence pack before treating 83 plot keys as independent physical forests or fitting a biological out-of-region model.

Previous Finnish/Carpathian deadwood/guild outcomes, PREDICTS alteration +0.0942, Thai/Brisbane canopy, NEON and BALA/GEB historical heldouts unchanged, no eBird/TinyFish, PR #469 Draft/unmerged, `main` unchanged.
