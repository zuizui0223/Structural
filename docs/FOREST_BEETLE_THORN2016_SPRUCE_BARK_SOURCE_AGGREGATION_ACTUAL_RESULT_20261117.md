# Thorn2016 bark-treatment experiment: 120 source species×3 treatments + 120×120 species-label matrix VERIFIED; original n=12 plot replication NOT retained (2026-11-17)

## Main actually executed source result

Publisher-original Thorn et al. 2016 source [Zenodo 10.5281/zenodo.13905995](https://doi.org/10.5281/zenodo.13905995), published field paper [*Forest Ecology and Management*, DOI 10.1016/j.foreco.2015.12.044](https://doi.org/10.1016/j.foreco.2015.12.044).

1. [Original two-file source/hash/header CI #44091187080](https://github.com/zuizui0223/Structural/actions/runs/44091187080) **SUCCESS**, artifact **14331018286**, ZIP SHA256 **100f1f62d5fa54fc2b58a4912f658915934c98f35059453a6572a910d67eabe9**. Source publisher original license **CC BY 4.0**. Original file `Babund.csv` MD5 `f7f57ac49bcd364d88b035eb7708ad9a`, **3531 bytes**, 121 lines/4 header columns; original file `Bdist.csv` MD5 `6a99359b7091bcfd7246440dc11e0f5a`, **262627 bytes**, 121 lines/121 header columns. No species or distance numeric values scored.
2. [New narrowly prespecified species-label source-identity gate](FOREST_BEETLE_THORN2016_AGGREGATE_SPECIES_TREATMENT_DISTANCE_IDENTITY_PRESPEC_20261117.md) then actually executed once via [**CI #44091686670 SUCCESS**](https://github.com/zuizui0223/Structural/actions/runs/44091686670), anonymous artifact **14331258662**, ZIP SHA256 **479b5af9b3723b461610760a936ae10a6c65e573f44c76ecf23ed8dadba25b8f**. Both publisher MD5 files reverified. Only original first identifier column from each row and `Bdist` column names were compared **in runner memory**; all species labels remained private, no source numeric abundance or distance values examined, and no ecological p/β or trait score computed.

**Actual verified anonymous matrix design:**

| Original author source field / identity test | Verified result |
|---|---:|
| `Babund.csv` original body rows (excluding header) | **120** |
| `Babund.csv` original columns | **4** = first source species identifier + **3 treatment summaries** |
| Three exact whitelisted original non-key treatment labels | **control / scratched / debarked** |
| `Bdist.csv` body rows excluding header | **120** |
| `Bdist.csv` header columns | **121** = first source identifier + **120 species columns** |
| Unique/nonmissing original row labels in `Babund` | **120 / 120** |
| Unique/nonmissing original row labels in `Bdist` | **120 / 120** |
| `Babund` row labels matching `Bdist` row labels | **120 / 120** |
| `Babund` row labels matching `Bdist` species column labels | **120 / 120** |
| `Bdist` row-label and col-label full original sets/order | **complete exact match and same order** |
| `Babund` and `Bdist` original row order | **exact match** |
| Original physical 12 field plot IDs × three trees × capture year recovered | **ZERO** |
| New original species abundance, interspecific-distance or biodiversity effect evaluated | **ZERO** |

### Crucial ecological distinction — original design versus released grain

The published original 2016 **field experiment** had **12 artificial spruce windthrow plot clusters × 3 trees** (one control, bark-scratched, fully debarked per plot), 36 experimental spruce trees, with stem-emergence traps. Its original paper already showed reduced target `Ips typographus` and strong non-target beetle/fungal collateral decline under full debarking, whereas bark scratching retained more non-target biodiversity. **These are authors' PRIOR findings**, not newly reproduced Structural biology.

The publicly provided original `Babund` is **an aggregate by 120 source species across only three treatment categories**, and the other original `Bdist` is label-compatible 120×120 species matrix (numeric distance type and units unexamined). It has **no 36 tree response columns or 12 plot response rows**. Therefore no researcher can reconstruct a valid n=12 paired block test or leave-one-windthrow-out forest holdout from these two files alone. Species n=120 does **not** constitute 120 independent trees, forest sites, sample years or randomized replicates. The successful row label audit DOES NOT reveal original per-tree zero counts or trap-days. Do not infer them or invent a replicated log×species matrix from aggregate abundance columns.

Because the original individual experimental-unit response is missing, no new independent host-resource×guild predictive ecological effect is admissible from this public source. A species-by-treatment **descriptive** comparison could in principle be computed from the aggregate, but would largely repeat the 2016 published treatment finding and cannot support a causal effect SE/p based on n=12 recovered trees. Structural deliberately did not open original abundance numbers to avoid post hoc narrative chasing.

### Independent cohort gate — updated forest macro scientific claim

- **Experimental design validation succeeded**: field access of substrate bark is genuinely experimentally manipulated in published literature, but the dataset does not preserve independent site×log source replication for new inferential analysis.
- **2025 Sbaraglia original sunshade×tree×fungus**: publisher CC0 3-file SHA256 manifest verifiable, source main `stickies_final.csv` official GET HTTP401; original source row-key and biological data unopened. [Source result](FOREST_BEETLE_SBARAGLIA2025_SUN_SHADE_SOURCE_ACCESS_ACTUAL_RESULT_20261117.md).
- Original German Piccini 2026 floor feedingguild 8-site original independent-site heldout +11.70% descriptive gain / exact p=.09375 **UNSUPPORTED**; original Finland 142-site deadwood Host_tree small ΔHellinger² +.00024237 conditional block p=.015, three-country Burner trait-label shuffle D=.091059 conditional. These are different responses, no justified meta-average; no cross-country biological hostwood×guild transfer confirmed.
- Other eligible-source tests Norway Wetherbee 270 site info has **0 exact hostwood amount header candidates** and unknown Burner lineage; Kriegel 8-country, Sweden Ramberg and Sbaraglia original Dryad official download return HTTP401; Poland original 48-row workbooks not author physically joined; Lettenmaier original 522 long×525 wide mismatched keys. No blind guessing to recover sample rows.

**Scientific status:** `SOURCE_AUTHOR_120SPECIES_TREATMENT_AGGREGATES_VALIDATED_NO_12PLOT_REPLICATION_NO_NEW_EFFECT`. All earlier original BALA/GEB, Finland, Thailand, PREDICTS, NEON, mammals and Piccini heldouts unchanged. GitHub PR #469 remains Draft/unmerged; no eBird, TinyFish, author outreach or external submission. An actual new macroecological validation must use an independent collection preserving parent site, source wood identity, calibrated trap effort and species×guild responses.
