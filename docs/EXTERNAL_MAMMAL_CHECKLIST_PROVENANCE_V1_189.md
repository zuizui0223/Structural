# Independent mammal checklist: frozen provenance gate v1.189

This is a **pre-outcome design**, not an empirical ecological result. The Hébert et al. Dryad nine-island-group dataset combines published checklists, atlases and island-specific literature. Its 0/1 matrix must not be opened until species/header support, island crosswalk and source independence are established.

The dataset README explicitly lists IUCN (2016) among **California Gulf** sources. Therefore California Gulf is excluded from any primary claim of independence from the original Barreto IUCN (2017)-derived polygon map.

The two Mediterranean groups cite Vigne (1992) zooarchaeology. They are held from a present-day occupancy primary until the source period can be separated independently for focal species. The other six groups are provisional literature-primary pools only; those matrices are still nonuniform literature compilations, not complete unbiased field detections. IUCN can also have been used globally for introduced-species screening.

v1.189 simply classifies the **metadata-only v1.188** group and taxon-header support. It must not load, count or infer binary occurrence values. It retains thresholds of >=20 exact focal taxa, >=3 qualifying groups and >=30 named islands **after excluding** direct IUCN and mixed historical groups. Failure causes STOP; success only enables an additional authoritative island-name → original island-ID gazetteer gate, **not** response scoring.

Without an exact crosswalk to the original 4,126 heldout island IDs and clear species-level provenance, the 204-island compilation cannot independently score the frozen C/R3 predictions. Likewise even future successful independent checklist scoring would be *post-hoc independent-source validation*, not a prospectively selected new species system.
