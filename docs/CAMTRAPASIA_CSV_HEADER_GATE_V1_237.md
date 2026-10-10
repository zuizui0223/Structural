# v1.237 CamTrapAsia site-and-taxon file schema only

The official public Zenodo API for record 10780971 was validated in source-only v1.236 (GitHub run 37888405085): exact checksums and sizes of the camera metadata CSV (245677 bytes), species-traits CSV (67450 bytes), and captures CSV (956340 bytes), without downloading or opening any body rows.

v1.237 is a separately frozen source-file byte identity check, allowed to fetch ONLY the site metadata and species traits files, not captures. Before decoding even CSV first lines, it checks full file size and MD5 against the exact v1.236 public record metadata. It then returns only the CSV field headers from the first line. No latitude, longitude, study ID, actual taxon name, detection count or species-by-island record is read as structured information. CSV payloads are never retained.

Depending on the returned field structure, a subsequent independently versioned source study site-geography and taxonomic name header-gated reader may be created; source species capture events may only be opened under a valid confirmed island-sample frame, clear site survey effort, exact original 529-name taxonomic mapping, native status, and matched original 4126 heldout islands. Camera trap deployments are not themselves sampled islands or migration trajectories. GEB scientific HOLD and prior closed source lanes remain unchanged.
