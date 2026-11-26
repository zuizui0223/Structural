# BioTIME 458 — actual salvage spatial identity result and aggregate decomposition (2026-11-25 JST)

## Consumed original endpoint
Frozen protocol commit ed343180dd691c0ae84408d6bd8434b86efdae0a. Completed run 45541446158, job 138960688016, artifact 14989766924, reported ZIP SHA256 96c9af5b62c3bec20ce0b2849ff970671f28649863c2dd2ca7d93ace46ed177e. Logs and artifact metadata verified (not independent ZIP download). Pinned live CSV SHA256 a39c4a3af2ede728c15ada47fa81f235dff619b6108526d06acb819265dbb005. 4304 source records, 179 valid_name labels, 44 site keys, 176 nonempty observed site-year communities; 0 explicit zero-count rows. Actual source validation and synthetic tests passed.

| Consecutive years | A logged | A unlogged | Logged minus unlogged |
|---|---:|---:|---:|
| 2008–09 | .12692350610069605 | .08919363062223172 | .037729875478464334 |
| 2009–10 | .15640518067323889 | .10462863459037351 | .051776546082865374 |
| 2010–11 | .1364937329416903 | .12640109629435414 | .010092636647336145 |
| Equal-year mean | .1399408065718751 | .1067411205023198 | .033199686069555284 |

Observed sign **opposes preregistered negative directional hypothesis** in this source. Three repeated periods are not independent. No p/CI, no causal claim. Do not rename this as confirmation of initial hypothesis or global replication. Both groups have weak positive absolute alignment (about .1), not near-complete retention. Logged and retained patches have different spatial arrangement and intervention replication (four larger retained patches). Observed detected assemblages only; zero samples and differential detection unresolved. Original run retired in commit 52a78b9ade4d5cc92f00b8a92ab49b70416f6093; current workflow synthetic only.

## Additional aggregate-only algebraic decomposition (post hoc descriptive, not independent endpoint)
Let T=mean squared Hellinger-incidence vector distance of same sites, S0 and S1 annual within-treatment spatial variances, C centered between-year covariance. Then T = M + S0 + S1 - 2C, with M=||annual group mean vector difference||². M is not the distance between pooled species assemblages. Calculated from the immutable original aggregate receipt, no new biological rows read. All distances use the original unhalved squared Euclidean distance of Hellinger vectors, not pure taxonomic replacement.

| Mean over three year pairs | Logged | Unlogged | Difference |
|---|---:|---:|---:|
| T | 1.0543399683695385 | .955276470521213 | .09906349784832535 |
| S0+S1 | 1.12848003108349 | .9373490339875726 | .19113099709591697 |
| C | .07902768480792498 | .05006657505116555 | .028961109756759428 |
| S0+S1-2C | .9704246614676397 | .8372158838852416 | .1332087775823981 |
| M | .08391530690189863 | .11806058663597141 | -.03414527973407276 |

Each of the three pairs has positive logged-minus-unlogged T, S0+S1, C and A; negative M. Larger spatial variance explains the positive raw temporal distance contrast algebraically despite higher covariance and lower centroid displacement. Not a causal variance partition. The forest-level centroid shifts less, not necessarily total forest species pool or ecosystem stability. Distinct dimensions of stability can rank treatments differently. Post hoc descriptive insight, hypothesis for independent data rather than evidence selected to confirm a new hypothesis. No recoding, rerunning or alternate metric search on 458.

## Next source comparison
Jari 775 original author article Beiroz et al. 2018 DOI 10.1016/j.ecolind.2018.07.062 and BioTIME study page confirm 12 primary forest, 8 corridor, 15 plantation sites. Existing source-only 35 plot codes and 175 annual records verified; no authenticated habitat mapping yet. Do not infer from record order, coordinates or group size. Original paper already reports variable temporal diversity; new question concerns the simultaneous contrast among A, T and M. Mexico 776 (Salomão et al. 2020 DOI 10.1016/j.ecolind.2019.105968, https://biotime.st-andrews.ac.uk/selectStudy.php?study=776) documents 11 forest fragments and 8 pastures, identical trap methods within paired census periods 1999–2000 and 2016–2017; matched March/May/June/August/October survey months, no 16-year gap bridge. Author metadata descriptor Site_HabitatType_Day_Month_Year. New candidate for a separate forest/pasture contrast with exact temporal opportunity audit; no equivalence to salvage removal. No independent causal or multi-biome conclusion yet.

PR #469 draft only; previous PREDICTS, NEON, Chiu, Swiss, Zarges and Lettenmaier holds unchanged; no eBird/TinyFish.
