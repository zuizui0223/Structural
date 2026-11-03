# Decadal arthropod turnover coincides with spatial convergence of beetle communities in island forests

**ANONYMIZED WORKING MANUSCRIPT — research article candidate, Journal of Biogeography**  
Version v1.345, 2 November 2026. Not submitted. Authors, affiliations, funding, permits, conflict statements and final data/code release require author confirmation. All analyses below are from the original 2024 BALA archived data; no new field collection is represented.

**Running title:** Two dimensions of island turnover

## Abstract

**Aim:** Species richness may remain stable while species identities change, but temporal turnover within sites does not determine whether spatial assemblages converge or diverge. We tested both dimensions in oceanic island forests and examined whether richness increases can accompany spatial homogenization.

**Location:** Azores, North Atlantic Ocean; seven islands.

**Taxon:** Ground-sampled spiders (Araneae) and beetles (Coleoptera).

**Methods:** We reanalysed three campaigns of published BALA arthropod records using 29 source-identical native-forest transects and a predetermined, equalized number of sampling events within transects and methods. We decomposed B1-to-B3 temporal compositional dissimilarity and compared cross-campaign half-sample dissimilarity with contemporaneous, disjoint half-sample differences. Independently of temporal change within transects, we compared within-island spatial Simpson and Sørensen beta diversity between B1 and B3, using the same physical forest-transect pairs. Islands were weighted equally.

**Results:** Cross-campaign Sørensen dissimilarity exceeded within-campaign sampling heterogeneity on all seven island means in both spiders (excess 0.191; 29 eligible transects) and beetles (0.221; 26). Nevertheless, spatial trajectories differed. Mean within-island Simpson beta declined for beetles (B3−B1 = −0.175; four islands homogenized) but was approximately stable for spiders (+0.022; heterogeneous island signs). The beetle mean remained negative after omitting any single island and across 18 predefined complementary half-sample partitions, but its exploratory seven-island 95% t interval (−0.440 to +0.089) included zero. In three of four homogenizing beetle islands, mean local observed species richness increased.

**Main conclusions:** Observed long-term species-identity change within island forests can coexist with spatial convergence, even where local richness rises, without establishing a universally negative spatial trend. Distinguishing temporal replacement, local richness and spatial community differentiation is necessary to describe island biodiversity trajectories. These detection-based observations do not establish actual colonization, extinction or a causal driver of homogenization.

**Keywords:** Azores; arthropods; beta diversity; biotic homogenization; Coleoptera; community assembly; island biogeography; long-term monitoring; species replacement.

---

## 1 | Introduction

Interpreting long-term biodiversity change requires distinguishing how many species are present from which species are present, and how communities are arranged across a landscape. Global assemblage analyses have shown that substantial changes in species identities can occur without uniform changes in local richness (Dornelas et al., 2014; Hillebrand et al., 2018). These results have moved biodiversity monitoring beyond single-number richness trends. They leave a second question: when local membership changes, do sampled communities become more similar or more differentiated from one another? The direction is not fixed by turnover within individual sites.

Biotic homogenization has a precise spatial meaning: similarity among places increases as identities and occurrences change (Olden & Rooney, 2006). Invasions, local losses and environmental changes can yield this pattern, but detecting homogenization does not identify which process acted. The converse, increasing differentiation, can also occur under anthropogenic change, and high spatial beta diversity is not invariably a desirable conservation outcome (Socolar et al., 2016). Decomposing beta diversity into species-replacement and richness-difference components further clarifies that even identical net richness trajectories can conceal different spatial organizations (Baselga, 2010).

Oceanic island forests provide a useful context for comparing these dimensions because native communities are geographically bounded and distributed among discrete forest fragments. Such a setting also brings limitations: island histories, fragment size, elevation, land-cover change and survey accessibility differ. Apparent island-wide relationships need not reflect a single causal mechanism, and samples within one island are not independent island replicates. Understanding forest community trajectories therefore requires tracking fixed physical sampling locations, separating plot-level temporal change from island-level spatial beta change, and reporting the original island as a unit of geographic replication.

