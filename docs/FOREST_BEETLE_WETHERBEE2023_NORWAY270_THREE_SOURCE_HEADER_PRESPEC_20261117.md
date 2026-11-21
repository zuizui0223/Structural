# Norway Wetherbee 2023 270-site source: original site×taxon×trait column-level audit (2026-11-17)

## Locked publisher source and active problem

[Original publisher manifest-only CI #44082232916](https://github.com/zuizui0223/Structural/actions/runs/44082232916) succeeded and verified 8 exact files at [Zenodo 10.5281/zenodo.8272489](https://doi.org/10.5281/zenodo.8272489) with publisher MD5. The published Wetherbee et al. 2023 source reports 270 forest sites from eight historical Norwegian forest beetle survey projects (1997–2007), 339 obligate saproxylic beetle species. The original article already associates predator fraction, wing and body morphology with forest naturalness (prior art). Norwegian site collections may partly overlap previous Burner 2022 original Norway 468-site source; field independence remains untested.

The identified **THREE original candidate field tables** and immutable publisher metadata are:
- `GBIFnormalized_SpcSite_matrix_FD_unique.csv`: 2,759,229 bytes, original MD5 `1cc6d3599dccd80b0889b55b5d571eda`;
- `GBIFnormalized_Trait_RAW_df.csv`: 485,427 bytes, original MD5 `da5aa42586fe6994deb039565a782f8a`;
- `SiteInfo_Alltaxon_Pred_Detri_SxFD.csv`: 403,751 bytes, original MD5 `2b0d5e8a7c209a958b6034838d1fd1`.
Five additional published archives (.RData, .xlsx, .R files, small ordination CSV) remain unopened. File names suggest original matrix, traits and site information but their actual keys, resolution and measured deadwood resources are **unknown**.

## ONE new source-only header gate, before any species responses

1. Fetch only the three exact official CSVs from publisher Zenodo 8272489, once each; require fixed file size and MD5 from the published version. All file bytes remain temporary private runner memory, no redistribution. Only FIRST CSV header line is parsed; original numerical data, species values, site labels, guild values, habitat/wood values and other rows are neither selected nor scored.
2. Record delimiter, header column counts and only **generic whitelisted field-name matches** for: site/plot physical key, original project, region, survey year/period, trap/method/effort, author-host-tree or deadwood resource measurements, managed/near-natural class, species/taxon, functional trophic guild and other trait names. Never print unidentified column headers, species names or original author site IDs.
3. For wide species×site matrix layouts with no explicit original site header, report width only; do not assume each column is an independently sampled forest. In source trait table, taxonomy names might not match prior Burner (Host_tree); a trait-table header is not evidence of harmonization. A field named `deadwood` requires the author definition and units before being used.
4. Only if the original site/project/trap/year source fields have unambiguous semantic names and an authoritative species–site join will a subsequent **separate** method/source-lineage-only crosswalk be eligible. No external ecological replication until all eight original project lineages are checked against previous Norway collections. No ecological prediction/model in this gate.
5. A file download 401/403 is access STOP, not ecology null. A technically successful header read is source compatibility progress, not a novel biological result. Old Georgia 40-site numeric vs mixed header mismatch stays scientific HOLD; Piccini 8-site p=.09375, Finnish VD10, Burner, Thai, PREDICTS, NEON, BALA and GEB biological scorers stay SEALED, no eBird/TinyFish or PR merge.
