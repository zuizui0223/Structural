# Structural v1.300–v1.309 — Cross-guild turnover is conditional, not yet a conserved forest signature

**2026-10-28. Actual independent taxonomic field observations, but one island and one previously outcome-exposed woody target. Source-status distinction is part of the science, not an implementation detail.**

## Main ecological question

Does spatial assemblage turnover in one guild tell us about turnover in a different guild after accounting for geographic distance? This matters because island and fragmentation monitoring often hopes to use one easily sampled taxonomic assemblage as a proxy for another.

**Do NOT** interpret a single taxonomic ratio, an association between guilds, or a shared plot label as direct habitat integrity, species persistence, tree–arthropod causality, or conservation intervention success.

## 1. Earlier ten-site Beetle→Woody result (v1.300): weak positive, context specific

On the exact original author-identical ten 50×50 m Terceira forest plots, after restricting original Beetle sampling to three methods shared among all sites at **six Events per site (60 total)**, source-observed taxon turnover predicted woody Jaccard turnover a little better than log physical distance alone:

| 10-site Beetle / Woody comparison | v1.300 observed |
|---|---:|
| Independent forest plots | 10 |
| Dependent plot pairs | 45 |
| Woody / Beetle detected taxa | 11 / 19 |
| Geography-only LOPO MSE | 0.0113032821 |
| Geography + Beetle LOPO MSE | 0.0107459614 |
| Gain (positive is lower error) | **+0.0005573207** |
| Relative LOPO-MSE reduction | **+4.93%** |
| 999 shuffled Beetle plot-label exceedance rank | 0.040 |