The long-term BALA arthropod monitoring programme in the Azores provides three survey campaigns spanning approximately two decades. Pozsgai et al. (2026) used these records to show broadly stable aggregate abundance, biomass and richness but heterogeneous individual-species trends. These findings are prior published evidence. Our contribution is not to rediscover richness stability. Instead, we ask whether the *same source-observed forest assemblages* underwent temporal identity replacement beyond contemporaneous sampling differences and, separately, whether the network of sampled forest transects converged or diverged spatially.

We evaluate three predictions. First, between-campaign species dissimilarity should exceed within-campaign differences generated by disjoint, equal-effort sub-samples if detected compositional change is not captured by contemporaneous sample heterogeneity alone. Second, temporal replacement should not force the same sign of spatial beta change in spiders and beetles; group-specific spatial coordination is an empirical question. Third, forest assemblages may converge while local richness rises, so alpha-richness change should not be used as a surrogate for spatial distinctiveness. These are observational predictions; we do not test an invasion, climate or dispersal mechanism.

## 2 | Materials and Methods

### 2.1 | Source, islands and unit of analysis

We used the University of the Azores BALA sampling-event archive (GBIF DOI 10.15468/rpdkx9), version 1.0, from which the original fixed source contains 10,379 Event records and 63,904 associated Occurrence records. Its archive SHA-256 is \`4b83fda7df412dc278d709d974bcda4c2fc1d423dfdea2e36f89656f27acc8a2\`. BALA surveys native forests on Faial, Flores, Pico, São Jorge, São Miguel, Santa Maria and Terceira. The publisher's accompanying study described 30 monitoring locations; only 29 physically author-identical transects met our fixed three-campaign matching rule. We did not treat the Event records or individual Occurrence records as independent forest locations.

The source survey periods were B1 (1997–2004), B2 (2010–2012) and B3 (2019–2022) as encoded in the fixed archived sampling-event design. The primary contrasts below compare B1 with B3. The original published study uses slightly different narrative period boundaries; our period labels denote the exact archived-source eligibility windows, not survey-year equality across the entire archipelago. Island-level summaries distinguish seven geographic contexts; the 29 transects are the physical within-island sampling locations.

### 2.2 | Fixed sampling opportunities and taxonomic assignment

Before examining species values for the new response, each island–source-locationID transect present in all three campaigns was identified. For each transect and each original collection method separately, we counted sampling Events in B1, B2 and B3. We retained \`k\` Events per campaign, where \`k\` was the smallest original count across the three campaigns for that transect and method. Eligible source Event IDs were selected by lexicographic ordering of original author core IDs, without consulting taxa, abundances or subsequent results.

This produced 29 physical transects × two methods × three campaigns, with 4,620 original selected Events in all: 1,540 per campaign (781 pitfall and 759 canopy-beating Events per campaign). The source Event membership is frozen by SHA-256 \`39db7c6db04e022b495e233506e9c9774d8e1cf9e2e1c35830bbe6aadce9d6ac\`. Equal Event counts standardize the number of recorded sampling opportunities; they do not guarantee equivalent detection probabilities or exact within-plot trap placement across decades.

The primary biological analysis used pitfall observations, separately for spiders (order Araneae) and beetles (order Coleoptera). Original \`scientificName\` labels were normalized only for case and whitespace. Species, subspecies and author-designated morphospecies ranks were eligible, and repeated records of the same operational taxon were collapsed to presence within each physical transect × campaign × method. Higher-rank unidentified observations were not treated as named species; original occurrences without taxon detections were not silently converted to observed absence. Canopy beating was evaluated as a secondary collection-method context, not pooled with pitfall.

### 2.3 | Temporal turnover within physically matched transects

For each qualifying transect and guild, let \(S_1\) and \(S_3\) denote the B1 and B3 detected species sets. Let \(a=|S_1\cap S_3|\), \(b=|S_1\setminus S_3|\) and \(c=|S_3\setminus S_1|\). We calculated Sørensen dissimilarity as

\[
\beta_{\mathrm{sor}}=\frac{b+c}{2a+b+c}
\]

and the Simpson replacement component as

\[
\beta_{\mathrm{sim}}=\frac{\min(b,c)}{a+\min(b,c)},
\]

with zero when the latter denominator was zero for nonempty sampled assemblages. These are compositional indices for **detected species sets**, not directly observed population extinctions or immigrations. We also reported absolute net richness differences \(\left||S_3|-|S_1|\right|\) and the proportion of sites whose matched species changes were classified as balanced replacement while net richness differed by no more than one operational taxon. The pre-frozen source scorer defines the exact balanced-replacement convention; it was not reselected post hoc.

To distinguish sampling heterogeneity from larger campaign differences, we used a separate, explicitly retrospective control: for each source transect, method and campaign, rank original source Event IDs by SHA-256 of a predefined salt and ID. Divide each original set into two disjoint halves with equal Event counts. Nine fixed salts generated nine alternative partitions of the *same* original source, not nine separate experiments. For a given partition, we calculated the average of within-campaign B1A–B1B and B3A–B3B Sørensen dissimilarities, and the mean of all four equal-half B1-versus-B3 comparisons. Their difference is the inter-campaign dissimilarity **in excess of** observed within-campaign half-sample heterogeneity. The same comparison was carried out for Simpson replacement.

A site–guild contrast was eligible only when all four half-sample taxa sets were nonempty in at least five of nine predefined partitions. The eligibility gate admitted 29 spider and 26 beetle pitfall transects, representing all seven original islands for each group. Zero detection was not recoded to similarity zero. We averaged valid partitions within physical transects, then averaged transects within islands and finally gave each island equal weight. We did not estimate formal biological confidence intervals or p-values from the nine highly dependent partitions.

### 2.4 | Spatial homogenization versus differentiation among transects

The second outcome has a different ecological unit and question. Within each island and each campaign, we computed pairwise Simpson and Sørensen dissimilarities **between distinct forest transects**, using the exact same pair of source-identified physical sites in B1 and B3. The spatial change for an island and guild is the mean pairwise B3 minus B1 beta value. A negative change means sampled communities became compositionally **more similar** (spatial homogenization), and a positive change means differentiation.

A source site with insufficient named species in either B1 or B3 was not used for the spatial comparison, resulting in 29 spider sites (56 dependent same-island site pairs) and 28 beetle sites (49 dependent pairs). Pairwise comparisons reuse source sites and are **not** independent replicates. We therefore reported island-level means and an equal-weight average over the seven islands rather than artificially treating 56 or 49 pairs as a sample of independent island changes.

We assessed descriptive stability by (i) repeating the source fixed nine-salt sampling-opportunity split with complementary halves (18 non-independent sensitivity estimates per guild) and (ii) recalculating the equal-island mean after omitting each of seven islands in turn, using source-frozen numerical island summaries alone. Neither is a prospective cross-island validation or a test of statistical significance.

### 2.5 | Island-unit uncertainty and the difference between robustness and inference

The island—not the within-island pair of transects, trap Event, or half-sample salt—was the unit of the supplementary uncertainty audit. As an explicitly **post hoc exploratory** check, we calculated the unweighted mean of seven island values, their sample standard deviation, and a conventional 95% Student-t interval for the mean using six degrees of freedom. We also enumerated all \(2^7=128\) sign assignments to the seven original island effects and reported the two-sided fraction yielding an absolute mean at least as large as observed. Such sign flips presume an exchangeable, symmetric island-level zero-centred null, and the t interval presumes independent island contexts. Neither premise is guaranteed among islands of the same archipelago; the calculations are **conditional descriptive diagnostics**, not prespecified confirmatory tests or complete ecological confidence intervals. Multiple outcomes were examined without multiplicity correction.

The same audit summarized the beetle-minus-spider spatial Simpson change paired by island. However, the guilds had 28 and 29 physically eligible plots respectively, so this paired island-context comparison was not interpreted as a formal species-group interaction. We evaluated uncertainty in both the temporal between-minus-within sampling contrast and the separate spatial B3−B1 Simpson contrast; the previously reported seven leave-one-island-out and 18 half-Event values remained non-independent sensitivity analyses.

### 2.6 | Local richness, source provenance and scope of inference

For each forest transect, the original number of named detected taxa per campaign provided an alpha-richness summary. We identified islands in which mean B3 local beetle richness exceeded B1 while spatial Simpson beta declined. We also inspected pooled detected island taxa as descriptive context, not an estimate of complete island gamma diversity.

All biological source runs were completed once under fixed source identity and subsequently sealed; the additional numerical audits use only committed original aggregate files. The original v1.314, v1.316 and v1.318 source executions, plus the source-free v1.344 arithmetic, are listed in the data and code statement. The aim is an interpretable spatiotemporal observation rather than an environmental driver analysis. We did not fit climate, invasion, fragment or source–sink causal models to these data.

## 3 | Results

### 3.1 | Species membership changed within forest transects

The 29 pitfall spider comparisons showed mean B1–B3 Sørensen dissimilarity of **0.470** and Simpson replacement of **0.349** across island-equal summaries. The 28 beetle comparisons showed Sørensen **0.616** and Simpson **0.511**. Absolute site richness change averaged **2.07 detected taxa** for spiders and **2.42** for beetles. In 23 of the 57 site × guild comparisons (**12 spider and 11 beetle**) balanced species replacement was observed even though the net richness difference was at most one operational taxon. This is consistent with earlier source-published aggregate richness stability but addresses a distinct, within-transect identity-change outcome.

Temporal between-campaign half-sample Sørensen dissimilarity was greater than the within-campaign half-sample reference in every island mean for each guild (Fig. 1). Spiders averaged **0.486 between** versus **0.295 within**, giving excess **+0.191** across 29 qualified transects. Beetles averaged **0.644 between** versus **0.423 within**, giving excess **+0.221** across 26 qualified transects. At the source physical-site level, 26/29 spider and 25/26 beetle comparisons had a positive between-minus-within difference. The same contrast for Simpson replacement was **+0.168** for spiders and **+0.245** for beetles. The large within-period baselines indicate substantial variation among sampling subsets even in a nominally common survey period; the excess does not amount to correction for all false absences or taxonomic drift. In the exploratory island-unit uncertainty audit, both temporal excess means had descriptive seven-island 95% t intervals above zero (**spiders +0.114 to +0.268; beetles +0.181 to +0.262**), with an unadjusted two-sided 128-sign-flip tail of **0.0156** for each. The islands share one archipelago, and the original sampling process remains imperfect, so these values are not a test of true population extinctions or immigration.

### 3.2 | Spatial beta diversity followed different trajectories

The island-equal change in between-transect Simpson beta diversity was **−0.1753** in beetles, but **+0.0224** in spiders (Fig. 2). A similar contrast appeared for spatial Sørensen dissimilarity (beetles **−0.1238**; spiders **+0.0487**). Nevertheless, the spatial direction was not uniform among islands. Beetles homogenized on **Flores (−0.5603), São Jorge (−0.4167), Santa Maria (−0.4015) and Terceira (−0.1286)**, while Faial (+0.1778), Pico (+0.0972) and São Miguel (+0.0050) differentiated or were approximately unchanged. Spiders differentiated on four islands and homogenized on three. The signs of spider and beetle spatial Simpson changes differed on Flores, Pico and Santa Maria.

The negative beetle spatial Simpson mean was stable under the fixed sensitivity summaries: it remained negative across **18/18** complementary half-Event estimates, and after dropping each island once, with leave-one-island-out means ranging from **−0.2342 to −0.1111**. These 18 samples and seven leave-one-out values are dependent re-expressions of the same biological data, not separate field replications or evidence of a common directional shift on all seven islands. The spiders' weak positive mean was less stable: only **13/18** half-effort estimates preserved the positive Simpson direction, and deletion of two islands reversed the mean.

**Island-level uncertainty qualified the directional inference.** The seven-island mean spatial Simpson change for beetles was −0.1753, but its exploratory 95% t interval was **−0.440 to +0.089**, with a two-sided 128-sign-flip tail probability of **0.188**. For spiders, the corresponding interval was **−0.113 to +0.158** (two-sided sign-flip **0.688**). The beetle-minus-spider paired island-context change averaged −0.1977, with an exploratory interval **−0.497 to +0.102** and two-sided sign-flip probability **0.172**. All three intervals include zero, so neither a population-wide negative spatial shift nor a statistically established guild contrast follows from the available seven island contexts (Table S1). The observed beetle direction remains a useful, explicitly descriptive sample result.

### 3.3 | Forests could gain local beetle species while becoming more similar

Three islands combined a negative spatial beetle Simpson change with an increase in the mean number of locally detected beetle taxa: **Flores** (5.00→8.25 taxa/site; spatial change −0.5603), **São Jorge** (3.00→3.75; −0.4167) and **Santa Maria** (13.50→16.50; −0.4015) (Fig. 3). The fourth homogenizing island, Terceira, showed a small mean decline in local beetle richness (5.57→5.43; −0.1286).

These examples demonstrate that the observed loss of spatial differentiation did not require a reduction in sampled local richness. Inferences are especially limited for Santa Maria, which had only two eligible source beetle sites (one spatial pair), and for island-specific estimates that share sampling sites with many pairwise comparisons.

## 4 | Discussion

### 4.1 | Temporal reassembly and spatial convergence are not interchangeable

Our clearest result is not the already-known possibility of turnover without richness loss. It is that the *same network of long-term island forest observations* permits two contrasting biodiversity trajectories to be quantified independently. Spiders and beetles both underwent large temporal changes in detected species identities that exceeded contemporaneous split-sample differences at the source island level. Yet beetle communities became more similar among the sampled forests on average, whereas spatial spider changes were smaller and more mixed. The negative beetle average survived both site-effort splitting and all single-island deletions, but its seven-island t interval and the exploratory sign-flip test did not establish a nonzero mean shift in a wider population of islands.

This distinction matters because temporal beta diversity and spatial beta diversity answer different questions. A high B1–B3 temporal dissimilarity says that species detected at a fixed transect differ across campaigns. It does not reveal whether the species found at *other* transects are now more similar to those found at the first. The spatial comparison requires matched physical locations observed contemporaneously, not a compositional replacement rate inferred from site totals. Our results operationalize the conceptual separation already emphasized by Olden and Rooney (2006) and Socolar et al. (2016) in a native-forest island time series.

### 4.2 | Why increasing local richness need not preserve regional distinctiveness

Local species richness counts membership without identifying its geography. If geographically widespread taxa are detected at more sites while more locally distinctive taxa are less frequently detected, communities can converge even as individual sites gain named taxa. In Flores, São Jorge and Santa Maria, our beetle data showed exactly the *joint metric pattern* of rising local richness and declining spatial Simpson beta. However, we did **not** establish that widespread introduced taxa expanded, or that geographically restricted endemics declined specifically at those sites. The compatible mechanism is a hypothesis, not an inferred cause.

This distinction has practical conservation significance. Monitoring solely the number of detected taxa at each native forest location can miss loss of spatial individuality across a network. Conversely, a rise in spatial dissimilarity does not automatically imply conservation success, because a degraded assemblage could also become distinctive. Protected-area assessment should therefore present local richness, species identities, and within-island spatial beta together, including explicit origin/taxonomic information where robustly sampled.

### 4.3 | Group differences and the limits of attribution

The spatial trajectories of spiders and beetles may reflect differences in dispersal, microhabitat association, population histories, environmental sensitivity or detectability. The present results do not distinguish among those explanations. Sampling by pitfall captures a method-specific subset of each group, and source-defined taxonomic resolution includes morphospecies. Canopy sampling cannot be treated as a fully comparable alternative; the original canopy-beetle detection gate admitted only 22 sites for the spatial endpoint and was stopped. An explicit paired-island comparison gave a beetle-minus-spider mean change of −0.198, but its exploratory t interval spanned zero (−0.497 to +0.102). Consequently, we do not claim a statistically significant beetle–spider interaction, a trait-mediated causal filter, or identical detection dynamics.

A further limitation concerns the biogeographic scale. Seven islands supply multiple island contexts *within one archipelago*, not seven independent archipelago-scale tests. Within-island pairwise distances are correlated because each source transect appears in several pairs. Environmental changes over the decades, forest fragmentation, dispersal barriers, local disturbance, taxonomic revisions and phenological differences are not separately identified. The unequal original survey year windows and the considerable same-campaign half-sample dissimilarity preclude claims of true local colonization or extinction based solely on presences and absences. Our original-source outcome counts are therefore conservative statements about **observed community composition**, not population demography.

### 4.4 | Contribution relative to existing work

Dornelas et al. (2014) and Hillebrand et al. (2018) established the general case for compositional monitoring beyond richness. Pozsgai et al. (2026) analysed the same Azorean BALA field lineage and found broadly stable long-term abundance, biomass and richness, while highlighting heterogeneous trends in species. The present reanalysis adds a *within-site sampling-heterogeneity benchmark* and a *same-island spatial convergence/differentiation trajectory* under physically matched sampling. The taxonomic source and its earlier richness conclusions are prior art, whereas these defined spatiotemporal contrasts constitute a separate derived analysis.

The results are strongest as a demonstrated boundary on inference: observed long-term species replacement does not determine the sign of spatial biodiversity change; average beetle convergence can arise in surveyed forests whose local richness increases. Establishing which species and environmental processes cause this convergence would require independent time-matched monitoring of forest fragments and surrounding habitat, measured detection probabilities, and environmental covariates. Those causal statements should not be retrofitted to the current dataset.

## 5 | Conclusions

Across seven sampled Azorean islands, pitfall spider and beetle communities showed marked observed species-identity reorganization between early and recent BALA campaigns relative to within-campaign sampling heterogeneity. Among the sampled forests, only beetles exhibited a negative island-equal spatial Simpson beta direction across the existing source-free sensitivity checks, although the seven-island uncertainty interval included zero. In several islands, the observed convergence coincided with increases in mean local beetle richness. Temporal replacement, local richness change and spatial homogenization are therefore distinct dimensions of island forest biodiversity, and their separate measurement changes the conclusions one can draw from apparent population or assemblage stability.

## Data availability and reproducibility

All empirical source records are publicly available from the University of the Azores BALA sampling-event archive (GBIF DOI: https://doi.org/10.15468/rpdkx9). To preserve double-anonymous review, the manuscript analysis code, source-selected Event-ID fingerprint and source-free island-level numerical summaries will be provided as a **blinded reproducibility supplement** for peer review; an openly attributed repository link and any archival DOI must be supplied only when actually issued. Exact selected Event membership SHA-256 and original source archive SHA-256 are reported in Methods. Species data need not be redistributed because the publisher's original archived observations are publicly accessible. The source-free figure generation and numerical audit can be rerun without reopening the original species tables.

## Declarations requiring author review before submission

- **Authors and contributions:** Pending verification with the researchers and original-data custodians; do not invent author agreements or imply the primary BALA data collectors approved this derived manuscript.
- **Acknowledgements and funding:** Pending confirmation.
- **Ethics / permits:** No new animals were sampled in this reanalysis; original survey permit details require confirmation from primary sources.
- **Conflicts of interest:** Must be completed by the submitting authors.
- **Data and code license:** Use the original BALA data under its publisher's terms and cite the exact GBIF dataset version; confirm any code repository license before public archive deposition.
- **Review format:** Prepare an anonymized main manuscript and separate title page as required by Journal of Biogeography.

## Figure legends

**Figure 1.** Temporal species identity change exceeds contemporaneous half-sample heterogeneity in both taxa. The seven island-mean B1-to-B3 minus within-period split-half Sørensen values are plotted separately for Araneae and Coleoptera. The same-period and between-period island-equal averages are shown as a supporting panel. Island dots are the seven geographic contexts; nine source salt partitions are methodological sensitivity replicates, not independent field samples.

**Figure 2.** Within-island spatial compositional change in matching forest-transect pairs. Island-level B3−B1 Simpson beta changes are shown for spiders and beetles; negative values imply increasing similarity among sampled sites. Overall island-equal means and source-free leave-one-island-out ranges are presented descriptively. The post hoc seven-island t intervals are given in Table S1 and include zero for both guilds; they are not archipelago-independent confidence intervals. Physical forest-transect counts were 29 and 28 respectively; dependent pairs (56/49) are not experimental replicates.

**Figure 3.** Alpha richness and spatial beta may change in opposite directions. Mean local beetle richness change (B3−B1) on the horizontal axis is shown against change in within-island Simpson beta on the vertical axis. Labels highlight Flores, São Jorge and Santa Maria: observed local richness increased while spatial dissimilarity fell. The single spatial pair on Santa Maria warrants caution; points are island means, not independent tests of a causal association.

## References (verified source details; format for journal at submission)

Baselga, A. (2010). Partitioning the turnover and nestedness components of beta diversity. *Global Ecology and Biogeography*, 19, 134–143. https://doi.org/10.1111/j.1466-8238.2009.00490.x

Dornelas, M., Gotelli, N. J., McGill, B., Shimadzu, H., Moyes, F., Sievers, C. & Magurran, A. E. (2014). Assemblage time series reveal biodiversity change but not systematic loss. *Science*, 344, 296–299. https://doi.org/10.1126/science.1248484

Hillebrand, H., Blasius, B., Borer, E. T., et al. (2018). Biodiversity change is uncoupled from species richness trends: Consequences for conservation and monitoring. *Journal of Applied Ecology*, 55, 169–184. https://doi.org/10.1111/1365-2664.12959

McKinney, M. L. & Lockwood, J. L. (1999). Biotic homogenization: A few winners replacing many losers in the next mass extinction. *Trends in Ecology & Evolution*, 14, 450–453. https://doi.org/10.1016/S0169-5347(99)01679-1

Olden, J. D. & Rooney, T. P. (2006). On defining and quantifying biotic homogenization. *Global Ecology and Biogeography*, 15, 113–120. https://doi.org/10.1111/j.1466-822X.2006.00214.x

Pozsgai, G., Cardoso, P., Fattorini, S., et al. (2026). Stability in the face of global decline: A 20-year study of arthropods in an oceanic archipelago. *Scientific Reports*, 16, 27703. https://doi.org/10.1038/s41598-026-57146-5

Pozsgai, G., Lhoumeau, S., Amorim, I. R., et al. (2024). The BALA project: A pioneering monitoring of Azorean forest invertebrates over two decades (1999–2022). *Scientific Data*, 11, 368. https://doi.org/10.1038/s41597-024-03174-7

Socolar, J. B., Gilroy, J. J., Kunin, W. E. & Edwards, D. P. (2016). How should beta-diversity inform biodiversity conservation? *Trends in Ecology & Evolution*, 31, 67–80. https://doi.org/10.1016/j.tree.2015.11.005

University of the Azores (BALA source data). Original three-campaign sampling-event data set, version 1.0. GBIF DOI https://doi.org/10.15468/rpdkx9 (specific dataset authorship and citation to follow original publisher metadata).

---

### Internal non-submission notes (remove from anonymized manuscript)

- **Publication caveat:** This is the **same underlying source** used by Pozsgai et al. (2026); make novelty precisely the separate beta estimand and sampling control, and consult primary data authors/custodians regarding attribution, overlap and ethics before journal submission.
- **Current evidence status:** Site-level ecological inference is observational; no formal uncertainty model that simultaneously respects original island and forest fragment clustering has been validated.
- **Potential weakness:** The assertion of long-term "stable richness" should be explicitly attributed to the published source study, not presented as a new independent test; spatial convergence is a group average with 4/7 negative island signs, not a seven-island universal trend.
- **Do not pool:** Separate SLAM/PRIBES/Madeira/Galápagos studies are not physical/method-matched confirmations or equivalent causal habitat replications. See PRs #462–#468 for their positive/negative/terminal status.
