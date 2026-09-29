#!/usr/bin/env python3
"""Query exactly the two published GIFT geology tables from the public API.

No checklist/species endpoint is permitted. The output is entity_ID + geology
state/simple + age only.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/gift_public_geology_contract_v1_53.json"
class Stop(RuntimeError): pass

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def get_json(url):
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"Structural-GIFT-geology-v1.53"})
    try:
        with urllib.request.urlopen(req,timeout=120) as r:
            raw=r.read()
    except Exception as exc:
        raise Stop(f"public geology query failed: {type(exc).__name__}") from None
    try:return json.loads(raw.decode("utf-8"))
    except Exception as exc: raise Stop("public geology query did not return JSON") from exc

def rows(x,label):
    if isinstance(x,list): return x
    if isinstance(x,dict):
        for key in ("data","results","rows"):
            if isinstance(x.get(key),list): return x[key]
    raise Stop(f"{label} did not return a row list")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--receipt",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c["schema"]!="structural.gift_public_geology_contract.v1_53":raise Stop("contract schema drift")
        base=c["public_API"]["base"]
        g_rows=rows(get_json(base+"geoentities_geology"),"geoentities_geology")
        l_rows=rows(get_json(base+"geology"),"geology")
        if not g_rows or not l_rows:raise Stop("public geology tables are empty")
        greq=set(c["projection"]["geoentities_geology_required_fields"])
        lreq=set(c["projection"]["geology_required_fields"])
        if not greq.issubset(g_rows[0]):raise Stop("geoentities_geology required fields absent")
        if not lreq.issubset(l_rows[0]):raise Stop("geology required fields absent")
        lookup={str(r["ID"]).strip():str(r["geology"]).strip() for r in l_rows}
        if len(lookup)!=len(l_rows):raise Stop("duplicate geology lookup ID")
        recode={}
        for simple,states in c["geology_simple_recode"].items():
            if simple=="other_or_missing":continue
            for state in states:
                if state in recode:raise Stop("duplicate geology state in frozen recode")
                recode[state]=simple
        out=[]
        seen=set()
        for r in g_rows:
            eid=str(r["entity_ID"]).strip()
            if not eid or eid in seen:raise Stop("blank or duplicate geology entity_ID")
            seen.add(eid)
            key=str(r["geology"]).strip()
            state=lookup.get(key,"")
            simple=recode.get(state,"")
            age=r.get("age_Ma")
            try:
                age_val=float(age) if age not in (None,"","NA") else None
                if age_val is not None and not math.isfinite(age_val):age_val=None
            except Exception:age_val=None
            out.append({"entity_ID":eid,"geology_state":state,"geology_simple":simple,"age_Ma":"" if age_val is None else format(age_val,".12g")})
        out.sort(key=lambda r:(int(r["entity_ID"]) if r["entity_ID"].isdigit() else r["entity_ID"]))
        a.output.parent.mkdir(parents=True,exist_ok=True)
        with a.output.open("w",encoding="utf-8",newline="") as h:
            w=csv.DictWriter(h,fieldnames=c["projection"]["saved_fields"],lineterminator="\n");w.writeheader();w.writerows(out)
        counts={}
        for r in out:
            k=r["geology_simple"] or "missing_other"
            counts[k]=counts.get(k,0)+1
        result={
          "schema":"structural.gift_public_geology_result.v1_53",
          "status":"PUBLIC_GIFT_GEOLOGY_PROJECTED_RESPONSE_INDEPENDENTLY",
          "geoentities_geology_rows":len(g_rows),"geology_lookup_rows":len(l_rows),
          "projected_entity_rows":len(out),"geology_simple_counts":counts,
          "output_sha256":sha(a.output),
          "species_endpoint_requested":False,"checklist_endpoint_requested":False,
          "species_composition_opened":False,"counts_as_empirical_evidence":False,
          "pilot_species_access_authorized":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,Stop) as exc:
        result={"schema":"structural.gift_public_geology_result.v1_53","status":"HOLD_ORIGIN_EXTERNAL_SOURCE_UNAVAILABLE",
          "reason":str(exc),"species_endpoint_requested":False,"checklist_endpoint_requested":False,
          "species_composition_opened":False,"counts_as_empirical_evidence":False,"pilot_species_access_authorized":False};code=2
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True));return code
if __name__=="__main__":raise SystemExit(main())
