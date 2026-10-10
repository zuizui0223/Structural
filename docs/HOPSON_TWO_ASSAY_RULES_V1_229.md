# Hopson v1.229 — Compare TWO precommitted prey-assay interpretations; retain v1.227 STOP

The source-pinned v1.227 predictor run **failed** because its initially frozen assay-domain parser required `dil.vol` and `sub.samp.vol` both zero or both positive. A distinct read-only v1.228 metadata audit of the published 4,830-row file found **3,591** unambiguously undiluted rows, **1,238** rows with both assay flags positive, and **one** row with zero dilution but positive subsample volume. The original v1.227 protocol therefore remains terminal STOP with zero numerical scores. This v1.229 is **separate post-outcome sensitivity**, not a rescue or confirmation.

The original R calculation says apply `(tet/sub.samp.vol)*(dil.vol+samp.vol)/samp.vol` for finite positive subsample and fallback to `tet/samp.vol` when calculation is nonfinite. Its README separately describes `dil.vol=0` as undiluted. These conventions diverge for the single metadata-inconsistent row. BEFORE scoring anything in this distinct version, lock both:
1. `author_R_literal`: use the R numerical formula whenever `sub.samp.vol>0` regardless of dilution flag.
2. `README_no_dilution`: for `dil.vol=0`, use `tet/samp.vol`; otherwise original R diluted formula.

Report **both** scores on the same 1,085 zero-count start transitions, 554 next-visit positive samples, and 14 whole-metapopulation LOSO folds, reusing v1.227's already-frozen lagged prey and ring source features, StandardScaler and L2 logistic. The original no-prey v1.226 score must exactly reproduce the previously frozen -0.000571276180789163. Do not select a preferred source convention based on favorable results, change training folds, lower a threshold, or turn this into a GEB R3 test. Both scores concern **observed predator sample re-detection**, not verified recolonization; there is no measured donor-to-target animal migration.

If either score fails for an additional unexpected assay reason, stop without opportunistic redesign and report the blockage. Already published Hopson predator/prey synchrony findings are acknowledged; even a negative heldout loss increment would not establish a new causal rescue mechanism.
