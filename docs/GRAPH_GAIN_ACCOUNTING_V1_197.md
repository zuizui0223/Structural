# Geography-derived graph gain accounting — v1.197

## Why a 20/20 win needs an effect-size decomposition

The prospective v1.119 test is valid **within its frozen null family**: among 529 ultrarare mammals with 1–4 mapped pilot-source positives, the original coordinate-built kNN graph performed better on heldout mapped-positive log loss than all 20 degree-/edge-length-bin-rewired models. However, a 20/20 directional comparison does not say how much of the advantage over R3 is *specific to the original kNN edges*.

Use only already frozen point estimates (no response, binary, graph, model or null data are reopened):

| Contrast, identical presence-bearing heldout-block metric | Log loss difference |
|---|---:|
| Original kNN C minus R3 | -0.596259 |
| Mean rewired C minus R3 | -0.537733 |
| Original kNN C minus mean rewired C | -0.058525 |

The exact additive accounting is:

```
(original C − R3) = (mean rewired C − R3) + (original C − mean rewired C)
```

The original C advantage over R3 on this metric has point-estimate magnitude 0.596259. Its rewired-mean counterpart retains **90.18%** of that magnitude; the original-kNN-specific increment is **9.82%** of it.

These are ratios of **point-estimate predictive log-loss contrasts**, not percentages of ecological processes, causal contributions, variance explained or independent information. A confidence interval on this ratio is **not** recoverable from the two marginal bootstrap intervals. The prospectively frozen original-versus-rewired estimate remains -0.058525 (95% block-bootstrap interval [-0.099309, -0.016291]); it was favourable against 20/20 specified nulls.

## Ecological interpretation and competing accounts

The strongest supported statement becomes **network representation gains are mostly retained after matched rewiring**, with a smaller but detected advantage for the original coordinate-based kNN graph in the ultrarare *mapped-label* endpoint.

This should not be sold as an observed dispersal network. Its kNN edges depend only on island centroids, and its matched rewires preserve degree and coarse edge-length bins but *not* local kNN neighbourhoods, directions or path detours. In addition, both predictor pilot positives and heldout targets originate from one manually curated IUCN polygon-overlap matrix, with some historically restored labels. Therefore even the residual original-kNN edge advantage could represent geographic smoothness or common map-construction structure.

Existing response-free v1.181 evidence likewise supports greater **structural co-coverage** and lower source-influence turnover, not spatially partitioned source-territory irreplaceability. The Azores BALA time-ordered test did not support the later source-loss consequence. The current analysis does **not** establish dispersal routes, colonization, rescue, source-population equivalence or management rankings.

A genuinely ecological discriminating result would require *new* independently measured mammal island-species observations, dispersal/movement with an independently specified destination opportunity set, or time-ordered occupancy transitions with detection denominators. Under such evidence, one could distinguish (i) spatial coherence of mapped range geometry from (ii) ecological connectivity beyond geographic distance and opportunity; current data do not adjudicate that fork.

## Evidence ledger

- Original primary and secondary v1.119 numeric freeze and pre-response scoring protocol: unchanged.
- v1.181 source-territory falsification and v1.185 kNN-versus-observed-movement semantics: unchanged.
- v1.196 independent-data admission: ALA v1.194 consumed but unscored due to prediction-header error; Hébert checklist stopped before headers were opened; neither is independent biological confirmation.
- No outcome reopened, model refitted, threshold moved, null set changed or historical record rewritten. eBird remains disabled.
- GEB v1.185 is still on **scientific HOLD**; v1.197 is a correction to the evidence summary, not an invitation to submit a mechanism claim.
