#!/usr/bin/env python3
"""Freeze the pristine GIFT plant spatial split and response-independent R0-R2 reference."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,statistics
from collections import defaultdict,deque
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/gift_spatial_reference_contract_v1_46.json"
class Stop(RuntimeError): pass

def file_sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

def fnum(x,label):
    try: v=float(str(x).strip())
    except Exception as exc: raise Stop(f"invalid numeric {label}") from exc
    if not math.isfinite(v): raise Stop(f"nonfinite numeric {label}")
    return v

def hav(lat1,lon1,lat2,lon2):
    r=6371.0088
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1.0,math.sqrt(a)))

def circular_mean_longitude(values):
    s=math.fsum(math.sin(math.radians(v)) for v in values)/len(values)
    c=math.fsum(math.cos(math.radians(v)) for v in values)/len(values)
    if math.hypot(s,c)<1e-12: raise Stop("archipelago longitude circular mean undefined")
    return math.degrees(math.atan2(s,c))

def pool_key(lat,lon,width):
    lat_i=min(int(180/width)-1,max(0,int(math.floor((lat+90.0)/width))))
    lon_i=int(math.floor(((lon+180.0)%360.0)/width))
    return f"RP{width:02d}_lat{lat_i:02d}_lon{lon_i:02d}"

def hash_rank(salt,name):
    return hashlib.sha256(f"{salt}|{name}".encode("utf-8")).hexdigest()

def connected(n,edges):
    if n<=1:return True
    adj=[[] for _ in range(n)]
    for i,j,_ in edges: adj[i].append(j); adj[j].append(i)
    seen={0}; q=deque([0])
    while q:
        i=q.popleft()
        for j in adj[i]:
            if j not in seen: seen.add(j); q.append(j)
    return len(seen)==n

def sym_knn(points,k):
    alln=[]
    for i,(_,lat,lon) in enumerate(points):
        ds=[]
        for j,(_,lat2,lon2) in enumerate(points):
            if i==j: continue
            ds.append((hav(lat,lon,lat2,lon2),j))
        ds.sort(key=lambda x:(x[0],points[x[1]][0]))
        alln.append(ds[:k])
    edges={}
    for i,ns in enumerate(alln):
        for d,j in ns:
            a,b=sorted((i,j)); edges[(a,b)]=min(d,edges.get((a,b),d))
    return [(a,b,d) for (a,b),d in sorted(edges.items())]

def choose_graph(points):
    if len(points)<3: raise Stop("regional pool has fewer than 3 islands after freeze")
    for k in range(1,len(points)):
        es=sym_knn(points,k)
        if connected(len(points),es): return k,es
    raise Stop("regional pool graph failed to connect")

def zvals(values,label):
    mean=math.fsum(values)/len(values)
    var=math.fsum((x-mean)**2 for x in values)/len(values)
    sd=math.sqrt(var)
    if not sd>0: raise Stop(f"zero variance predictor: {label}")
    return [(x-mean)/sd for x in values],mean,sd

def load_inputs(geo_path,cross_path,contract):
    if file_sha(geo_path)!=contract["parents_fingerprints"]["gift_geography_sha256"]:
        raise Stop("GIFT geography SHA mismatch")
    if file_sha(cross_path)!=contract["parents_fingerprints"]["crosswalk_sha256"]:
        raise Stop("GIFT-Weigelt crosswalk SHA mismatch")
    with geo_path.open("r",encoding="utf-8",newline="") as h: geo=list(csv.DictReader(h))
    with cross_path.open("r",encoding="utf-8",newline="") as h: cross=list(csv.DictReader(h))
    gm={str(r["entity_ID"]):r for r in geo}
    if len(gm)!=len(geo): raise Stop("duplicate GIFT geography entity_ID")
    if len(cross)!=548: raise Stop("strict crosswalk island count drift")
    rows=[]
    for r in cross:
        eid=str(r["entity_ID"])
        if eid not in gm: raise Stop("crosswalk entity absent from frozen GIFT geography")
        g=gm[eid]
        arch=str(r.get("archip","") or "").strip()
        if arch.casefold() in {"","na","nan","none","null"}: arch=""
        rows.append({
            "entity_ID":eid,"geo_entity":str(r["geo_entity"]),"weigelt_id":str(r["weigelt_id"]),
            "archip":arch,"countryiso":str(r["countryiso"]),
            "lat":fnum(g["latitude"],"latitude"),"lon":fnum(g["longitude"],"longitude"),
            "area":fnum(r["weigelt_area"],"weigelt_area"),"dist":fnum(r["dist"],"dist"),
            "slmp":fnum(r["slmp"],"slmp"),"gmmc":fnum(r["gmmc"],"gmmc"),
            "elev":fnum(r["elev"],"elev"),"temp":fnum(r["temp"],"temp"),
            "vart":fnum(r["vart"],"vart"),"ccvt":fnum(r["ccvt"],"ccvt"),
            "prec":fnum(r["prec"],"prec"),"varp":fnum(r["varp"],"varp"),
        })
    return rows

def build(rows,contract):
    known=[r for r in rows if r["archip"]]
    if len(known)!=contract["population"]["expected_archip_known_islands"]:
        raise Stop("archip-known island count drift")
    by_arch=defaultdict(list)
    for r in known: by_arch[r["archip"]].append(r)
    if len(by_arch)!=contract["population"]["expected_archip_count_before_sparse_pool_filter"]:
        raise Stop("archipelago count drift")

    centroid={}
    for a,rs in by_arch.items():
        centroid[a]=(math.fsum(r["lat"] for r in rs)/len(rs),
                     circular_mean_longitude([r["lon"] for r in rs]))

    chosen_width=None; chosen_map=None; chosen_good=None
    for width in contract["regional_pool"]["candidate_cell_width_degrees"]:
        amap={a:pool_key(*centroid[a],int(width)) for a in by_arch}
        pool_n=defaultdict(int)
        for a,rs in by_arch.items(): pool_n[amap[a]]+=len(rs)
        good={p for p,n in pool_n.items() if n>=3}
        retained=sum(len(rs) for a,rs in by_arch.items() if amap[a] in good)
        if not retained: continue
        # mandatory one block per retained pool, ranked without outcomes
        mandatory=set()
        salt=contract["validation_blocks"]["ranking_salt"]
        for p in sorted(good):
            candidates=[a for a in by_arch if amap[a]==p]
            mandatory.add(min(candidates,key=lambda a:(hash_rank(salt,a),a)))
        mandatory_islands=sum(len(by_arch[a]) for a in mandatory)
        retained_fraction=retained/len(known)
        burden=mandatory_islands/retained
        if retained_fraction>=0.98 and burden<=0.20:
            chosen_width=int(width); chosen_map=amap; chosen_good=good; break
    if chosen_width!=contract["regional_pool"]["expected_selected_width_degrees"]:
        raise Stop("selected regional-pool width drift")

    primary=[r for r in known if chosen_map[r["archip"]] in chosen_good]
    if len(primary)!=contract["regional_pool"]["expected_primary_islands"]:
        raise Stop("primary plant island count drift")
    primary_arch=sorted({r["archip"] for r in primary})
    if len(primary_arch)!=contract["regional_pool"]["expected_archipelago_blocks"]:
        raise Stop("primary archipelago count drift")
    pools=sorted({chosen_map[a] for a in primary_arch})
    if len(pools)!=contract["regional_pool"]["expected_regional_pools"]:
        raise Stop("regional pool count drift")

    salt=contract["validation_blocks"]["ranking_salt"]
    mandatory=set()
    for p in pools:
        cand=[a for a in primary_arch if chosen_map[a]==p]
        mandatory.add(min(cand,key=lambda a:(hash_rank(salt,a),a)))
    remaining=sorted([a for a in primary_arch if a not in mandatory],
                     key=lambda a:(hash_rank(salt,a),a))
    total=len(primary); target=0.20*total
    candidates=[]
    selected=set(mandatory)
    def nsel(ss): return sum(len(by_arch[a]) for a in ss)
    if len(primary_arch)-len(selected)>=30:
        candidates.append((abs(nsel(selected)-target),len(selected),tuple(sorted(selected)),set(selected)))
    for a in remaining:
        selected.add(a)
        if len(primary_arch)-len(selected)>=30:
            candidates.append((abs(nsel(selected)-target),len(selected),tuple(sorted(selected)),set(selected)))
    if not candidates: raise Stop("no valid pilot prefix")
    _,_,_,pilot=min(candidates,key=lambda x:(x[0],x[1],x[2]))
    pilot_n=nsel(pilot)
    confirm=set(primary_arch)-pilot
    if len(pilot)!=contract["validation_blocks"]["expected_pilot_blocks"] or pilot_n!=contract["validation_blocks"]["expected_pilot_islands"]:
        raise Stop("pilot split drift")
    if len(confirm)!=contract["validation_blocks"]["expected_confirmatory_blocks"] or total-pilot_n!=contract["validation_blocks"]["expected_confirmatory_islands"]:
        raise Stop("confirmatory split drift")

    # Response-independent graph inside broad regional pools.
    nearest={}; pressure={}; edges_out=[]; selected_k={}; scales={}
    by_pool=defaultdict(list)
    for r in primary:
        r["regional_pool"]=chosen_map[r["archip"]]
        r["split"]="pilot" if r["archip"] in pilot else "confirmatory"
        by_pool[r["regional_pool"]].append(r)
    for p in sorted(by_pool):
        rs=sorted(by_pool[p],key=lambda r:(int(r["entity_ID"]) if r["entity_ID"].isdigit() else r["entity_ID"]))
        pts=[(r["entity_ID"],r["lat"],r["lon"]) for r in rs]
        k,es=choose_graph(pts); selected_k[p]=k
        lens=[d for _,_,d in es]; scale=statistics.median(lens)
        if not scale>0: raise Stop("nonpositive regional graph scale")
        scales[p]=scale; inc=defaultdict(list)
        for i,j,d in es:
            ida,idb=pts[i][0],pts[j][0]
            inc[ida].append(d); inc[idb].append(d)
            edges_out.append((p,ida,idb,d))
        for iid,_,_ in pts:
            if not inc[iid]: raise Stop("isolated regional graph island")
            nearest[iid]=min(inc[iid])
            pressure[iid]=math.fsum(math.exp(-d/scale) for d in inc[iid])

    primary=sorted(primary,key=lambda r:(int(r["entity_ID"]) if r["entity_ID"].isdigit() else r["entity_ID"]))
    raw={
      "ccvt":[r["ccvt"] for r in primary],
      "temp":[r["temp"] for r in primary],
      "vart":[r["vart"] for r in primary],
      "prec":[r["prec"] for r in primary],
      "varp":[r["varp"] for r in primary],
      "elev":[r["elev"] for r in primary],
      "log_area":[math.log(r["area"]) for r in primary],
      "dist":[r["dist"] for r in primary],
      "slmp":[r["slmp"] for r in primary],
      "gmmc":[r["gmmc"] for r in primary],
      "log1p_nearest_island_km":[math.log1p(nearest[r["entity_ID"]]) for r in primary],
      "generic_neighbor_pressure":[pressure[r["entity_ID"]] for r in primary],
    }
    zs={}; stats={}
    for name,vals in raw.items():
        z,m,sd=zvals(vals,name); zs[name]=z; stats[name]={"mean_hex":m.hex(),"sd_hex":sd.hex()}
    return primary,by_arch,pilot,confirm,selected_k,scales,edges_out,zs,stats,chosen_width,chosen_map,chosen_good

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("gift_geography",type=Path); ap.add_argument("crosswalk",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--partition",type=Path,required=True); ap.add_argument("--block-table",type=Path,required=True)
    ap.add_argument("--state",type=Path,required=True); ap.add_argument("--edges",type=Path,required=True)
    ap.add_argument("--excluded",type=Path,required=True); ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c["schema"]!="structural.gift_spatial_reference_contract.v1_46": raise Stop("contract schema drift")
        rows=load_inputs(a.gift_geography,a.crosswalk,c)
        primary,by_arch,pilot,confirm,selected_k,scales,edges,zs,stats,width,amap,good=build(rows,c)
        a.partition.parent.mkdir(parents=True,exist_ok=True)
        with a.partition.open("w",encoding="utf-8",newline="") as h:
            fields=["entity_ID","geo_entity","weigelt_id","archip","regional_pool","split"]
            w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n"); w.writeheader()
            for r in primary:w.writerow({k:r[k] for k in fields})
        with a.block_table.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n"); w.writerow(["archip","regional_pool","island_count","split"])
            for arch in sorted({r["archip"] for r in primary}):
                rs=[r for r in primary if r["archip"]==arch]
                w.writerow([arch,rs[0]["regional_pool"],len(rs),"pilot" if arch in pilot else "confirmatory"])
        names=list(zs)
        with a.state.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n")
            w.writerow(["entity_ID","regional_pool","archip","split"]+[f"z_{n}" for n in names])
            for i,r in enumerate(primary):
                w.writerow([r["entity_ID"],r["regional_pool"],r["archip"],r["split"]]+[zs[n][i].hex() for n in names])
        with a.edges.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n"); w.writerow(["regional_pool","from_entity_ID","to_entity_ID","distance_km_hex"])
            for p,x,y,d in sorted(edges):w.writerow([p,x,y,d.hex()])
        primary_ids={r["entity_ID"] for r in primary}
        with a.excluded.open("w",encoding="utf-8",newline="") as h:
            w=csv.writer(h,lineterminator="\n");w.writerow(["entity_ID","geo_entity","reason"])
            for r in rows:
                if r["entity_ID"] in primary_ids:continue
                reason="missing_archip" if not r["archip"] else "regional_pool_fewer_than_3_islands"
                w.writerow([r["entity_ID"],r["geo_entity"],reason])
        result={
          "schema":"structural.gift_spatial_reference_result.v1_46",
          "status":"PRISTINE_PLANT_SPATIAL_REFERENCE_FROZEN_RESPONSE_INDEPENDENTLY",
          "strict_common_geography_islands":548,
          "archip_known_islands":508,
          "primary_islands":len(primary),"archipelago_blocks":len(pilot)+len(confirm),
          "regional_pools":len(selected_k),"selected_regional_pool_width_degrees":width,
          "pilot_blocks":len(pilot),"pilot_islands":sum(1 for r in primary if r["split"]=="pilot"),
          "confirmatory_blocks":len(confirm),"confirmatory_islands":sum(1 for r in primary if r["split"]=="confirmatory"),
          "selected_k_by_regional_pool":selected_k,
          "regional_edge_scale_hex":{k:v.hex() for k,v in sorted(scales.items())},
          "edge_count":len(edges),"standardization":stats,
          "partition_sha256":file_sha(a.partition),"block_table_sha256":file_sha(a.block_table),
          "state_sha256":file_sha(a.state),"edge_sha256":file_sha(a.edges),"excluded_sha256":file_sha(a.excluded),
          "species_composition_opened":False,"species_richness_computed":False,
          "counts_as_empirical_evidence":False,"fresh_system_denominator_contribution":0,
          "species_response_authorized":False,
          "next_action":"resolve geological-origin metadata and freeze exact species-response firewall plus cross-fitted R3/C formulas before opening GIFT checklists"
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as e:
        result={"schema":"structural.gift_spatial_reference_result.v1_46","status":"STOP","reason":str(e),
          "species_composition_opened":False,"species_richness_computed":False,"counts_as_empirical_evidence":False,
          "fresh_system_denominator_contribution":0,"species_response_authorized":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
