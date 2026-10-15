# v1.246 — The mechanism needed for source loss to HELP rather than HARM

The Structural source-loss hypothesis (`development/prospective_source_loss_leverage_hypothesis_v1_123.json`) expects greater contractions after loss of high-leverage occupied sources. Its independent BALA three-wave test did **not** support the frozen primary effect (`development/source_loss_leverage_cross_system_synthesis_v1_144.json`). We do not reanalyze these outcomes or claim the hypothesis was proved.

Two experimental studies establish that ecological signs need not align:

1. **Fox et al. 2017**, [DOI 10.1038/s41559-017-0271-y](https://doi.org/10.1038/s41559-017-0271-y), [original Dryad 10.5061/dryad.2rs23](https://doi.org/10.5061/dryad.2rs23): repeated catastrophic local population extinctions under strong dispersal in cyclic predator–prey laboratory metapopulations prevented synchrony and increased whole-metapopulation persistence. This *spatial hydra* phenomenon was published by Fox et al., not discovered by Structural.
2. **Matter & Roland 2010**, [DOI 10.1098/rspb.2009.1520](https://doi.org/10.1098/rspb.2009.1520): removing two of 17 local Rocky Mountain Apollo butterfly populations reduced realized immigration to nearby meadows and **increased** spatial synchrony among surviving populations. They did *not* observe an actual post-removal elevation in the overall metapopulation extinction rate, so this experiment supports synchrony amplification, not an observed negative persistence effect.

### One exact intervention decomposition, two ecological routes

Let `X_i=1` mean donor island/population i actually sends **viable, endpoint-relevant recruits** to one recipient during a specified future interval; not mere occupancy, graph distance, or population size. Let C be removed, A and B remain.

- `Q_before=P(X_A=X_B=X_C=0)`, the baseline complete failure of source supply.
- `Q_static=P(X_A=X_B=0)` under the **same baseline** joint state of survivors, ignoring any post-removal feedback.
- `Q_after=P(X'_A=X'_B=0)` after the source loss has changed remaining source dynamics.

The exact identity is

`Q_after - Q_before = [Q_static - Q_before] + [Q_after - Q_static]`.

The first bracket is `P(X_C=1, X_A=X_B=0)>=0`, the source's unique effective contribution, and cannot improve rescue if C disappears. The second term is the change in joint behavior of A/B, potentially **negative** if the removal desynchronizes survivors (hydra-like opportunity) or **positive** if it synchronizes them (potentially amplified collapse). Therefore complete source-supply interruption falls after losing C *only if* the desynchronization reduction is more negative than the unique donor loss term. This is a theorem about a one-step source-delivery opportunity, NOT an equality for true metapopulation persistence time or treatment effect.

### Exact known-truth examples (NO experimental observations)

Fixed baseline: surviving A/B are perfectly synchronous, each active with probability .5; C independent and active with probability .4. `Q_before=.30`. Removing C while holding A/B dynamics fixed gives `Q_static=.50`, harm +.20. But if removal makes A/B independent, each maintaining the same marginal active probability .5, `Q_after=.25`. Although mean active sources fell **1.4→1.0**, complete source interruption falls .30→.25, net −.05. The surviving source marginals have not changed; only joint synchrony changed.

Opposite fixed-marginal example: A/B were independent before removal, C active with probability .4, baseline `Q_before=.15`; removing C causes A/B to synchronize at their unchanged marginals .5, `Q_after=.50`. Direct donor loss +.10 and altered survivor synchronization +.25 jointly increase complete source failure by +.35.

These are **synthetic exact-probability examples** to check the equation and prospective identifiability. Existing v1.203 already proved pairwise covariance need not determine higher-order cofailure, so v1.246 is a distinct **intervention decomposition**, not new empirical evidence and not rebranding that prior theorem.

### Consequences for ecological mechanism testing

To distinguish the sign in natural island fragmentation, observe independently and directionally verified donor→target viable recruits, local source failures and repeated pre/post source joint delivery states with detection. Estimate the unique donor opportunity and the residual synchronization feedback **separately**, with habitat and shared climate shocks. Fox's measured endpoint was persistence; Matter/Roland's was spatial synchrony and immigration. Do not aggregate their published results as if they were repeated measures of one common effect size.

A comparison of original source distances or an increase in effective number of mapped sources is insufficient. The user-endpoint is future true colonization / persistence after an exogenous loss. Such data remain unavailable in Structural's closed empirical queue, and original GEB SCIENTIFIC HOLD, prior BALA non-support, eBird prohibition, and original mammal heldout firewall remain intact.
