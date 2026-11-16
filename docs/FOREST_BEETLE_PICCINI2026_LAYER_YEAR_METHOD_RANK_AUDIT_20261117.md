# Piccini2026 forest beetle design: cross-layer causal contrast is rank-deficient; within-layer stand contrast remains algebraically estimable (2026-11-17)

## Actual source vs author published design

From the original published paper [Piccini et al. (2026) DOI 10.1111/1365-2664.70472](https://doi.org/10.1111/1365-2664.70472), floor = 2019/pitfall, subcanopy = 2019/FIT and canopy = 2021/FIT. The [source-only original hierarchy #43882224507](https://github.com/zuizui0223/Structural/actions/runs/43882224507) verified 8 original sites × five stand categories/parent site, 40 nested plot identities and three source layers, while original 'period' tokens cannot be treated as calendar years.

**Independent source-free exact linear algebra audit** (ordinary Gaussian elimination; no original species, guild, abundance, donor or predictions):
\[
X_{\text{layer+method+year}}=
\begin{array}{c|ccccc}
&1&\mathrm{Sub}&\mathrm{Can}&\mathrm{FIT}&\mathrm{Year2021}\\
\mathrm{floor}&1&0&0&0&0\\
\mathrm{subcanopy}&1&1&0&1&0\\
\mathrm{canopy}&1&0&1&1&1
\end{array}
\]
There are exactly **five columns but matrix rank three (nullity two)**, because FIT = Sub + Can and Year2021 = Can. Replicating the same rows across all 8×5 site×stand contexts does not alter these exact identities. Therefore a model containing arbitrary layer differences, method differences and year effects **cannot identify their independent coefficients** from this original source. This is a design-based nonidentifiability, not an ecological null for true vertical stratification.

For one layer at a time, the nominal balanced site×stand fixed-effect design has **40 plot labels, 12 design columns** (intercept + 7 parent-site indicators + 4 stand indicators), full rank **12**, giving 28 purely algebraic residual degrees of freedom if every row is treated once. This only establishes that the within-layer *observational* stand contrast is algebraically identifiable, NOT that 28 independent forest regions are available: only **8 actual parent-site geographical blocks** exist. Four changed original plots and source trap-effort/zero-capture uncertainty remain.

## Scientific interpretation and next exact gate

Any cross-layer numerical difference is inseparable from different trap method and/or year without new overlapping sampling. Conversely, a within-layer stand-type association can be estimated in principle if author trap deployment/effort, taxonomy and guild definitions are verified. This interpretation is also consistent with the source author's published conclusions and should not be called novel Structural ecological causality. Cross-region predictive transfer of the stand contrast is still **NOT VERIFIED**.

The independent original method-only [#43901051028](https://github.com/zuizui0223/Structural/actions/runs/43901051028) verified three distinct trap-like source headers but no explicit effort/zero-trap exposure denominator. An additional author-original exact 'trapID' layout benchmark has a separate frozen source-only protocol; a fit or response opening is not authorized by this linear algebra calculation. Old original Finnish/Thai/PREDICTS/NEON/BALA/GEB outcomes untouched, no eBird/TinyFish.
