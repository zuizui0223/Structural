# Verified references for macro dual-isolation manuscript v1.86

This file is a submission-facing reference audit for `manuscript/macro_dual_isolation_mammal_v1_86.md`.

The role column is deliberately narrow. A citation may support the stated prior concept without implying that it already tested the present species-conditioned, training-only occupied-source-topology estimand.

| Reference | Verified record | Role in manuscript | Must not be used to claim |
|---|---|---|---|
| MacArthur & Wilson 1967 | MacArthur, R. H. & Wilson, E. O. *The Theory of Island Biogeography*. Princeton Univ. Press. | Classical colonization/extinction and mainland-source framing. | That mainland distance is the only meaningful isolation axis. |
| Hanski 1994 | Hanski, I. (1994). Patch-occupancy dynamics in fragmented landscapes. *Trends in Ecology & Evolution* 9:131–135. DOI 10.1016/0169-5347(94)90177-5. | Occupancy can depend on surrounding occupied habitat / colonization context. | Static graph paths are realized colonization routes. |
| Fahrig 2013 | Fahrig, L. (2013). Rethinking patch size and isolation effects: the habitat amount hypothesis. *Journal of Biogeography* 40:1649–1663. DOI 10.1111/jbi.12130. | Nearby habitat/source amount can redefine effective isolation; each patch can have a different potential immigrant pool. | Habitat-amount theory is equivalent to species-conditioned source topology. |
| Weigelt & Kreft 2013 | Weigelt, P. & Kreft, H. (2013). Quantifying island isolation—insights from global patterns of insular plant species richness. *Ecography* 36:417–429. DOI 10.1111/j.1600-0587.2012.07669.x. | Global evidence that island isolation is multidimensional: mainland distance, surrounding land, stepping stones, large-island sources and related metrics differ in explanatory value. | Species-conditioned occupied-source topology was tested. |
| Sillero et al. 2018 | Sillero, N., Biaggini, M. & Corti, C. (2018). Analysing the importance of stepping-stone islands in maintaining structural connectivity and endemicity. *Biological Journal of the Linnean Society* 124:113–125. DOI 10.1093/biolinnean/bly033. | Island-network / graph-theoretic structural connectivity and stepping stones can matter within archipelagos. | Structural connectivity is equivalent to realized species-specific source connectivity. |
| Carter et al. 2020 | Carter, Z. T., Perry, G. L. W. & Russell, J. C. (2020). Determining the underlying structure of insular isolation measures. *Journal of Biogeography* 47:955–967. DOI 10.1111/jbi.13778. | Sixteen isolation measures reduce to distinct mainland-distance, stepping-stone and insular-network axes. | Generic isolation components already condition on the focal species' occupied sources. |
| König et al. 2021 | König, C. et al. (2021). Source pools and disharmony of the world's island floras. *Ecography* 44:44–55. DOI 10.1111/ecog.05174. | Island biogeography can explicitly model source regions/source pools rather than treat all external areas as equivalent. | Their source-pool framework tests occupied inter-island source-network topology. |
| Cornell & Harrison 2014 | Cornell, H. V. & Harrison, S. P. (2014). What are species pools and when are they important? *Annual Review of Ecology, Evolution, and Systematics* 45:45–67. DOI 10.1146/annurev-ecolsys-120213-091759. | Species pools link regional availability and local community assembly; pool definition and spatial scale matter. | A regional species pool is identical to a realized occupied-source graph. |
| Berlow et al. 2013 | Berlow, E. L. et al. (2013). A network extension of species occupancy models in a patchy environment applied to the Yosemite toad (*Anaxyrus canorus*). *PLoS ONE* 8:e72200. DOI 10.1371/journal.pone.0072200. | Network structure can be incorporated directly into patch-occupancy models. | The present global held-out incremental test is methodologically unprecedented simply because it uses a graph. |
| Ortiz-Rodríguez et al. 2019 | Ortiz-Rodríguez, D. O., Guisan, A., Holderegger, R. & van Strien, M. J. (2019). Predicting species occurrences with habitat network models. *Ecology and Evolution* 9:10457–10471. DOI 10.1002/ece3.5567. | Habitat quality, weighted connectivity and network topology can jointly predict patch occurrence. | Existing habitat-network models already test the exact R3→C incremental estimand used here. |
| Daniel et al. 2023 | Daniel, A. et al. (2023). Validating graph-based connectivity models with independent presence–absence and genetic data sets. *Conservation Biology* 37:e14047. DOI 10.1111/cobi.14047. | Graph-based connectivity can be evaluated against ecological and genetic data rather than assumed valid. | Graph connectivity in this manuscript is genetically or mechanistically validated. |
| Wang et al. 2023 | Wang, D. et al. (2023). Nearby large islands diminish biodiversity of the focal island by a negative target effect. *Journal of Animal Ecology* 92:492–502. DOI 10.1111/1365-2656.13856. | Nearby islands can act as sources, stepping stones or competing colonization targets; source/target context is richer than mainland distance. | Their negative target effect establishes the present occupancy-constraint mechanism. |
| Schrader et al. 2021 | Schrader, J., Wright, I. J., Kreft, H. & Westoby, M. (2021). A roadmap to plant functional island biogeography. *Biological Reviews* 96:2851–2870. DOI 10.1111/brv.12782. | Island assembly reflects dispersal, establishment, interactions, extinction and evolution, and species traits can inform these processes. | The paper specifically established the present source-network decomposition. |
| Denelle et al. 2023 | Denelle, P., Weigelt, P. & Kreft, H. (2023). GIFT—An R package to access the Global Inventory of Floras and Traits. *Methods in Ecology and Evolution* 14:2738–2748. DOI 10.1111/2041-210X.14213. | Data/method citation for the GIFT plant lane. | The endpoint-available GIFT continuation is representative of all global island floras. |

## Novelty boundary supported by these references

Prior literature establishes all of the following:

- island isolation is multidimensional;
- stepping stones and generic network position can matter;
- nearby islands can act as sources and targets;
- source/species pools are fundamental to assembly;
- patch occurrence can be modelled with network structure;
- graph connectivity requires empirical validation.

The remaining question addressed here is narrower:

> Does the **topology of the focal species' realized, training-only occupied insular source network** retain held-out occurrence information after target environment, island area, current and historical external isolation, generic island-network context, global occupancy breadth, species × regional prevalence, nearest occupied-source distance, and diffuse occupied-source pressure are already represented?

The manuscript must present that conditional incremental question—not graphs, connectivity, source pools, or multidimensional isolation themselves—as the conceptual advance.
