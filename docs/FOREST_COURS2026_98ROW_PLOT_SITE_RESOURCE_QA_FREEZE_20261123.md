# Cours et al. 2026: 98-row original plot/site and source-resource QA (response sealed)

## Previous immutable observations

Official Zenodo 10.5281/zenodo.17927769, CC BY 4.0, Decline_Data.RData exactly 33,531 B / MD5 34312f823dafa60568fa0cd92926ee37. Original Rmd 80,911 B, MD5 083c1aef2e0acb519675f52dcbbf92f7. RData original object/class/column-name-only inspection GitHub Actions #45078541600 **PASS** with 3 author data frames **Pyr 56×82, Bav 27×82, CVL 15×82**. These 98 observations are source model records, not 98 independent forests. Source-author functional guild responses include `Abund_Xyl`, `Abund_Sxy`, `Abund_Myc`, etc; no physical plot×species abundance matrix shown in this RData.

The author's original paper already models decline/mortality, deadwood/TreM habitat and beetle guild responses through piecewise SEM. A mere new significant association of the same kind is prior-art, not novel.

## New independent response-blind source field gate

1. Open publisher SHA-pinned RData **only for nonresponse variables**, without reading or calculating any `Abund*`, beetle richness, guild, diversity response, original model estimate, p-value or raw plot IDs/coordinates.
2. Require all original three object names and exact source dataframe sizes + shared columns, no silent row-order joins. Source-native separate context labels `Pyr`, `Bav`, `CVL` are original class design, not three independent forest programmes.
3. Inspect only source fields `plot`, `site`, `Region`, `salvaged`, `class_decline_ARCHI`, `prop_decline`, `TreMs_div`, `FDis_TreMs`, `FDis_DW_diam`, `FDis_DW_decay`, `CWM_DW_diam`, `CWM_DW_decay`, `CWM_DW_type_substrate`, `Abund_TreMs_Fon`, `Abund_TreMs_Injur`, `Abund_TreMs_Rot_Hole`, `Abund_TreMs_Saprox`. Terms derived directly from source schema, no response result-driven feature choice.
4. Publish only per-original-context n source `site` keys, n source `Region` keys, n unique `plot`, number of plot-key duplicates, anonymous min/max number plots per site, *missingness counts only* of the fixed nonresponse variables, type/class counts for `salvaged`, and no raw site/plot/year IDs or actual substrate/Beetle values.
5. If site hierarchy missing or any original response fields are incompatible across datasets (not tested here), hold: a site-level cross-validation is NOT authorized by a passing field QA alone.
6. After identity and missingness are inspected, author a distinct **one** leave-one-source-site-out test comparing total deadwood/decline/effort context to resource diversity for a compatible guild endpoint only if justified by source methods and independent held sites. Test must not reopen completed historical heldout results or cherry-pick among guilds and contexts.

No new ecological coefficients. No eBird/TinyFish, Ramberg scientific STOP and Korhonen HTTP401 HOLD unchanged, PR #469 Draft.
