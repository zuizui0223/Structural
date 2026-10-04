#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,urllib.request,zipfile
from collections import Counter,defaultdict
from pathlib import Path
from scripts.audit_bala_event_core_v1_128 import parse_meta,parse_event_core,read_member,year_from,norm
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_pitfall_quality_contract_v1_134.json"
FIELD_RE=re.compile(r"(ETHY|TURQ|TUR)-S0*([1-9][0-9]*)",re.I)
class Stop(RuntimeError): pass
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def phase_for_year(y,w):
    h=[p for p,(a,b) in w.items() if y is not None and int(a)<=y<=int(b)]
    return h[0] if len(h)==1 else None
def lineage(code):
    return "FAI-NFCF-REPLACED-LINEAGE" if code in {"FAI-NFCF-T-11","FAI-NFCF-TB26"} else code
def allowed(code,ph,c):
    u=set(c["core_identity"].get("unchanged_29",[]))
    # fallback to parent-known rule encoded here
    unchanged={
      "FLO-NFFR-T-07","FLO-NFFR-T-06","FLO-NFMA-T-08","FLO-NFMA-T-16","FAI-NFCG-T-01","FAI-NFCG-T-03","FAI-NFCF-T-10",
      "PIC-NFMP-T-10","PIC-NFMP-T-01","PIC-NFCA-T-09","PIC-NFCA-T-08","SJG-NFPP-T-02","SJG-NFPP-T-09","SJG-NFTO-T-12","SJG-NFTO-T-06",
      "TER-NFSB-T-06","TER-NFSB-T-11","TER-NFBF-T-02","TER-NFPG-T-22","TER-NFPG-T-33","TER-NFBF-T-01","TER-NFTB-T-15","TER-NFTB-T-18",
      "SMG-NFGR-T-03","SMG-NFGR-T-07","SMG-NFPV-T-01","SMG-NFPV-T-04","SMR-NFPA-T-01","SMR-NFPA-T-03"}
    if code in unchanged:return True
    return (code=="FAI-NFCF-T-11" and ph=="BALA1") or (code=="FAI-NFCF-TB26" and ph in {"BALA2","BALA3"})
def parse_token(s):
    m=FIELD_RE.search(norm(s))
    if not m:return None
    n=int(m.group(2))
    if not 1<=n<=30:return None
    fam="ETHY" if m.group(1).upper()=="ETHY" else "TUR"
    return fam,n
