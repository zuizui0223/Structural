# Poland 2026 rove beetle × forest stand source original worksheet-grain audit (2026-11-15)

## Actual source result — ORIGINAL file access passed; field-site matching not yet demonstrated

Previous original publisher files [Actions #43695297997](https://github.com/zuizui0223/Structural/actions/runs/43695297997) **SUCCESS**: exact author original `abundance_data_dominant.xlsx` (17,503 bytes, MD5 `ecc1836c111bf08cc1eba3f23aaaf6e4`), `Forest_stand_characteristics.xlsx` (15,002 bytes, MD5 `283db0672933621c7e4d0e0b8ac03160`) and source `README.txt` (1,656 bytes, MD5 `2d34fa07c7137e15fc99bd826843d495`) downloaded with publisher checksum match. Two independent original Zenodo records [21486790](https://doi.org/10.5281/zenodo.21486790) (beetles), [21535672](https://doi.org/10.5281/zenodo.21535672) (stand variables), all publicly listed CC BY 4.0.

Now new [original worksheet source-only Actions #43695811282](https://github.com/zuizui0223/Structural/actions/runs/43695811282) **SUCCESS**, ZIP aggregate artifact **14154371307**, SHA256 `5195405d64a3b16f162443f761cc0e6fa7ffcba1f3773f8411157d41321bb44e`. The source scanner inspected original Excel OpenXML worksheet dimensions, header *shapes* and only safe generic field-name matches in the first 3 rows, not any beetle species/individual measurements or original forest stand values.

| Author original file/sheet | Original worksheet rows INCLUDING potential headers | Maximum occupied cells/row | Source-identity qualification |
| --- | ---: | ---: | --- |
| Beetle `21_species_abundance` | **48** | **21** | No generic site/plot field name found in first 3 header-like rows |
| Beetle `276 species` | **277** | **1** | Single-column species list: NOT an independent 276-site or 276-plot community matrix |
| Forest `Stand characteristics` | **48** | **13** | No generic site/plot field name found in first 3 header-like rows |
| README | **72 source lines** | N/A | Published original source available, its raw method text not exported |

**Scientific decision:** the two original main data sheets each having 48 rows does NOT demonstrate that row `i` of beetle captures belongs to row `i` of forest environments. A 48-row table may include headers and nested source study units; original author-defined physical stands/sites, times and sampling effort are not verified by this limited schema scanner. **NO Excel row-index join, sample-size claim of 47 independent forest stands, 21 independent community studies, biodiversity/hostwood correlation, regression or p-value is authorized.**

This is an **unresolved SOURCE-GRAIN** gate, not evidence that forest stand environment is irrelevant for rove beetles. A separate original README/author key codebook audit, using only exact source physical site/plot identifiers and study method fields, would be needed before an ecological effect. The author 2026 paper already modelled 21 dominant rove beetle abundance responses to forest stand heterogeneity, so simply repeating those published regressions cannot be claimed as novel independent support. Original primary article DOI [10.1111/afe.70091](https://doi.org/10.1111/afe.70091).

## Next independent forest network prioritized

The better direct original host-substrate design is the 12-year original source of Lettenmaier et al. (2025/2026), [Journal of Animal Ecology DOI 10.1111/1365-2656.70183](https://doi.org/10.1111/1365-2656.70183), publisher-linked [Zenodo DOI 10.5281/zenodo.17337484](https://doi.org/10.5281/zenodo.17337484). That author paper reports emergence-trap beetles from beech, fir and spruce original logs, plus a longitudinal age/decay window. **It has its own already-published host-wood and temporal ecology results**; analysis novelty and original log-level sampling units require re-evaluation. A frozen metadata-only source-rights and file-availability gate is staged: [source prespec](FOREST_BEETLE_12YEAR_HOSTTREE_LONGTERM_SOURCE_PRESPEC_20261115.md), workflow `.github/workflows/forest-macro-saproxylic-12year-zenodo-sourceonly.yml`.

All previously frozen Finnish 142-site site-author Host_tree null / VD10 geographic heldout positive, 3-country Burner conditional null, PREDICTS, NEON, BALA and GEB holdouts unchanged. The original Poland and Sweden scans did not read organisms. Draft PR #469 not merged, no eBird/TinyFish.
