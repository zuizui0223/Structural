# Independent host-tree and saproxylic beetle forest cohort: ORIGINAL SOURCE QUALIFICATION (2026-11-15; response-unopened)

## Scientific starting point and primary goal

The Finnish 142-author-forest same-year original exploratory test is already frozen: local total-deadwood z-score `VD10` improved geographically held-out beetle Host_tree guild composition prediction by **cell-equal ΔHellinger²=+0.00024237**, block-bootstrap [0.00012123,0.00035658], conditional block-signflip p=.015 (9 blocks), while a separate source site trait-label null found D=+.035237. This is modest **within the same observational network** and lacks separately measured **local wood tree-species identity**. Neither effect will be re-optimized. PREDICTS +.0942, NEON static canopy-height +.0349/p=.1759, GEB and BALA holdouts remain sealed.

**Current single target:** qualify a genuinely independent forest cohort with (A) original site/plot-keyed beetle species incidence/abundance, (B) **actual site-matched wood tree identity or species-specific host-resource measurement**, (C) source survey method/time/effort, and (D) enough independent source forests/study regions for a preregistered *exploratory* external test. First assess original **source availability and grain only**. Do not score any ecological response until the entire sample hierarchy and primary estimand are frozen.

### Priority A — Ramberg et al. 2025 Sweden, independent burned forest network

Original publication DOI **10.1111/1365-2664.70084**, author original Dryad DOI **10.5061/dryad.k3j9kd5m4**. **23 field sites / three Swedish regions**, burned 2015–2018; **2022** beetles recorded using four to five flight intercept traps per site for ~6 weeks (188 saproxylic species / 3,094 beetle individuals in article). Local coarse deadwood was surveyed **2020**, so there is a known **2-year wood–beetle measurement gap**; do not call it concurrent or directly observed feeding. Original source inventory publicly lists:
- `Beetlespecies_data.xlsx`: `Beetledata` trap/site species counts and `speciescode` source scientific names/groups.
- `deadwood_local.xlsx`: original site/transect, tree *Species* (pine, spruce, birch, oak, alder, aspen, unknown), standing/fallen and diameter/height data; site-level host composition is directly measured rather than inferred from beetle affiliations.
- `site_coordinate.xlsx`: author physical site and source region/coordinates.
- `2km_landscapebuffer.xlsx` and `5km_landscapebuffer.xlsx`: original source landscape context, including measured living-tree volume of spruce/pine/deciduous.
- `README.md`: field-grain and methods.

**Prior art warning:** original article already analyzes local deadwood, canopy cover, surrounding old forest and regional beetle community dissimilarity, and cites local fallen-deadwood compositional association. Another model of raw species turnover versus deadwood alone is **not a novel independent finding**. A later explicit new question would need link source wood identity to beetle host-affiliation guild distributions controlling site-region/burn history/effort and recognize original host beetle identity is separate 2022 source (possibly incomplete exact taxon overlap). This source is one study/network, not 23 independent studies.

### Backup availability only — independently published 2026 Poland forest inventory / beetles

Melosik et al. 2026 *Agricultural and Forest Entomology* DOI **10.1111/afe.70091** explicitly links original beetle data Zenodo **10.5281/zenodo.21486790** and original forest stand characteristics Zenodo **10.5281/zenodo.21535672**. This has only one temperate lowland forest / 21 dominant Staphylinidae species modelled (2,947 individuals in article), not a 2nd regional replication or necessarily host-tree preference. It is *an alternative accessible source* only if original records and field-plot identity are qualified; not a substitute for the species-specific hostwood network goal. Do not pool with Sweden or Finland before environmental/taxon/method compatibility is demonstrated.

### Source-only execution, before any new biodiversity effect

1. Query **official Dryad dataset REST metadata** for `doi:10.5061/dryad.k3j9kd5m4` via public `/api/v2/datasets/{encoded DOI}`, follow its published `stash:version` file-list metadata once; capture only source status, filenames, file sizes, format, digest and license. Require four priority metadata documents `README.md, Beetlespecies_data.xlsx, deadwood_local.xlsx, site_coordinate.xlsx` at the same original published version. Do not download/use sample or taxon values in this stage.
2. Query official **Zenodo records API** (21486790 and 21535672), report published metadata/rights and original filenames/formats/digests. Treat access errors as **SOURCE_ACCESS_STOP**, not null ecological results. Never alter these original DOI/version selectors in response to missing or negative results.
3. If Dryad metadata is accessible, test no more than one original officially advertised **README.md** download for method feasibility using its approved file ID/URL, and return only HTTP status/size/digest, not README raw personal/site IDs. No circumvention after HTTP 401/403. No `.xlsx` open, no biological/wood measurements, no original taxa, no guild matching, no model fitting.
4. Decision gate: Sweden primary is eligible for subsequent source-method auditing only if original source DOI, filenames, usable file GET and author source hierarchy can be verified; otherwise hold at a named SOURCE_STOP, not ecological non-support. Zenodo Poland is a separately labelled fallback if accessible, with its own still-unverified original site count/forest-region scope.
5. Preserve prior results, all author sealed scores and CI expected run artifacts. PR #469 remains **Draft/unmerged**; eBird/TinyFish not used.

### A genuinely discriminating next biological design, AFTER source qualification

For Swedish field sites, a source-grain matched *relative representation* hypothesis is more informative than species turnover alone: are beetle host-affiliation guild incidences closer to original measured local **broadleaf/conifer deadwood fractions** than under a community-composition baseline adjusted for source region/burn year/effort? Do not confuse capture activity with emergence or actual host use. With only 23 sites and 3 regions, estimate effect sizes/conditional sensitivity; held-out-region reproducibility is weak and no strong p-value from hundreds of beetle trap or wood-piece rows is allowed. Tree/wood measurements 2020 and beetles 2022 need temporal measurement caveat. Never cherry-pick species labels, individual guilds or tree diameter thresholds to match prior Finnish sign.