def write(p,rows,fields):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT);ap.add_argument("--output-dir",type=Path,required=True);a=ap.parse_args()
    c=json.loads(a.contract.read_text())
    req=urllib.request.Request(c["source"]["dwca_url"],headers={"User-Agent":"Structural-BALA-pitfall-quality/1.0"})
    with urllib.request.urlopen(req,timeout=90) as resp: raw=resp.read()
    if sha_bytes(raw)!=c["source"]["archive_sha256"]:raise Stop("archive SHA drift")
    z=zipfile.ZipFile(io.BytesIO(raw));meta=next(x.filename for x in z.infolist() if Path(x.filename).name.lower()=="meta.xml")
    core,exts=parse_meta(read_member(z,meta)); eb=read_member(z,core["location"])
    if sha_bytes(eb)!=c["source"]["event_core_sha256"]:raise Stop("Event SHA drift")
    occ=[e for e in exts if e["rowType"].endswith("/Occurrence")]; ob=read_member(z,occ[0]["location"])
    if sha_bytes(ob)!=c["source"]["occurrence_extension_sha256_opaque_bytes"]:raise Stop("Occurrence SHA drift")
    del ob
    windows={"BALA1":(1997,2004),"BALA2":(2010,2011),"BALA3":(2019,2022)}
    rows,_=parse_event_core(eb,core); pits=[]
    for r in rows:
        ph=phase_for_year(year_from(r),windows);code=norm(r.get("locationID",""))
        if ph and allowed(code,ph,c) and norm(r.get("samplingProtocol",""))=="Pitfall solution":
            pits.append((ph,lineage(code),code,r))
    by=defaultdict(list)
    recovery=[]
    for ph,lin,code,r in pits:
        p=parse_token(r.get("fieldNumber",""))
        src="fieldNumber"
        if not p:
            p=parse_token(r.get("eventID",""));src="eventID_fallback" if p else "unresolved"
        recovery.append({"phase":ph,"lineage":lin,"locationID":code,"eventID":norm(r.get("eventID","")),"fieldNumber":norm(r.get("fieldNumber","")),"position":p[1] if p else "","family":p[0] if p else "","position_source":src})
        if p: by[(lin,ph)].append((p[1],p[0],norm(r.get("eventID",""))))
        else: by[(lin,ph)].append((None,None,norm(r.get("eventID",""))))
    site=[];dups=[];island=defaultdict(lambda:{"sites":0,"positions":0})
    for (lin,ph),rr in sorted(by.items()):
        pos=Counter(x[0] for x in rr if x[0] is not None); uniq=len(pos); unresolved=sum(x[0] is None for x in rr)
        for n,k in sorted(pos.items()):
            if k>1:dups.append({"phase":ph,"lineage":lin,"position":n,"event_rows":k,"duplicate_rows_above_one":k-1})
        isl=("FAI" if lin=="FAI-NFCF-REPLACED-LINEAGE" else lin.split("-")[0])
        island[(isl,ph)]["sites"]+=1;island[(isl,ph)]["positions"]+=uniq
        site.append({"phase":ph,"lineage":lin,"island":isl,"pitfall_event_rows":len(rr),"unique_recovered_positions":uniq,"unresolved_event_rows":unresolved,"duplicate_position_rows":sum(k-1 for k in pos.values() if k>1),"quality_pass":str(uniq>=20).lower()})
    island_rows=[]
    for (isl,ph),x in sorted(island.items()):
        nominal=x["sites"]*30;frac=x["positions"]/nominal
        island_rows.append({"island":isl,"phase":ph,"core_sites":x["sites"],"unique_recovered_positions":x["positions"],"nominal_positions":nominal,"coverage_fraction":frac,"quality_pass":str(frac>=0.80).lower()})
    site_pass=all(int(r["unique_recovered_positions"])>=20 for r in site); island_pass=all(float(r["coverage_fraction"])>=0.80 for r in island_rows)
    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    write(out/"pitfall_position_recovery.csv",recovery,["phase","lineage","locationID","eventID","fieldNumber","position","family","position_source"])
    write(out/"pitfall_duplicate_position_groups.csv",dups,["phase","lineage","position","event_rows","duplicate_rows_above_one"])
    write(out/"pitfall_site_phase_quality.csv",site,["phase","lineage","island","pitfall_event_rows","unique_recovered_positions","unresolved_event_rows","duplicate_position_rows","quality_pass"])
    write(out/"pitfall_island_phase_quality.csv",island_rows,["island","phase","core_sites","unique_recovered_positions","nominal_positions","coverage_fraction","quality_pass"])
    result={"schema":"structural.bala_pitfall_quality_result.v1_134","status":"BALA_PITFALL_SURVEY_QUALITY_FROZEN_RESPONSE_UNOPENED","pitfall_event_rows":len(pits),"site_phases":len(site),"island_phases":len(island_rows),"eventID_fallback_recoveries":sum(r["position_source"]=="eventID_fallback" for r in recovery),"unresolved_event_rows":sum(r["position_source"]=="unresolved" for r in recovery),"duplicate_position_rows":sum(int(r["duplicate_rows_above_one"]) for r in dups),"minimum_site_phase_unique_positions":min(int(r["unique_recovered_positions"]) for r in site),"minimum_island_phase_coverage_fraction":min(float(r["coverage_fraction"]) for r in island_rows),"all_site_phases_pass_20_of_30":site_pass,"all_island_phases_pass_80_percent":island_pass,"quality_gate_passed":site_pass and island_pass and len(site)==90 and len(island_rows)==21,"occurrence_extension_semantically_opened":False,"event_by_taxon_rows_parsed":0,"taxon_occurrence_values_opened":0,"source_loss_effects_computed":0,"confirmatory_eligible":False,"next_gate":"freeze Occurrence schema/header-only taxon routing token and deterministic pilot/confirmatory taxon partition"}
    (out/"pitfall_quality_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":main()
