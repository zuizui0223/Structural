# Global mammal Weigelt safe-column firewall v0.59

## Status

The pristine 5,592-island mammal response remains unopened.

A public Figshare/UvA mirror of the Weigelt et al. 2013 global island table has now been physically verified and schema-audited without opening any island row value.

The `islanddata` layer contains **17,883 islands** and is a WGS84 point layer.

## Safe columns frozen before row access

The only islanddata values that may be opened in the next step are:

- `id`
- `countryiso`
- `country`
- `archip`
- `island`
- `gazetteer`
- `name_id`
- `name_long`
- `name_lat`
- `no_names`
- `name_dist`
- `name_meth`
- `name_alt`
- `area`
- `dist`
- `slmp`
- `gmmc`
- `elev`
- `temp`
- `vart`
- `ccvt`
- `prec`
- `varp`

These are the response-independent ID/name/geography/climate fields needed to build a v0.55 island reference and to test the routing-ID crosswalk.

## Explicitly forbidden

The following are excluded before values are opened:

- geometry blob `geom`;
- all `sr*` richness/model columns;
- all `pam*` and `upgma*` derived columns;
- all `pca*` ordination columns;
- `buffer` and `modeled_t`.

They are not needed for the mammal reference and cannot be introduced later as opportunistic predictors.

## Key ecological fields

The schema confirms the exact response-independent variables required for the dual-isolation programme:

- `area` — island area;
- `dist` — mainland-distance variable;
- `slmp` — current isolation / surrounding-landmass variable;
- `gmmc` — past mainland-connection state;
- `name_long`, `name_lat` — coordinates;
- `archip` — archipelago;
- `temp`, `vart`, `prec`, `varp`, `elev`, `ccvt` — environmental reference.

## Next gate

A single response-independent extraction may now read only these safe columns and produce a compact, SHA-pinned island table.

After that, the mammal matrix itself may be opened only at the routing-metadata level to recover its island identifier column. Species 0/1 cells must remain byte-sealed.

If `id_spatial_island` does not match Weigelt `id` exactly or through a prospectively frozen response-independent crosswalk, the system remains HOLD rather than using outcome-informed matching.
