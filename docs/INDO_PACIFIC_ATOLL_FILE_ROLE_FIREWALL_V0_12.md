# Indo-Pacific atoll file-role firewall v0.12

## Status

The exact Zenodo archive was inventoried content-blind before any semantic parsing.

Frozen source archive:

- Zenodo record: 18848127
- file: `Steibl_2026_Indo_Pacific_Atolls_Dataset.zip`
- compressed bytes: 1,525,818
- MD5: `3b314df61fd1ae889bab2a545f801a78`
- SHA-256: `1f95097bb88caf2eaf3ad8f49d6afb87beab9a747af08d24cfff4903c231444e`

The v0.11 inventory contains 25 members and records zero semantic parses, zero response parses and zero model fits.

## Conservative role policy

All taxon-by-atoll biodiversity and seabird population tables are classified as **response**, including their `*_refs.csv` companions. They remain semantically closed even when they are not the focal vascular-plant response.

`notebook.ipynb` is **code** and remains closed.

`atoll_shapefiles.kml` is **safe_schema** because geometry is response-independent and is required only for spatial identity/geometry checks.

Response-independent atoll descriptor tables are classified as **metadata**.

No file is classified as unknown or mixed.

## Why non-focal biodiversity remains closed

Opening birds, reptiles, arthropods, land crabs, mammals or seabird abundance could expose ecological outcomes that might influence later design choices. They are therefore treated exactly like the focal plant response for the pre-response phase.

The source-pool-handoff plant design may not borrow candidate selection, graph scales, thresholds or covariates from those outcomes.

## Next semantic-open subset

A v0.12 pass does not authorize opening every metadata file merely because it is safe.

The next audit should open only the minimum files needed to construct the frozen plant design:

- `atoll_main_310.csv`;
- `atoll_biogeography.csv`;
- `atoll_environmental.csv`;
- `atoll_shapefiles.kml`;
- `fair2.json` only for data-dictionary/schema provenance.

Military use, human population, reefscape and oceanographic tables remain unused unless a new response-blind protocol explicitly justifies them before plant response access.

## Evidence boundary

At v0.12:

- plant response values opened: no;
- any biodiversity response values opened: no;
- original notebook opened: no;
- model fits: zero;
- empirical evidence contribution: zero.

The next valid operation is a minimal safe-metadata/schema audit only.
