#!/usr/bin/env python3
"""One-shot geometry-only crosswalk: ALA Australian island polygons to frozen mammal heldout IDs.

NEVER load ALA mammal point/occurrence shapefiles or any original species response.
Inputs: the ABS-derived corrected island polygon geometry ZIP, original safe island
covariates and original heldout-island routing only. No taxon/label data are used.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,zipfile
from collections import Counter
from pathlib import Path

class GateStop(ValueError):
    pass

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def git_blob_sha1(data):
    h=hashlib.sha1()
    h.update(b"blob "+str(len(data)).encode("ascii")+b"\0")
    h.update(data)
    return h.hexdigest()

def valid_float(value,name):
    try:
        raw=str(value).strip()
        f=float.fromhex(raw) if raw.lower().startswith(("0x","+0x","-0x")) else float(raw)
    except (TypeError,ValueError) as exc: raise GateStop(f"invalid {name}") from exc
    if not math.isfinite(f):raise GateStop(f"nonfinite {name}")
    return f

def source_polygons(blob,contract):
    import shapefile
    from pyproj import CRS
    from shapely.geometry import shape as to_geom
    if len(blob)!=contract["source"]["geometry_zip_size_bytes"]:
        raise GateStop("Australian geometry ZIP size drift")
    if git_blob_sha1(blob)!=contract["source"]["geometry_blob_sha1"]:
        raise GateStop("Australian geometry Git blob fingerprint drift")
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        if archive.testzip() is not None:raise GateStop("ZIP integrity failed")
        names=archive.namelist()
        shp=[n for n in names if n.lower().endswith(".shp")]
        if len(shp)!=1:raise GateStop(f"expected exactly one polygon shapefile, got {len(shp)}")
        stem=shp[0][:-4]
        bylower={n.lower():n for n in names}
        parts={}
        for ext in (".shp",".shx",".dbf",".prj"):
            key=(stem+ext).lower()
            if key not in bylower:raise GateStop(f"missing island geometry component {ext}")
            parts[ext]=archive.read(bylower[key])
    crs=CRS.from_wkt(parts[".prj"].decode("utf-8-sig"))
    if not crs.is_projected or not crs.axis_info or abs(crs.axis_info[0].unit_conversion_factor-1)>0.001:
        raise GateStop("source polygon CRS not metres in projected coordinate system")
    with shapefile.Reader(shp=io.BytesIO(parts[".shp"]),
                          shx=io.BytesIO(parts[".shx"]),
                          dbf=io.BytesIO(parts[".dbf"])) as rdr:
        fields=[n for n,*_ in rdr.fields if n!="DeletionFlag"]
        allowed=contract["geometry_gate"]["source_polygon_id_fields_allowed"]
        field=next((n for n in allowed if n in fields),None)
        if not field:raise GateStop("source island FID field absent")
        shapes=[];fids=[]
        for record in rdr.iterShapeRecords():
            value=record.record.as_dict().get(field)
            if value is None:raise GateStop("missing ALA FID")
            fid=str(value).strip()
            if not fid:raise GateStop("blank ALA FID")
            geom=to_geom(record.shape.__geo_interface__)
            if not geom.is_valid:geom=geom.buffer(0)
            if geom.is_empty or geom.geom_type not in ("Polygon","MultiPolygon"):
                raise GateStop("invalid/nonpolygon Australian island geometry")
            if not geom.area>0:raise GateStop("zero island polygon area")
            shapes.append(geom);fids.append(fid)
        if len(fids)!=len(set(fids)):raise GateStop("source polygon duplicate FID")
    if not shapes:raise GateStop("no source island geometry")
    return shapes,fids,crs,fields

def select_match(point,source_area_km2,tree,polygons,fids,lo,hi):
    """Return (FID, area ratio, reason). Ambiguous source spatial membership is excluded."""
    ix=tree.query(point)
    inside=[int(i) for i in ix if polygons[int(i)].covers(point)]
    if not inside:return (None,None,"outside")
    if len(inside)>1:return (None,None,"ambiguous_geometry")
    i=inside[0]
    ratio=float(polygons[i].area/1e6/source_area_km2)
    if not lo<=ratio<=hi:return (None,ratio,"area_mismatch")
    return (fids[i],ratio,"candidate")

def evaluate(original_path,heldout_path,geometry_zip_path,contract):
    from pyproj import Transformer
    from shapely.geometry import Point
    from shapely.strtree import STRtree

    if contract.get("schema")!="structural.external_ala_mammal_island_geometry_gate.v1_191":
        raise GateStop("contract schema mismatch")
    if contract["source"]["response_mammals_zip_must_not_be_downloaded"] is not True:
        raise GateStop("mammal response transport not blocked")
    if original_path.name!=contract["original"]["appendix2_safe_file"] or sha256(original_path)!=contract["original"]["appendix2_safe_sha256"]:
        raise GateStop("original safe appendix2 fingerprint drift")
    if heldout_path.name!=contract["original"]["heldout_ids_file"] or sha256(heldout_path)!=contract["original"]["heldout_ids_sha256"]:
        raise GateStop("original heldout routing fingerprint drift")
    if geometry_zip_path.name!="ausislandsAlbersGeom_corrected.zip":
        raise GateStop("unexpected external input (only geometry archive authorized)")
    rows=list(csv.DictReader(original_path.open("r",encoding="utf-8-sig",newline="")))
    held=list(csv.DictReader(heldout_path.open("r",encoding="utf-8-sig",newline="")))
    if len(held)!=contract["original"]["frozen_heldout_islands"] or any("ID" not in r for r in held):
        raise GateStop("heldout population drift")
    orig={r["ID"]:r for r in rows}
    if len(orig)!=len(rows):raise GateStop("duplicate original safe ID")
    heldids=[r["ID"] for r in held]
    if len(set(heldids))!=len(heldids) or not set(heldids).issubset(orig):
        raise GateStop("frozen heldout ID not found in safe island metadata")

    blob=geometry_zip_path.read_bytes()
    polygons,fids,crs,source_fields=source_polygons(blob,contract)
    tr=Transformer.from_crs("EPSG:4326",crs,always_xy=True)
    tree=STRtree(polygons)
    area_rule=contract["geometry_gate"]
    outcomes=Counter()
    candidates=[]
    for id_ in heldids:
        row=orig[id_]
        lat=valid_float(row["Latitude_centroid"],"Latitude_centroid")
        lon=valid_float(row["Longitude_centroid"],"Longitude_centroid")
        area=valid_float(row["Area"],"original island area")
        if not (0<area and -90<=lat<=90 and -180<=lon<=180):
            raise GateStop("invalid original area or centroid")
        x,y=tr.transform(lon,lat)
        fid,ratio,reason=select_match(Point(x,y),area,tree,polygons,fids,
            area_rule["area_ratio_min"],area_rule["area_ratio_max"])
        outcomes[reason]+=1
        if reason=="candidate":
            candidates.append({"ID":id_,"ALA_FID":fid,"polygon_to_original_area_ratio":ratio})
    id_frequency=Counter(row["ALA_FID"] for row in candidates)
    exact=[row for row in candidates if id_frequency[row["ALA_FID"]]==1]
    outcomes["multi_original_to_one_ala_excluded"]=len(candidates)-len(exact)
    exact=sorted(exact,key=lambda r:r["ID"])
    threshold=area_rule["min_exact_one_to_one_heldout_islands"]
    status=(contract["success_status"] if len(exact)>=threshold else contract["stop_status"])
    receipt={
        "schema":"structural.external_ala_mammal_island_geometry_result.v1_191",
        "status":status,
        "source_repository":contract["source"]["repository"],
        "source_commit":contract["source"]["source_commit"],
        "geometry_git_blob_sha1":contract["source"]["geometry_blob_sha1"],
        "geometry_file_sha256":hashlib.sha256(blob).hexdigest(),
        "original_safe_sha256":sha256(original_path),
        "heldout_routing_sha256":sha256(heldout_path),
        "source_polygon_count":len(polygons),
        "source_fid_field_present":True,
        "source_field_names":source_fields,
        "heldout_islands":len(heldids),
        "reason_counts":dict(outcomes),
        "exact_one_to_one_heldout_matches":len(exact),
        "required_matches":threshold,
        "area_ratio_range":[area_rule["area_ratio_min"],area_rule["area_ratio_max"]],
        "external_ala_mammal_occurrence_values_opened":0,
        "external_ala_mammal_zip_downloaded":False,
        "original_heldout_occurrence_values_opened":0,
        "taxon_gate_passed":False,
        "biological_scoring_authorized":False,
        "eBird_used":False
    }
    return exact,receipt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("safe_appendix2",type=Path)
    ap.add_argument("heldout_ids",type=Path)
    ap.add_argument("external_geometry_zip",type=Path)
    ap.add_argument("--contract",type=Path,default=Path("development/global_mammals_ala_island_geometry_gate_v1_191.json"))
    ap.add_argument("--crosswalk",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        contract=json.loads(a.contract.read_text())
        rows,receipt=evaluate(a.safe_appendix2,a.heldout_ids,a.external_geometry_zip,contract)
        if rows:
            a.crosswalk.parent.mkdir(parents=True,exist_ok=True)
            with a.crosswalk.open("w",newline="",encoding="utf-8") as h:
                w=csv.DictWriter(h,fieldnames=["ID","ALA_FID","polygon_to_original_area_ratio"],lineterminator="\n")
                w.writeheader();w.writerows(rows)
            receipt["crosswalk_sha256"]=sha256(a.crosswalk)
        code=0 if receipt["status"]==contract["success_status"] else 2
    except (GateStop,ValueError,OSError,RuntimeError,KeyError,json.JSONDecodeError,zipfile.BadZipFile) as e:
        code=2
        receipt={"schema":"structural.external_ala_mammal_island_geometry_result.v1_191",
                 "status":"STOP_ALA_GEOMETRY_PREACCESS_SCHEMA",
                 "reason":str(e),"external_ala_mammal_occurrence_values_opened":0,
                 "external_ala_mammal_zip_downloaded":False,
                 "original_heldout_occurrence_values_opened":0,
                 "biological_scoring_authorized":False,"eBird_used":False}
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())
