# v1.260 — Can donor loss paradoxically improve one-step recolonist availability?

## Ecological reason

Unconditional “losing a source always raises recolonization failure” is not valid when shared donor failure changes. However, claiming losing sources is good conservation would be equally wrong: two separate experiments have reported opposite synchrony responses to local extinction.

**Fox et al. (2017)** [DOI 10.1038/s41559-017-0271-y] used lab cyclic protist predator/prey metapopulations and catastrophes that killed a local population **without removing the habitat patch**. In high dispersal treatments, these transient extinctions prevented system-wide synchronization, increased recolonization and extended regional persistence. This **spatial hydra effect was their discovery**, not Structural's.

**Matter & Roland (2010)** [DOI 10.1098/rspb.2009.1520] experimentally removed **two adjacent Parnassius smintheus populations from a set of 17** Rocky Mountain alpine meadow populations, reducing immigration to remaining neighbors and *increasing* local abundance synchrony. Their paper predicts increased global extinction risk under some models; it does NOT report observed subsequent regional extinction caused by the experiment. These manipulations differ in duration and demographic context, and both empirical result directions are already published.

Both sides imply the relevant prediction is not “occupied donor count” alone. It must specify at least: (i) whether the removal is transient and habitat survives, (ii) loss of mean viable source supply, (iii) local donor cofailure covariance and its before/after change, (iv) the realized source→target arrival process, and (v) target colonization/persistence after the intervention. The original Structural v1.123 source-leverage hypothesis remains **future-only** and unconfirmed.

## Exact counterexample (known truth, not new biology)

Let a metapopulation have n potential donor populations each with **the same marginal failure probability** q. A common catastrophic shock wipes all donors with probability c. Conditional on no shared shock, donors fail independently with probability p=(q−c)/(1−c). Hence the unconditional failure probability of every donor is always q, while the pairwise failure correlation is c(1−q)/(q(1−c)). A surviving donor independently succeeds in delivering an effective immigrant to one designated target with probability a. Then:

`P(no arrival | n,q,c,a)=c+(1-c)[1 - a(1-q)/(1-c)]^n`

`E(number of effective arrivals)=n(1-q)a`

We compare pre-intervention n=4,c=.22 with post-intervention n=3,c=.01 (holding q=.35). This *hypothesizes* that a source removal is accompanied by loss of spatial synchrony. For a=.30 donor removal **raises** the probability of zero arrivals. For a=.75 it **lowers** the probability, even though the expected *number* of arrivals falls at both a values. An interior nontrivial threshold a* separates these outcomes. If c remains .22 after loss, zero-arrival risk instead rises for every a>0. These facts are verified by a second exact enumeration of all possible donor viability states, not by invented source or validation data.

The model answers “can these opposing channels mathematically coexist in a specified delivery mechanism?” It does **NOT** show the donor correlation drop really follows biological extinction, that a is equal to microcosm mixing rate, that arrival implies successful establishment, or that regional persistence improves. The numerical choice is an illustrative known-truth witness—not a parameter fit.

## Structural-specific discriminating observation

A future independent experiment/site panel must record pre-intervention counts/donor phase or covariance, post-loss *changes* in synchrony, prospective source viability and realized transfers, and a target's subsequent detection-adjusted 0→1 colonization or 1→1 persistence. For causal mediation, estimate or manipulate the synchrony route independently; conditioning blindly on post-treatment synchrony can be biased. Complete between-system independent validation after the v0.31/v0.42 estimability gate is required. The intervention contrasts should never equate an island's permanent destruction with transient microcosm extinction.

Previously published Fox and Matter signs are background prior art, not newly confirmed results. The separate follow-on source metadata intake is **not** a confirmatory replication. GEB scientific HOLD unchanged; no original protected mammal responses/predictions or eBird used.