Original [run #40081020518](https://github.com/zuizui0223/Structural/actions/runs/40081020518), original artifact #12555172261, ZIP SHA256 `5a6926ecba21876c1cee72404de9d1eed39de9c7646acc2bdc267ef5be8a2107`.

This was **not** an independent archipelago replication. The original full-method Beetle sampling varied from 13 to 27 Events per plot, and its strict v1.298 full-sample comparability gate remains **TERMINAL**. A *different* fixed three-method subset (v1.299) was chosen before Beetle species values opened and was scored in v1.300. The apparent spatial guild signal is small, and the initial 999-permutation Monte Carlo interval extends across 0.05, as audited in v1.301.

## 2. Third guild, original Spider source: observed design quality failure

The author-source 2019 Spider data ([DOI 10.15468/kcgjfr](https://doi.org/10.15468/kcgjfr), v1.8; 423 Event and 1,639 Occurrence records) use the exact same ten normalized Terceira author plot IDs as the original Woody survey. The **first** frozen ten-site v1.303 protocol required every original Spider subevent to agree within **0.0003°** with the corresponding Woody plot coordinates and the dates to resolve as 2012–2013. It failed; later exact Event-only diagnostics explained why.

- Among 260 Terceira Spider source Event rows, **145** were written in day/month/year format rather than year-first; year was actually populated and numeric on all 260.
- **233** of the 260 source Event coordinates were within the source-time-fixed 0.0003° plot coordinate tolerance; **27** did not pass, spread over two original plots.
- One of these plots had a **systematic 0.000803° offset across 26 Events**. The other was mainly matched but had **one 0.01144° source coordinate outlier**.
- Original site IDs were **10/10 exact**, showing that name agreement does **not** ensure full physical measurement equivalence.

Original date/coordinate audits [v1.305 #40610110696](https://github.com/zuizui0223/Structural/actions/runs/40610110696) and [v1.306 #40610499954](https://github.com/zuizui0223/Structural/actions/runs/40610499954) examined **Event metadata only**, with zero original Spider or Woody species rows opened.

The old v1.303 and pre-conditional v1.304 **ten-site gate cannot be reclassified as a success**. All-ten Spider transfer remains unscored.

## 3. Separate post-Event, pre-Spider-response eight-site study: observed NON-SUPPORT (v1.307–v1.308)

A new explicitly exploratory v1.307 rule, frozen *after* seeing only author Event coordinate quality, retained exactly the **eight sites for which all original Spider Events were positionally compatible**, with all five common Spider sampling modes standardized at [2,3,3,4,11] original Events per plot. This selected **23 original Spider Events per plot, 184 total**. No Spider species values informed site or method selection. Event-source [run #40611215086](https://github.com/zuizui0223/Structural/actions/runs/40611215086) PASSED, four tests, 8/10 physical sites and 184 Event core IDs locked by SHA256. It is NOT confirmation of the old ten-site endpoint.

Original biological v1.308 [run #40611772269](https://github.com/zuizui0223/Structural/actions/runs/40611772269) passed five synthetic tests before opening the original taxon files, joined 402 source Woody and 1,639 Spider Occurrence records to original Event keys with **100% join completeness**, and admitted 717 Spider records inside the 184 response-blind original Event subset. There were 28 Spider operational taxa and 11 Woody taxa across eight sites. Only 22/717 (3.07%) selected Spider records had unresolved/unsupported name ranks, under the predeclared 5% cutoff.

| Eight EXACT plot Woody target | v1.308 original observed |
|---|---:|
| Independent forest plots / dependent dyads | 8 / 28 |
| Geography-only LOPO MSE | **0.0135436884** |
| Geography + Spider LOPO MSE | **0.0155154990** |
| Spider increment (positive would improve the prediction) | **−0.0019718106** |
| Change in predicted error | **+14.56%** (worse) |
| Original 999 Spider plot-label null exceedance rank | **0.867** |
| Spider improvement over geography | **NOT SUPPORTED** |

Original source artifact #12783532137, ZIP SHA256 `27745a70e17081189634c9ed59c558c03e48cdf69b847bda9715ad058c1abc65`, JSON SHA256 `6f4b92fe79a796db7fa57cc5273c7e0586960432e892ecba38b580c0a642da36`. Existing run was independently audited **without rerunning any species source** by the read-only [run #40612171049](https://github.com/zuizui0223/Structural/actions/runs/40612171049).

**This observation does NOT support a positive Spider↔Woody spatial predictive link** under the frozen eight-site, equal-Spider-methods comparison. The failure could reflect guild-specific ecological response, measurement bias, different COBRA sampling opportunity, or the two-site exclusion. It is not proof that spiders are ecologically independent of vegetation or that all island guilds are uncoupled.

## 4. Essential fair comparison (v1.309): same eight plots, same Woody response

The earlier **positive Beetle result used 10 plots**, whereas this **negative Spider result uses 8 plots**, so their sign difference alone is NOT evidence of taxon-specific structural coupling. Both relied on the **same Woody field lineage**, and both are single-island exploratory analyses.

The explicitly post-outcome, no-tuning **v1.309** protocol is therefore fixed to apply the **old v1.299 Beetle 6 original Event samples/site** to exactly the **same eight original author-coordinate-matched Tree plots** used by v1.308, preserving the same original Woody Jaccard and geography.

The new eight-site Beetle geography-only LOPO MSE **must reproduce 0.0135436884** from the Spider study within absolute 1e−10 or the candidate result STOPs. The only new numerical quantity is Beetle eight-site incremental MSE improvement; 999 Beetle plot-label permutations use the same fixed seed for a descriptive plot-level null. Original Spider species values are **not reopened**. If eight-site Beetle gain vanishes, the 10-site signal is likely spatial-subset-sensitive; if it persists, a taxon-specific or taxon-method-specific observational difference remains plausible, not causal.

## 5. Conservation inference ceiling

The shared ecological takeaway is **conditionality and sampling-design dependence** in cross-taxonomic biodiversity surrogacy: one source-observed forest guild may carry extra information about another in a specified plot frame, while a different guild or different plot subset need not. Before using a taxon as a biodiversity monitoring proxy, validate identical physical sites, sampling opportunity, source taxonomic resolution and independent plot-held-out predictions.

This is NOT evidence of metapopulation donor effects, colonization or demographic rescue; the original mapped-mammal **GEB scientific HOLD**, zero newly admitted confirmatory systems and eBird-off policy remain unchanged.

No original mammal/BioTIME/RLS or Macaronesia S2–S4 protected outcome was opened in these analyses.
