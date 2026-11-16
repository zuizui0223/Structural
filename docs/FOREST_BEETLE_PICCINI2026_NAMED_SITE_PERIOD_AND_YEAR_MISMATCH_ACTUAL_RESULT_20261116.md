# Piccini 2026 three-layer forest beetles: original field hierarchy CONFIRMED, period≠calendar year (2026-11-16)

## Audited outcome and primary scientific decision

**The original 2026 field-method source validates nested 8 field sites × 5 forest-stand categories = 40 plot labels; the three vertical strata have data in all 40 plots.** This is a new, original-source *design/field-denominator* verification, NOT a biological effect. **Same named `period` cannot be interpreted as same calendar year or matched observation campaign.** The original 2026 publication explicitly states floor and subcanopy sampled in 2019, canopy in 2021, using method-specific traps. Therefore **a same-site, same-year, same-method three-way layer contrast is scientifically NON-ESTIMABLE from these collections**. Do not claim the 79 repeated `plot×period` triples reflect synchronous sampling or 40 independent forests.

## Actually executed GitHub Actions and exact source-only numbers

- [One official dataset/DOI identity and published-version intake #43875641370](https://github.com/zuizui0223/Structural/actions/runs/43875641370) **SUCCESS**: publisher DataCite/GRO metadata verify the original [10.25625/H8EMJS](https://doi.org/10.25625/H8EMJS) two unrestricted published text files, and related [10.25625/5AWJBC](https://doi.org/10.25625/5AWJBC) two unrestricted published text files. They may share the canopy biological observations and are NOT independent replicates. No species rows were opened then.
- [Method-column-only #43877711860](https://github.com/zuizui0223/Structural/actions/runs/43877711860) **SUCCESS**: original 2026 GRO full file publisher MD5 verified, 22,414 original field-method CSV rows / 17 semicolon-separated fields, 3 generic site-like fields with cardinalities 5,8,40; one vertical-layer field with 3 labels, one temporal field with 8 labels, three method/effort fields with 8,320,557 distinct labels. **No species abundance/functional guild fields used.**
- [Strict exact-author-name source gate #43878597612](https://github.com/zuizui0223/Structural/actions/runs/43878597612) **SUCCESS as execution, scientifically stopped** because its permitted calendar header names did not include original `period`. Safe original method names revealed `site`, `stand`, `plot`, `stratum`; none matched literal `year` variants. No taxa opened.
- [Corrected STRICT semantic source-only gate #43882224507](https://github.com/zuizui0223/Structural/actions/runs/43882224507) **SUCCESS**; artifact **14233007527**, workflow ZIP SHA256 `2fc657c5a97188c54adc6e0a1bd4bb6aa9ce2552fba2acccf6c13f28323ce021`. The prior source-only failure was corrected by a separately frozen generic time-column audit [prespec](FOREST_BEETLE_PICCINI2026_TIME_FIELD_STRICT_SOURCE_AUDIT_PRESPEC_20261116.md), with no change to biological outcomes, exclusion, statistics or ecology.

**Exact original-source support (one site is the highest independent geographical unit):**

| Original verified metadata-only quantity | Result |
|---|---:|
| Original method rows scanned | **22,414** |
| Source exact generic roles | **site, stand, plot, stratum, period** |
| Parent sites / stand categories / plot labels / vertical stratum labels | **8 / 5 / 40 / 3** |
| Parent sites with five original stand categories | **8 / 8** |
| Stand categories represented across all eight parent sites | **5 / 5** |
| Plot IDs assigned to >1 parent site or >1 stand category | **0 / 0** |
| Plot labels with all three vertical categories (across ANY period) | **40 / 40** |
| Distinct `period` label categories | **8** |
| Plot labels with shared time *token* across three strata | **40** |
| `plot×period` token cells with three strata | **79 / 313** |
| Original `period` rows parseable as strict YYYY or YYYY-MM-DD | **0 / 22,414** |
| Plots with 3 layers established in the **same calendar year** | **NOT IDENTIFIABLE from period** |
| Different time-token counts per stratum (sorted; anonymous) | **4, 5, 7** |
| Source taxon, abundance, trait, host-tree measurements newly scored | **ZERO** |

The 79/313 are token overlap counts, not true contemporaneous biological observations. Source `period` strings were not exported or guessed into calendar-year labels. The source-only code correctly withheld the calendar-triple count (`null`), rather than inferring 40 contemporaneous plots.

## Independent author methods resolve why cross-layer causal effects are not identified

[Piccini et al. (2026), *Journal of Applied Ecology*, DOI 10.1111/1365-2664.70472](https://doi.org/10.1111/1365-2664.70472), Methods §2.2:
- **Forest floor**: pitfall traps, eight per plot, April–August **2019**.
- **Subcanopy**: flight-interception traps (FIT), three per plot, May–August **2019**, height 2.5 m.
- **Canopy**: FIT, three per plot, approximately April–August **2021**, height mean 17.5 m (SD 3.1).
- The author describes **four plot replacements after 2019** due to storm damage. A repeated 40-plot label count does not automatically prove unchanged physical coordinates/trees from 2019 to 2021.
- The author expressly cautions that strata were sampled in different years and focuses on **within-stratum** relative patterns.

**Design-based confounding matrix** (irrespective of statistical significance):
- floor vs subcanopy: same 2019 but **different method** (pitfall versus FIT);
- subcanopy vs canopy: FIT in both strata but **different year** (2019 versus 2021);
- floor vs canopy: **method and year both differ**.

Even with all original biodiversity rows, a causal height, microclimate or tree-resource effect across layers is not identified by direct differences without additional detection and time-matched observations. This is not a negative result for forest vertical niches. The original paper has already reported stand-type and vertical differences in taxonomic, functional and phylogenetic diversity; these are PRIOR ART, not new Structural findings.

## What remains biologically testable and publication novelty boundary

1. **Within-stratum** source design is balanced 8 source sites × 5 stand categories. Tree-type sorting of a specified beetle functional guild composition can be assessed observationally *within each layer*, acknowledging local microclimate, trap effort, storm disturbance and author prior art.
2. One possible future prospective/predeclared **leave-one-parent-site-out (n=8 blocks)** test is whether original **stand type / host tree identity** adds out-of-site prediction for a **single named functional guild composition endpoint** beyond a fixed null baseline **within one layer**, not across three differently dated/method-sampled layers.
3. Before any biology: validate the published `stratum` and `period` category codebook, original trap durations/methods per row, species/feeding-guild header meaning, source positive-only vs negative sampling opportunity, and author site/stand replacement identity. The German 2026 paper already studied vertical functional guilds, so simple significant tree × guild differences would be a shared-source reanalysis rather than an independently novel discovery.

**Scientific state: source-only physical hierarchy CONFIRMED / same-year all-layer biological effect STOP / no new ecological coefficient or p-value.** Existing Thai/Finland/PREDICTS/NEON/BALA/mammal original biological scorers untouched, GEB SCIENTIFIC HOLD, eBird/TinyFish unused. Draft PR #469 unchanged in submission status.
