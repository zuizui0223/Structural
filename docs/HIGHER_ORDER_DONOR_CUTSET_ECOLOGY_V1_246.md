# Structural v1.246 — A higher-order source-failure cutset with the SAME pairwise synchrony

## Mechanistic question, not an obvious source count effect

Could two archipelagos have the *same four marginal donor-viability probabilities*, *same six pairwise donor co-viability probabilities*, *same complete distribution of global number of viable donor islands*, and the *same source–recipient accessibility graph*, yet reverse **which** receiving island has no usable donor? An exact rational counterexample shows yes.

Let source availability be x=(x1,x2,x3,x4), xi=1 for a potentially viable source, 0 for an unavailable source. Recipient A can access sources 1,2,3 and recipient B can access sources 1,2,4. Both receive potential support from three donors. Define two fully specified four-source availability distributions:

`p_s(x) = 1/16 + s/32 [(-1)^(x1+x2+x3) − (-1)^(x1+x2+x4)]`, for s∈{−1,+1}.

Every one of the sixteen state probabilities is exactly 0, 1/16, or 1/8. Under both worlds, each source is viable with probability 1/2; every donor pair is jointly viable with probability 1/4, hence every pair covariance is zero. The entire global live-source count distribution for k=0 to 4 is exactly (1,4,6,4,1)/16, *not just the same mean*. The probability all **four** sources are unavailable is 1/16 in both worlds.

Nevertheless, in world s=−1, A loses all three accessible donors with probability **1/16** and B with **3/16**. In world s=+1, the exact probabilities **reverse**. The recipient's all-accessible-sources-unavailable risk therefore differs **threefold**, and by 1/8 in absolute probability, despite all first- and second-order source reliability and aggregate count information matching. The **sum of A and B risks is 1/4 in both worlds**: vulnerability is redistributed, not created at the aggregate level.

This is a *four-way ecological cutset problem*: pairwise independence is insufficient to identify which three donors might fail together, and the geography of which donors can reach which recipient matters. The result is not reducible to the truism “fewer sources means less support”; even the *full distribution* of the number of available sources does not identify recipient-level potential source loss.

## Literature boundary and why the ecological sign is not universal

These published experiments are **different systems, manipulations and outcomes**:

- **Fox et al. 2017** (DOI 10.1038/s41559-017-0271-y) already discovered the *spatial hydra effect*: deliberately inducing catastrophic local extinction in highly dispersed, cyclic protist metapopulations can disrupt synchrony and prolong metapopulation persistence.
- **Matter & Roland 2009** (DOI 10.1098/rspb.2009.1520) removed adults from two of seventeen neighboring Rocky Mountain Apollo meadow populations for multiple years; immigration into surrounding meadows declined while nearby local synchrony increased. This is an intervention on adult removal, not proved completed local extinction.
- **Matter & Roland 2010** (DOI 10.1111/j.1600-0706.2010.18666.x) reported strong within-generation abundance effects but limited effects on longer-term persistence of neighboring butterfly meadows.
- **Park et al. 2024** (DOI 10.1098/rsos.240557) returned to that **same butterfly intervention**. Even after eight generations of removing observed adults, the manipulated P/Q populations had **not gone extinct**; 471 specimens and 152 filtered SNPs indicated immigration from several neighboring populations contributed to their persistence. Park and Matter are **one experimental lineage**, not two independent confirmations.

The present exact counterexample does not replicate those biological phenomena or prove higher-order cofailure occurs. It constructs a *future-measurable mechanistic distinction* between potential donor availability and real immigrant demographic rescue. Do not call its probabilities measured extinction risks or its donor viability bits realized individual dispersal.

## Field test and Structural controls

A future independent island/fragment network must record **time-resolved viability of all accessible natal source populations**; actual directional movement and its effort/detection; the recipient's next-interval occupancy/recruitment; environmental shared shocks, island size, habitat, source distance and identity; and all local accessible source cutsets before recipient response. A strong reference must at least control all donor marginals and pairwise cofailure, the *full* global live-source count distribution, and individual receiver accessibility/effort. A new higher-order feature would add only the chance that **all locally accessible donors** fail together.

This is a new *known-truth identifiability witness*, **not new empirical support**. The frozen earlier Structural prospective source-loss leverage hypothesis v1.123 existed independently and is not rebranded as discovered here. Any future biological claim requires the untouched v0.31/v0.42 source-quality and disjoint response gates. Original global mammal heldout remains unopened, eBird unused, GEB scientific HOLD unchanged.
