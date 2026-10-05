#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics,zipfile
from collections import defaultdict,deque
from pathlib import Path

from scripts.audit_bala_event_core_v1_128 import parse_meta,parse_event_core,read_member,year_from,norm

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_geometry_operator_contract_v1_136.json"
DEFAULT_CORE=ROOT/"development/bala_official_core_code_audit_contract_v1_131.json"
class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def hav(lat1,lon1,lat2,lon2):
    r=6371.0088
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1);dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1.0,math.sqrt(a)))

def phase_for_year(y,windows):
    hits=[p for p,(lo,hi) in windows.items() if y is not None and lo<=y<=hi]
    return hits[0] if len(hits)==1 else None

def lineage(code):
    return "FAI-NFCF-REPLACED-LINEAGE" if code in {"FAI-NFCF-T-11","FAI-NFCF-TB26"} else code

def code_allowed(code,phase,official):
    unchanged=set(official["official_core_codes"]["unchanged_29"])
    if code in unchanged:return True
    return (
      (code==official["official_core_codes"]["BALA1_replaced_site_code"] and phase=="BALA1") or
      (code==official["official_core_codes"]["BALA2_BALA3_replacement_site_code"] and phase in {"BALA2","BALA3"})
    )

def project(points):
    mean_lat=math.radians(statistics.mean(v["latitude"] for v in points.values()))
    r=6371.0088
    out={}
    for k,v in points.items():
        out[k]=(r*math.cos(mean_lat)*math.radians(v["longitude"]),r*math.radians(v["latitude"]))
    return out

def gabriel_edges(points):
    xy=project(points);ids=sorted(points);edges=[]
    for aidx in range(len(ids)):
        for bidx in range(aidx+1,len(ids)):
            a,b=ids[aidx],ids[bidx]
            x1,y1=xy[a];x2,y2=xy[b]
            mx,my=(x1+x2)/2,(y1+y2)/2
            rad2=((x1-x2)**2+(y1-y2)**2)/4
            blocked=False
            for k in ids:
                if k in {a,b}:continue
                x,y=xy[k]
                if (x-mx)**2+(y-my)**2 < rad2-1e-9:
                    blocked=True;break
            if not blocked:
                d=hav(points[a]["latitude"],points[a]["longitude"],points[b]["latitude"],points[b]["longitude"])
                edges.append((a,b,d))
    return edges

def connected(ids,edges):
    adj=defaultdict(list)
    for a,b,_ in edges:adj[a].append(b);adj[b].append(a)
    seen={ids[0]};q=deque([ids[0]])
    while q:
        a=q.popleft()
        for b in adj[a]:
            if b not in seen:seen.add(b);q.append(b)
    return len(seen)==len(ids)

