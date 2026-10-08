# Global mammal graph nodes were selected upstream using mammal occurrence (v1.218)

Barreto et al. (2021), *Proceedings of the Royal Society B*, doi:10.1098/rspb.2021.1879, state that islands with no mammal mapped by IUCN were omitted. Islands of uncertain taxon attribution and with missing physical/environmental covariates were also excluded. Their scientific question was mammal richness and endemism on islands containing mammals. The Structural question about island-source geographic networks has a different target population.

The compiled mammal binary matrix contained 5,592 islands, before Structural's sealed-block quarantine of 15 and source-overlap removal of 176; exactly 5,401 remained. Geographic kNN edges were calculated only among these 5,401 retained nodes. Thus the edges were independent of focal heldout responses **conditional on the selected universe**, yet the node universe itself had been filtered using *community-wide mapped mammal presence* before the study's holdout.

This is not a claim of a broken response firewall: heldout focal-species labels were sealed, and outcome-dependent modeling within this eligible universe is prohibited. The source compilation's conditioning is upstream of that firewall.

Important ecological consequence: completely mammal-zero islands from the IUCN source mapping were unavailable as heldout prediction targets and also absent as physical intermediate graph nodes. For a focal species, its mapped 'absence' was evaluated only among islands with some mapped mammal. Such conditional predictive results cannot be extended to the entire oceanic island universe or to immigration/establishment on empty islands without new independent observations and an ex-ante complete physical island frame.

Do not infer the number of missing islands or the sign/size of selection bias from the published 5,592 and the approximately 17,000 islands above 1 km2 quoted by Barreto et al.; definitions and covariate/region eligibility differ. Do not claim the negative source-influence turnover proves population redundancy. Original v1.119, v1.181 and BALA results remain untouched; GEB is still scientifically on HOLD.

Source article: https://doi.org/10.1098/rspb.2021.1879 ; original Dryad: https://datadryad.org/dataset/doi%3A10.5061/dryad.hmgqnk9j2 .
