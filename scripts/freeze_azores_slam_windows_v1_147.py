#!/usr/bin/env python3
"""Deterministically freeze one SLAM site key and disjoint pilot/confirmatory windows.

Consumes response-independent Event-audit summaries only.
"""
from __future__ import annotations
import argparse,csv,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/azores_slam_window_selection_contract_v1_147.json"

class Stop(RuntimeError): pass

def read_csv(path:Path):
    with path.open("r",encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

def as_bool(x):
    return str(x).strip().lower() in {"1","true","t","yes","y"}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--site-key-candidates",type=Path,required=True)
    ap.add_argument("--site-year-coverage",type=Path,required=True)
    ap.add_argument("--window-candidates",type=Path,required=True)
    ap.add_argument("--output-dir",type=Path,required=True)
    a=ap.parse_args()

    c=json.loads(a.contract.read_text())
    if c.get("schema")!="structural.azores_slam_window_selection_contract.v1_147":
        raise Stop("contract schema drift")

    sites=read_csv(a.site_key_candidates)
    cov=read_csv(a.site_year_coverage)
    wins=read_csv(a.window_candidates)
    site_by={r["candidate_key"]:r for r in sites}
    if len(site_by)!=len(sites):raise Stop("duplicate site-key candidate rows")

    selected_key=None
    reasons={}
    for key in c["site_key_selection"]["priority_order"]:
        r=site_by.get(key)
        if r is None:
            reasons[key]="missing audit row";continue
        nonblank=float(r["nonblank_event_fraction"])
        islands=int(r["unique_islands"])
        ew=[w for w in wins if w["candidate_key"]==key and as_bool(w["eligible_provisional"])]
        pairs=[
          (p,q) for p in ew for q in ew
          if int(p["end_year"]) < int(q["start_year"])
        ]
        ok=(nonblank==1.0 and islands>=3 and len(ew)>=2 and len(pairs)>=1)
        reasons[key]={
          "nonblank_event_fraction":nonblank,
          "unique_islands":islands,
          "eligible_windows":len(ew),
          "nonoverlapping_pairs":len(pairs),
          "admissible":ok
        }
        if ok and selected_key is None:
            selected_key=key
    if selected_key is None:
        raise Stop(f"no admissible site key under frozen rule: {reasons}")

    ew=[w for w in wins if w["candidate_key"]==selected_key and as_bool(w["eligible_provisional"])]
    eligible_pilots=[]
    for p in ew:
        later=[q for q in ew if int(p["end_year"]) < int(q["start_year"])]
        if later:eligible_pilots.append(p)
    if not eligible_pilots:raise Stop("no eligible pilot window with later nonoverlap")
    pilot=sorted(eligible_pilots,key=lambda r:(int(r["start_year"]),int(r["end_year"])))[0]
    later=[q for q in ew if int(pilot["end_year"]) < int(q["start_year"])]
    confirm=sorted(later,key=lambda r:(int(r["end_year"]),int(r["start_year"])),reverse=True)[0]

    def yearset(w):
        return set(range(int(w["start_year"]),int(w["end_year"])+1))
    if yearset(pilot)&yearset(confirm):raise Stop("selected windows overlap")

    selected_cov=[r for r in cov if r["candidate_key"]==selected_key]
    def core_sites(w):
        years=yearset(w)
        by={}
        for r in selected_cov:
            y=int(r["year"])
            if y not in years:continue
            by.setdefault(r["site_key"],set()).add(y)
        return sorted(k for k,v in by.items() if v==years)

    pilot_sites=core_sites(pilot);confirm_sites=core_sites(confirm)
    if not pilot_sites or not confirm_sites:raise Stop("selected window lacks core sites")

    out=a.output_dir;out.mkdir(parents=True,exist_ok=True)
    with (out/"selected_core_sites.csv").open("w",encoding="utf-8",newline="") as h:
        w=csv.writer(h,lineterminator="\n")
        w.writerow(["partition","site_key"])
        for x in pilot_sites:w.writerow(["pilot",x])
        for x in confirm_sites:w.writerow(["confirmatory",x])

    result={
      "schema":"structural.azores_slam_window_selection_result.v1_147",
      "status":"SLAM_RESPONSE_UNOPENED_SITE_KEY_AND_WINDOWS_FROZEN",
      "selected_site_key":selected_key,
      "site_key_audit":reasons,
      "pilot":{
        "start_year":int(pilot["start_year"]),
        "end_year":int(pilot["end_year"]),
        "islands_meeting_event_rule":int(pilot["islands_meeting_event_rule"]),
        "island_names":pilot["island_names"].split(";") if pilot["island_names"] else [],
        "core_sites":len(pilot_sites)
      },
      "confirmatory":{
        "start_year":int(confirm["start_year"]),
        "end_year":int(confirm["end_year"]),
        "islands_meeting_event_rule":int(confirm["islands_meeting_event_rule"]),
        "island_names":confirm["island_names"].split(";") if confirm["island_names"] else [],
        "core_sites":len(confirm_sites)
      },
      "year_overlap":0,
      "occurrence_extension_semantically_opened":False,
      "source_loss_effects_computed":0,
      "pilot_effect_estimation_allowed":False,
      "confirmatory_response_access_authorized":False,
      "next_gate":"freeze exact Event-supported core-site/island-year surfaces, then freeze taxon universe and opaque occurrence routing before any semantic occurrence access"
    }
    (out/"window_selection_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
