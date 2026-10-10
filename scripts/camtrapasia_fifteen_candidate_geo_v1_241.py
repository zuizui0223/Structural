#!/usr/bin/env python3
"""Original frozen 15 candidate camera-site geography rows only; no species observations."""
import argparse,csv,io,json,math
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from camtrapasia_sites_vs_mammal_heldout_grid_v1_239 import get_source
from camtrapasia_nearest_heldout_centroid_v1_240 import load_heldout,xyz,hav,num

SAFE_FIELDS={"survey_id","country","landscape","site","Y_lat","X_long","effort"}
def inspect(source,geom,held):
    ids,coords=load_heldout(geom,held)
    with io.StringIO(source.decode("utf-8-sig")) as fp:
        rd=csv.DictReader(fp)
        if not SAFE_FIELDS.issubset(rd.fieldnames or []):raise ValueError("New site schema")
        rows=[{k:r[k] for k in SAFE_FIELDS} for r in rd]
    if len(rows)!=239:raise ValueError("Source camera survey count changed")
    keys=list(coords);pts=np.array([xyz(*coords[k]) for k in keys])
    tree=cKDTree(pts)
    output=[]
    for r in rows:
        lat=float(r["Y_lat"]);lon=float(r["X_long"])
        if not(math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180):
            raise ValueError("Source site WGS84 coordinates changed")
        _,ind=tree.query(xyz(lat,lon))
        found=keys[int(ind)]
        dist=hav((lat,lon),coords[found])
        if dist>=25:continue
        output.append({"survey_id":r["survey_id"],"country":r["country"],
            "landscape":r["landscape"],"site":r["site"],
            "Y_lat":lat,"X_long":lon,
            "nearest_original_heldout_island_ID":found,
            "nearest_heldout_block_id":ids[found],
            "distance_km":dist})
    if len(output)!=15 or len({r["nearest_original_heldout_island_ID"] for r in output})!=10 or len({r["nearest_heldout_block_id"] for r in output})!=7:
        raise ValueError("Frozen prior v1.240 candidate set not reproduced")
    output.sort(key=lambda x:(x["distance_km"],x["survey_id"]))
    countries=sorted({r["country"] for r in output})
    return {"schema":"structural.camtrapasia_fifteen_candidate_geography.v1_241",
        "status":"PASS_FROZEN_15_CENTROID_NEAR_CANDIDATES_METADATA_ONLY",
        "sites_total":239,"candidates_below_25km":len(output),
        "unique_original_heldout_nearest_islands":10,"unique_original_heldout_blocks":7,
        "candidate_countries":countries,
        "candidate_site_metadata":output,
        "these_are_not_verified_same_island_stations":True,
        "source_capture_rows_read":0,"original_species_response_rows_read":0,
        "original_model_predictions_read":0,"physical_GADM_land_polygon_checked":False}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("original",type=Path);p.add_argument("heldout",type=Path)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    try:res=inspect(get_source(),a.original,a.heldout)
    except Exception as e:res={"schema":"structural.camtrapasia_fifteen_candidate_geography.v1_241",
         "status":"STOP_SITE_GEOGRAPHIC_IDENTITY_OR_FROZEN_COUNT",
         "reason_type":type(e).__name__,
         "source_capture_rows_read":0,"original_species_response_rows_read":0}
    a.out.write_text(json.dumps(res,indent=2,sort_keys=True)+"\n")
    print(json.dumps(res,sort_keys=True))
    if res["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
