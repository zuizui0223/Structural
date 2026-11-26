# BioTIME 775 actual result and cross-region aggregate decomposition (2026-11-25 JST)

## Consumed Jari outcome, conditional code-group interpretation
Frozen protocol bb9cef9883cf29cfb241089d40313f3c8c1c0936; completed run 45585210678, job 139104941127, artifact 15007369925, reported ZIP SHA256 8af648729c655084085c0293945444dd2de728c503318ecb448c0c249317d2c9. Logs and artifact metadata checked, not independent ZIP replay. Source live CSV SHA256 0223c9897f86c7c9d93a000fb6a38f1b932063ec642c5585c126a3a27cdc2ca6, 2745 records, 64 taxon labels, 35 site keys, 175 observed nonempty site-years, zero explicit zero rows. F=12, C=8, E=15. Author habitat code mapping remains NOT VERIFIED. No ecological treatment claim from the provisional mnemonic. One tropical landscape, not 35 independent treatment replicates. Original scoring workflow retired at 66257ad809d56f605a879adf9728a60388c5caa8.

| E minus F (four consecutive periods, equal period weight) | Full group | Matched 8-site exhaustive subset mean |
|---|---:|---:|
| Spatial identity alignment A | .06851430680724849 | .06744192269850663 |
| Mean squared same-site temporal distance T | .20459824021187287 | .2045982402118734 |
| Squared centroid displacement M | -.02275280900082237 | .002647488952054935 |

The prespecified joint signature (+,+,-) matched in the full code groups but **FAILED** the prespecified balanced-site sensitivity. Do not count as complete independent replication. A difference positive 3/4 periods, T positive 4/4, M negative 3/4 full groups and 2/4 balanced. All subsets evaluated with no undefined alignments; 495 F, 1 C, 6435 E subsets per pair. T equal by construction in the exhaustive balanced subset mean; not an independent robustness test. A is nonlinear and its balanced sensitivity is informative. All sign counts are descriptive and dependent, no population p or CI. Sampling season shifted in 2013, effort and detection caveats preserved.

## New aggregate-only mathematical analysis
Use frozen BioTIME458 and BioTIME775 receipts only, no original response rows reopened. Let delta_i be next-minus-prior Hellinger incidence vector of a repeated site. T=mean squared length(delta_i), M=squared length(mean delta_i), U=mean distinct-site dot product(delta_i,delta_j). Exact identity U=(nM-T)/(n-1). U incorporates both directional agreement and magnitude, not a normalized synchrony index; lower U does not imply negative correlation or biological compensation. M(k)=U+(T-U)/k exactly equals expected squared centroid displacement when uniformly choosing k of the n observed sites without replacement and retaining same sites in both years. No independence assumption needed for finite-set identity. U need not be an unbiased estimate for an unsampled landscape with spatially dependent sites.

| Region | Delta A (full) | Delta T | Delta U |
|---|---:|---:|---:|
| Bavaria, logged minus retained | .033199686069555284 | .09906349784832535 | -.0404885548570441 |
| Jari, literal E minus F | .06851430680724849 | .20459824021187287 | -.026202618370775477 |

U differences by target pair: Bavaria -.059780832569449646, -.026877005184898942, -.03480782681678371; Jari -.022861390182716372, -.06546832683661366, -.00682035562911406, -.009660400834657804. T differences positive all seven repeated periods; A positive six of seven. These are not seven independent tests. U is POST HOC algebraic decomposition of consumed outcomes, not a newly prespecified independent outcome. Directional pattern at both datasets motivates prospective test, conditional on authenticated Jari habitats and distinct sampling networks.

Expected equal-site-count contrast delta M(k)=delta U+(delta T-delta U)/k; signs switch between 3 and 4 selected sites in Bavaria (continuous algebraic crossing 3.4467037215) and 8 and 9 in Jari (8.8083127921). At 8 sites: Bavaria -.023044548268872915, Jari +.0026474889520555663. Reproduced all eight Jari E/F year-specific balanced centroid means within 1e-12 from full-group aggregates; original balanced C was the same 8-site group. No biological resampling or new effect test. These are descriptive finite-site aggregation results, NOT spatial distances, habitat area, contiguous spatial grain, causal threshold, or evidence of population resilience. Both groups' average vectors can move in different directions or lengths. A positive A contrast can coexist with a lower U contrast; they measure different objects.

Reproducible aggregate-only script analysis/forest_macro_global/biotime458_775_aggregate_change_coherence.mjs, commit db260428f6932105c73ca097077a80a53e0cfd28. Constructed four-vector exhaustive subset fixture and actual aggregate identity validation executed in JS before commit. No source raw records exported.

## Next primary research direction
Scale-of-aggregation reversal is a mathematically identifiable candidate rather than an unsupported universal forest stabilization claim. Need original Jari site/habitat codebook from author or public supplementary methods, and an independent repeated-site contrast with documented habitat and sampling opportunities. Freeze (+delta T, -delta U) as new hypothesis only for *unseen independent data*; A secondary distinct diagnostic, fixed same taxon support and matched physical sites; do not choose subset size after results. Spatial scale requires actual spatial extent and geometry independently standardized; n alone is not a spatial scale. Do not reopen 458/775 for threshold or habitat matching optimization, do not pool incompatible land-use treatments, do not claim global generality. Mexico 776 eligibility HOLD, previous source and outcome decisions unchanged; PR #469 draft, no eBird/TinyFish.