def write_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("archive",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--official-core",type=Path,default=DEFAULT_CORE)
    ap.add_argument("--geometry",type=Path,required=True)
    ap.add_argument("--edges",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text());official=json.loads(a.official_core.read_text())
        if c["schema"]!="structural.bala_geometry_operator_contract.v1_136":raise Stop("contract schema drift")
        if official["schema"]!="structural.bala_official_core_code_audit_contract.v1_131":raise Stop("core contract drift")
        if sha(a.archive)!=c["source"]["archive_sha256"]:raise Stop("archive SHA drift")
        with zipfile.ZipFile(a.archive) as z:
            meta_name=next((x.filename for x in z.infolist() if Path(x.filename).name.lower()=="meta.xml"),None)
            if not meta_name:raise Stop("meta.xml missing")
            core,_=parse_meta(read_member(z,meta_name))
            if core["location"]!=c["source"]["event_core_path"]:raise Stop("Event location drift")
            event_bytes=read_member(z,core["location"])
            if hashlib.sha256(event_bytes).hexdigest()!=c["source"]["event_core_sha256"]:raise Stop("Event SHA drift")
            rows,_=parse_event_core(event_bytes,core)

        windows={k:(int(v[0]),int(v[1])) for k,v in c["site_geometry"]["phase_windows"].items()}
        physical=defaultdict(list)
        for r in rows:
            y=year_from(r);phase=phase_for_year(y,windows);code=norm(r.get("locationID",""))
            if not phase or not code or not code_allowed(code,phase,official):continue
            try:lat=float(norm(r.get("decimalLatitude","")));lon=float(norm(r.get("decimalLongitude","")))
            except Exception:continue
            if not (-90<=lat<=90 and -180<=lon<=180):continue
            physical[code].append((lat,lon))
        expected=set(official["official_core_codes"]["unchanged_29"])|{
          official["official_core_codes"]["BALA1_replaced_site_code"],
          official["official_core_codes"]["BALA2_BALA3_replacement_site_code"]
        }
        if set(physical)!=expected:raise Stop(f"core coordinate support mismatch: missing={sorted(expected-set(physical))} extra={sorted(set(physical)-expected)}")
        physical_rep={k:(statistics.median(x[0] for x in vals),statistics.median(x[1] for x in vals)) for k,vals in physical.items()}
        bylin=defaultdict(list)
        for code,xy in physical_rep.items():bylin[lineage(code)].append(xy)
        if len(bylin)!=30:raise Stop("conceptual lineage count drift")
        linrep={k:(statistics.median(x[0] for x in vals),statistics.median(x[1] for x in vals)) for k,vals in bylin.items()}
        byisland=defaultdict(list)
        for lin,xy in linrep.items():byisland[lin[:3]].append(xy)
        if len(byisland)!=7:raise Stop("island count drift")
        islands={k:{"latitude":statistics.median(x[0] for x in vals),"longitude":statistics.median(x[1] for x in vals),"conceptual_lineages":len(vals)} for k,vals in byisland.items()}
        if sum(v["conceptual_lineages"] for v in islands.values())!=30:raise Stop("lineage allocation drift")
        edges=gabriel_edges(islands);ids=sorted(islands)
        if not edges or not connected(ids,edges):raise Stop("Gabriel graph not connected")
        lengths=[d for _,_,d in edges];lam=statistics.median(lengths)
        if not lam>0:raise Stop("invalid graph lambda")

        grows=[{"island":k,"latitude":repr(islands[k]["latitude"]),"longitude":repr(islands[k]["longitude"]),"conceptual_lineages":islands[k]["conceptual_lineages"]} for k in ids]
        erows=[{"from_island":x,"to_island":y,"haversine_km":repr(d)} for x,y,d in sorted(edges)]
        write_csv(a.geometry,grows,["island","latitude","longitude","conceptual_lineages"])
        write_csv(a.edges,erows,["from_island","to_island","haversine_km"])
        result={
          "schema":"structural.bala_geometry_operator_result.v1_136",
          "status":"BALA_RESPONSE_INDEPENDENT_GABRIEL_GRAPH_FROZEN",
          "islands":len(ids),"conceptual_lineages":len(linrep),"physical_site_codes":len(physical_rep),
          "island_codes":ids,"graph_edges":len(edges),"graph_connected":True,
          "edge_length_km_min":min(lengths),"edge_length_km_median":lam,"edge_length_km_max":max(lengths),
          "kernel_lambda_km":lam,
          "geometry_sha256":sha(a.geometry),"edges_sha256":sha(a.edges),
          "occurrence_extension_semantically_opened":False,"taxon_tokens_opened":0,
          "taxon_occurrence_values_opened":0,"source_loss_effects_computed":0,
          "pilot_occurrence_access_authorized":False,"confirmatory_occurrence_access_authorized":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,zipfile.BadZipFile,Stop) as e:
        result={"schema":"structural.bala_geometry_operator_result.v1_136","status":"STOP","reason":str(e),
          "occurrence_extension_semantically_opened":False,"taxon_occurrence_values_opened":0,"source_loss_effects_computed":0};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True);a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
