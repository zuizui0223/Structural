# CamTrapAsia survey intake: public Zenodo source identity v1.236

Mendes et al. 2024 *Ecology*, DOI 10.1002/ecy.4299, presents 239 camera-trap studies with 876,606 trap nights and 278,260 independent capture events, 371 vertebrate taxa including 232 mammals, across tropical Asia (Indonesia, Singapore, Malaysia plus mainland countries). The study is an alternative *real field observation* dataset that may contain multiple marine-island sites. However, "studies", "camera stations" and "islands" have different grains; not all 239 sites are islands and some are from continental areas. Direct original 529-species validation is NOT established.

This one-shot v1.236 queries ONLY official Zenodo public **record metadata** at https://zenodo.org/api/records/10780971. It matches the immutable record DOI/id and exact published checksums for metadata, species-traits and capture source files. It never downloads those files, even CSV headers, and never reads capture records or any source species-by-island response.

If the published record provides confirmed metadata, the next **separate** gate may open only CSV field headers to establish whether site coordinates, study effort and taxon name columns are available. If no source coordinates or no archived 529 taxon overlap, stop before capture rows. A positive camera record can be a supported local detection, while undetected species need compatible deployment effort and detection modeling. An island camera dataset alone does not measure island-to-island dispersal or population rescue.

Geographic prescreen v1.235 is prior: frozen global heldout islands and blocks, no new IUCN responses. Previously closed Hébert/ALA/BALA sources are not retries. GEB scientific HOLD and eBird-off remain.
