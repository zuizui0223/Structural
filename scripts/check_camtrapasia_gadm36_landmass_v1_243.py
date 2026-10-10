#!/usr/bin/env python3
"""15 site/heldout centroid physical polygon relation under pinned GADM3.6 adm0 GeoJSON."""
import argparse,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlsplit
import shapely.geometry as sg
from shapely.strtree import STRtree

PIN="4e73ae720b9250f0974e8a93f949aaeab6989159"
SOURCE={
 "Indonesia":("IDN",714643,"7fe728548987171b36f19657da2df253853c99c6"),
 "Malaysia":("MYS",4997549,"d53bd009c0094c98ee4c530cbfca584196010394"),
 "Vietnam":("VNM",1157736,"d5a56b71d57fd99bb70c49b521b70b320635260c")
}
def public_polygon_source(country):
    iso,length,digest=SOURCE[country]
    url=f"https://raw.githubusercontent.com/stephanietuerk/admin-boundaries/{PIN}/hi-res/Admin0/gadm36_{iso}_0.json"
    with urlopen(Request(url,headers={"User-Agent":"Structural-response-safe-polygon-v1.243"}),timeout=75) as r:
        p=urlsplit(r.url)
        if p.scheme!="https" or p.hostname not in ("raw.githubusercontent.com","github.com"):
            raise ValueError("Untrusted GitHub geometry redirect")
        raw=r.read(length+1)
    if len(raw)!=length:raise ValueError("Pinned GADM36 GeoJSON length differs")
    blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()
    if blob!=digest:raise ValueError("Pinned GADM36 Git blob SHA mismatch")
    obj=json.loads(raw.decode("utf-8"))
    if obj.get("type")!="FeatureCollection" or len(obj.get("features",[]))!=1:
        raise ValueError("GADM36 admin0 source layer schema differs")
    g=sg.shape(obj["features"][0]["geometry"])
    if g.geom_type!="MultiPolygon":raise ValueError("Expected source country MultiPolygon")
    parts=list(g.geoms)
    if not parts or any(poly.is_empty for poly in parts):raise ValueError("Invalid source GADM geography")
    return parts,{"git_blob_sha1":blob,"pieces":len(parts),"bytes":len(raw)}
def classify(a,b,parts):
    t=STRtree(parts)
    def covered(p):
        point=sg.Point(*p)
        return [int(i) for i in t.query(point) if parts[int(i)].covers(point)]
    aa=covered(a);bb=covered(b)
    if len(aa)>1 or len(bb)>1:return "ambiguous"
    if not aa or not bb:return "one_or_both_outside"
    return "same_component" if aa[0]==bb[0] else "different_component"
def read_geo(path):
    import hashlib,csv
    expected="b60fbfd643b8a517d3a632a50db6b2b9916f9f3f34bae123ba7b7e89665b39e8"
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise ValueError("Original response-free georeference changed")
    with path.open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if not {"ID","Latitude_centroid","Longitude_centroid"}.issubset(reader.fieldnames or []):
            raise ValueError("Source geography columns missing")
        rows=list(reader)
    if len(rows)!=5592:raise ValueError("Original 5592 candidate island count differs")
    out={}
    for r in rows:
        def numeric(v):return float.fromhex(v) if "0x" in v.lower() else float(v)
        out[r["ID"]]=(numeric(r["Longitude_centroid"]),numeric(r["Latitude_centroid"]))
    return out
def analyze(candidates,coords):
    if candidates.get("status")!="PASS_FROZEN_15_CENTROID_NEAR_CANDIDATES_METADATA_ONLY":
        raise ValueError("Input does not match source-lock v1.241")
    sites=candidates.get("candidate_site_metadata")
    if len(sites)!=15 or len({x["nearest_original_heldout_island_ID"] for x in sites})!=10:
        raise ValueError("Earlier candidate identities changed")
    sources={c:public_polygon_source(c) for c in SOURCE}
    records=[]
    for site in sites:
        if not 0<=site["distance_km"]<25:raise ValueError("Pre-selected distance gate changed")
        name=site["country"]
        parts,meta=sources[name]
        result=classify((site["X_long"],site["Y_lat"]),
                        coords[site["nearest_original_heldout_island_ID"]],parts)
        records.append({"survey_id":site["survey_id"],"country":name,"landscape":site["landscape"],
            "nearest_original_heldout_id":site["nearest_original_heldout_island_ID"],
            "distance_km":site["distance_km"],"physical_component":result})
    counts=Counter(x["physical_component"] for x in records)
    country_counts={c:dict(Counter(x["physical_component"] for x in records if x["country"]==c)) for c in SOURCE}
    return {"schema":"structural.camtrapasia_gadm36_country_landmass_result.v1_243",
        "status":"PASS_PINNED_GADM36_COUNTRY_POLYGON_COMPONENT_SCREEN",
        "original_GADM_version":3.6,
        "country_sources":{c:meta for c,(part,meta) in sources.items()},
        "source_sites":15,"class_counts":dict(counts),"class_counts_by_country":country_counts,
        "candidate_site_records":records,
        "one_same_component_is_not_one_independent_archipelago":True,
        "original_mammal_island_polygon_id_canonical_crosswalk_verified":False,
        "original_mammal_heldout_labels_read":0,"field_capture_data_read":0,
        "model_predictions_opened":0}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("candidates",type=Path);p.add_argument("original",type=Path)
    p.add_argument("--out",type=Path,required=True);a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True)
    stage="candidate_source_identity"
    try:
        data=json.loads(a.candidates.read_text());coords=read_geo(a.original)
        stage="pinned_GADM3_6_country_boundaries"
        out=analyze(data,coords)
    except Exception as e:
        out={"schema":"structural.camtrapasia_gadm36_country_landmass_result.v1_243",
             "status":"STOP_GADM36_GEOGRAPHIC_IDENTITY_OR_SCHEMA","failure_stage":stage,
             "reason_class":type(e).__name__,"safe_reason":str(e)[:180],
             "original_mammal_heldout_labels_read":0,"field_capture_data_read":0}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    if out["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
