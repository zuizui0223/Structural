#!/usr/bin/env python3
"""Site-only CamTrapAsia geography compared with frozen 4,126 heldout 10deg tiles."""
import argparse,csv,hashlib,io,json,math
from collections import defaultdict
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from index_original_mammal_heldout_geography_v1_235 import tile

URL="https://zenodo.org/api/records/10780971/files/CamTrapAsia_Metadata_20231031.csv/content"
SOURCE_SIZE=245677
SOURCE_MD5="2b50c534737b0c98a93da54128b10a32"
HOSTS={"zenodo.org","www.zenodo.org","files.zenodo.org","s3.cern.ch"}
ALLOWED={"survey_id","country","landscape","site","effort","Y_lat","X_long","year_start","year_end"}
def get_source():
    with urlopen(Request(URL,headers={"User-Agent":"Structural-site-geography-only-v1.239"}),timeout=45) as r:
        p=urlsplit(r.url)
        if p.scheme!="https" or p.hostname not in HOSTS:
            raise ValueError("Untrusted public source redirect")
        raw=r.read(SOURCE_SIZE+1)
    if len(raw)!=SOURCE_SIZE or hashlib.md5(raw).hexdigest()!=SOURCE_MD5:
        raise ValueError("Source survey metadata failed frozen byte identity")
    return raw

def source_sites(raw):
    if len(raw)!=SOURCE_SIZE or hashlib.md5(raw).hexdigest()!=SOURCE_MD5:
        raise ValueError("Source site list SHA/size mismatch")
    sites=[]
    with io.StringIO(raw.decode("utf-8-sig")) as fp:
        reader=csv.DictReader(fp)
        if not ALLOWED.issubset(reader.fieldnames or []):
            raise ValueError("Site metadata schema changed")
        for row in reader:
            r={field:row[field] for field in ALLOWED} # disallowed species/detection fields NEVER accessed.
            study=(r["survey_id"] or "").strip()
            if not study:raise ValueError("Blank survey id")
            try:
                lat=float(r["Y_lat"]);lon=float(r["X_long"])
                coordinate_valid=math.isfinite(lat) and math.isfinite(lon) and -90<=lat<=90 and -180<=lon<=180
            except (TypeError,ValueError):
                coordinate_valid=False;lat=lon=None
            effort_ok=False
            try:
                effort=float(r["effort"])
                effort_ok=math.isfinite(effort) and effort>=0
            except (TypeError,ValueError):
                pass
            sites.append({"survey_id":study,"lat":lat,"lon":lon,"coordinates_valid":coordinate_valid,
                          "effort_present":effort_ok})
    if not 1<=len(sites)<=2000:raise ValueError("Unexpected number of source survey rows")
    return sites

def validated_grid(source):
    if source.get("schema")!="structural.global_mammal_heldout_geographic_search_index_result.v1_235":
        raise ValueError("Wrong original sealed map index schema")
    if (source.get("original_heldout_islands"),source.get("original_selected_model_islands"),
        source.get("global_distinct_heldout_blocks"))!=(4126,5401,168):
        raise ValueError("Original heldout geography changed")
    if source.get("status")!="PASS_GEOGRAPHY_ONLY_INDEPENDENT_SURVEY_SEARCH_INDEX":
        raise ValueError("Original heldout tile index not a PASS")
    frames={}
    for label in ("primary","shifted"):
        records=source.get(label+"_all_nonempty_tiles")
        if not isinstance(records,list):raise ValueError("Missing original tiles")
        if sum(z["heldout_islands"] for z in records)!=4126:
            raise ValueError("Focal heldout population not accounted for")
        frame={(z["lat_min"],z["lon_min"]):z for z in records}
        if len(frame)!=len(records):raise ValueError("Duplicate heldout grid cell")
        frames[label]=frame
    return frames
def analyze(sites,source):
    frames=validated_grid(source)
    valid=[s for s in sites if s["coordinates_valid"]]
    survey_ids={x["survey_id"] for x in sites}
    summaries={}
    for label,shift in (("primary",0),("shifted",5)):
        by_tile=defaultdict(lambda:{"rows":0,"studies":set()})
        for x in valid:
            lat,lon=tile(x["lat"],x["lon"],shift)
            key=(lat[0],lon[0]);by_tile[key]["rows"]+=1;by_tile[key]["studies"].add(x["survey_id"])
        overlapping=[]
        for key,site in by_tile.items():
            geo=frames[label].get(key)
            if geo is None:continue
            overlapping.append({
                "latitude_min":key[0],"longitude_min":key[1],
                "camera_metadata_rows":site["rows"],"distinct_survey_ids":len(site["studies"]),
                "original_heldout_centroid_count_same_tile":geo["heldout_islands"],
                "original_heldout_blocks_same_tile":geo["distinct_heldout_blocks"]
            })
        overlapping.sort(key=lambda z:(-z["original_heldout_blocks_same_tile"],
            -z["distinct_survey_ids"],-z["original_heldout_centroid_count_same_tile"],
            z["latitude_min"],z["longitude_min"]))
        summaries[label]={
            "source_study_center_tiles_with_original_heldout_centroids":len(overlapping),
            "source_survey_ids_in_coincident_tiles":len({
                x["survey_id"] for x in valid
                if (lambda key:key in frames[label])((lambda t:(t[0][0],t[1][0]))(
                    tile(x["lat"],x["lon"],shift)))}),
            "overlap_tiles_with_at_least_two_original_heldout_blocks":
                sum(z["original_heldout_blocks_same_tile"]>=2 for z in overlapping),
            "top20_geographic_coincidence_tiles":overlapping[:20],
            "all_geographic_coincidence_tiles":overlapping
        }
    return {
      "schema":"structural.camtrapasia_site_only_heldout_geogrid_result.v1_239",
      "status":"PASS_CANDIDATE_CAMERA_STUDY_LOCATIONS_VS_ORIGINAL_HELDOUT_GRID",
      "source_metadata_row_count":len(sites),
      "source_distinct_survey_ids":len(survey_ids),
      "source_with_valid_WGS84_centroid":len(valid),
      "source_with_valid_effort_field":sum(z["effort_present"] for z in sites),
      "primary":summaries["primary"],"shifted":summaries["shifted"],
      "island_polygon_or_site_identity_verified":False,
      "all_sites_are_oceanic_islands":False,
      "species_detection_values_read":0,
      "original_IUCN_heldout_responses_read":0,
      "original_predictions_read":0,
      "external_predictive_validation_admitted":False
    }

def main():
    p=argparse.ArgumentParser();p.add_argument("frozen_grid",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=analyze(source_sites(get_source()),json.loads(a.frozen_grid.read_text(encoding="utf-8")))
    except HTTPError as e:
        result={"status":"STOP_SOURCE_HTTP","http_status":e.code}
    except Exception as e:
        result={"status":"STOP_SITE_GEO_SOURCE_OR_GRID_SCHEMA","reason_class":type(e).__name__}
    result.setdefault("schema","structural.camtrapasia_site_only_heldout_geogrid_result.v1_239")
    result.setdefault("species_detection_values_read",0)
    result.setdefault("original_IUCN_heldout_responses_read",0)
    result.setdefault("external_predictive_validation_admitted",False)
    a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    msg={k:v for k,v in result.items() if k not in ("primary","shifted")}
    for key in ("primary","shifted"):
        if key in result:
            msg[key]={k:v for k,v in result[key].items() if k!="all_geographic_coincidence_tiles"}
    print(json.dumps(msg,sort_keys=True))
    if result["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
