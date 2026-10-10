# v1.213: Do not attribute the 4- vs 6-patch reversal to patch count alone

The Wolfe et al. 2022 public README shows the 48-ml microcosm landscape treatments explicitly: `4Ho=12+12+12+12`, `4He=16+16+8+8`, `6Ho=8+8+8+8+8+8`, `6He=12+12+12+4+4+4`. All total to 48 ml. Thus 4He uses a **2:1** large:small ratio and population patch-size CV **1/3**, while 6He uses **3:1** ratio and CV **1/2**. Their Gini coefficients are **1/6** versus **1/4**. The six-patch heterogeneous treatment is *also more unequal* and has a smaller absolute minimum-patch volume. This is a design feature, not an implementation bug.

The v1.212 source-label-independent exclusion result shows a qualitative reversal in day-21 joint predator guild retention: four-patch heterogeneity minus homogeneity **[-5.56,-2.78] percentage points** and six-patch heterogeneity minus homogeneity **[+13.89,+25.00] percentage points**, with bounds only for five ambiguous/missing binary outcomes. The *within-patch-count treatment bundles* are observed; the pure interaction of patch number with equal-intensity habitat heterogeneity is **NOT identified**, because dose of relative heterogeneity and absolute patch-size ranges differ.

Wolfe et al. already proposed patch-size thresholds: larger patches may support generalists while smaller patches may provide refuges reducing top-predator pressure on specialists. Current terminal-day microcosm-level CSV cannot validate the refuge or threshold mechanism, nor distinguish interactions within individual patches or temporal source-to-target colonization.

A discriminating follow-up experiment would orthogonally manipulate patch count (4 vs 6), *the same* relative size inequality (e.g. CV=0.5: [18,18,6,6] vs [12,12,12,4,4,4], fixed total=48), and a sufficient set of absolute patch-size thresholds. It would observe guild-specific patch occupancy and viable donor output through time and actual dispersal rates. This requires **new experiments**; existing data have no off-design counterfactual treatment combinations. The current result is a useful hypothesis generator, not a newly identified landscape mechanism.

Authored as a response-free treatment-design semantic audit and does not modify the numerical v1.212 result, old terminal stops, or GEB's scientific HOLD.

