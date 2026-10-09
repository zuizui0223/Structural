#!/usr/bin/env python3
"""v1.252: study-campaign years for already published wild camera-positive taxa. NOT population persistence."""
import argparse,csv,io,json,re,math,unicodedata,sys
from collections import defaultdict,Counter
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from camtrapasia_four_island_field_positives_v1_250 import fetch,canon,SAFE_WILD
from camtrapasia_replicated_field_positives_v1_251 import __file__ as previous_script
ISLANDS={"65554":("Java",25),"70378":("Sumatra",49)}
STRICT7={"Arctictis binturong","Lariscus insignis","Macaca fascicularis","Martes flavigula","Muntiacus muntjak","Prionailurus bengalensis","Sus scrofa"}
def parse_year(value):
    s=(value or "").strip()
    if not re.fullmatch(r"\d{4}",s):return None
    y=int(s)
    return y if 1980<=y<=2026 else None
def study_windows(raw,ids):
    with io.StringIO(raw.decode("utf-8-sig")) as fp:
        reader=csv.DictReader(fp)
        if not {"survey_id","year_start","year_end"}.issubset(reader.fieldnames or []):
            raise ValueError("Study campaign year columns changed")
        windows={};invalid=0
        for rec in reader:
            sid=rec["survey_id"]
            if sid not in ids:continue
            if sid in windows:raise ValueError("Duplicate study window")
            start,end=parse_year(rec["year_start"]),parse_year(rec["year_end"])
            if start is None or end is None or start>end:
                invalid+=1;windows[sid]=None
            else:windows[sid]=(start,end)
    if set(windows)!=ids:raise ValueError("Study-window population not complete")
    return windows,invalid
def result(geo,taxonomy,metadata,photos):
    if geo.get("status")!="PASS_RESPONSE_SAFE_FULL239_POLYGON_IDENTITY_PRESCREEN":
        raise ValueError("Unfrozen original geographic candidate source")
    if taxonomy.get("exact_verified_taxon_overlaps")!=38:
        raise ValueError("Frozen original taxon names drift")
    targets={canon(x["survey_verified_binomial"]):x["original_529_binomial"].replace("."," ")
             for x in taxonomy["exact_matched_binomials"]}
    if len(targets)!=38:raise ValueError("Duplicate original name crosswalk")
    by_island=defaultdict(set)
    for r in geo["geography_only_candidate_studies"]:
        iid=r["candidate_original_heldout_ID"]
        if iid in ISLANDS:by_island[iid].add(r["survey_id"])
    if any(len(by_island[i])!=n for i,(label,n) in ISLANDS.items()):
        raise ValueError("Original Java/Sumatra camera study population drift")
    studies={sid:i for i,group in by_island.items() for sid in group}
    allwindows,faults=study_windows(metadata,set(studies))
    detections=defaultdict(lambda:defaultdict(set))
    with io.StringIO(photos.decode("utf-8-sig")) as fp:
        reader=csv.DictReader(fp)
        if not {"survey_id","records","class","binomial_verified","domestic"}.issubset(reader.fieldnames or []):
            raise ValueError("Source camera field columns changed")
        for row in reader:
            sid=row["survey_id"]
            if sid not in studies:continue
            if (row["class"] or "").strip().casefold()!="mammalia":continue
            key=canon(row["binomial_verified"] or "")
            if key not in targets or (row["domestic"] or "").strip().casefold() not in SAFE_WILD:continue
            count=float((row["records"] or "").strip())
            if not math.isfinite(count) or count<0 or int(count)!=count:raise ValueError("Invalid source photo records")
            if count>0:detections[studies[sid]][targets[key]].add(sid)
    rows=[]
    for label in sorted(STRICT7):
        per={}
        for iid,(island,n) in ISLANDS.items():
            d=detections[iid].get(label,set())
            timed=sorted([(sid,*allwindows[sid]) for sid in d if allwindows[sid] is not None],
                key=lambda z:(z[1],z[2],z[0]))
            disjoint=any(a[2]<b[1] or b[2]<a[1] for j,a in enumerate(timed) for b in timed[j+1:])
            before=sum(end<2017 for sid,start,end in timed)
            during=sum(start<=2017<=end for sid,start,end in timed)
            after=sum(start>2017 for sid,start,end in timed)
            per[island]={
                "wild_positive_distinct_survey_ids":len(d),
                "wild_positive_survey_ids_with_valid_years":len(timed),
                "study_interval_earliest_start":min((v[1] for v in timed),default=None),
                "study_interval_latest_end":max((v[2] for v in timed),default=None),
                "nonoverlapping_positive_study_windows":disjoint,
                "positive_studies_entirely_before_2017":before,
                "positive_studies_spanning_2017":during,
                "positive_studies_entirely_after_2017":after,
                "separated_positive_campaigns_bracketing_2017":bool(before and after)
            }
        rows.append({"taxon":label,"Java":per["Java"],"Sumatra":per["Sumatra"],
          "separate_positive_campaigns_in_both_islands":bool(per["Java"]["nonoverlapping_positive_study_windows"] and per["Sumatra"]["nonoverlapping_positive_study_windows"]),
          "prepost_2017_evidence_in_both_islands":bool(per["Java"]["separated_positive_campaigns_bracketing_2017"] and per["Sumatra"]["separated_positive_campaigns_bracketing_2017"])})
    return {
        "schema":"structural.camtrapasia_repeated_wild_taxa_campaign_windows_result.v1_252",
        "status":"PASS_POSTOUTCOME_CAMPAIGN_YEAR_DESCRIPTIVE_RECHECK",
        "source_candidate_study_centers":sum(map(len,by_island.values())),
        "source_study_windows_invalid_or_unknown":faults,
        "source_study_windows_valid":len(allwindows)-faults,
        "original_repeated_wild_taxa_postoutcome":7,
        "both_islands_nonoverlapping_positive_study_campaign_windows":sum(z["separate_positive_campaigns_in_both_islands"] for z in rows),
        "both_islands_positive_campaign_windows_pre2017_and_post2017":sum(z["prepost_2017_evidence_in_both_islands"] for z in rows),
        "per_taxon_timed_positive_evidence":rows,
        "study_windows_not_actual_photo_event_dates":True,
        "source_capture_nonpositive_not_true_species_absence":True,
        "source_camera_detections_are_prior_published":True,
        "original_IUCN_heldout_species_responses_read":0,
        "original_GEB_prediction_scores_read":0,
        "this_is_not_confirmatory_biological_persistence":True
    }
def main():
    p=argparse.ArgumentParser();p.add_argument("geometry",type=Path);p.add_argument("taxa",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    try:
        out=result(json.loads(a.geometry.read_text()),json.loads(a.taxa.read_text()),
                   fetch("CamTrapAsia_Metadata_20231031.csv"),fetch("CamTrapAsia_Captures_20231031.csv"))
    except Exception as e:out={"schema":"structural.camtrapasia_repeated_wild_taxa_campaign_windows_result.v1_252",
      "status":"STOP_CAMPAIGN_YEAR_OR_FROZEN_GEOGRAPHY_SOURCE","reason_type":type(e).__name__,
      "original_IUCN_heldout_species_responses_read":0}
    a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print(json.dumps(out,sort_keys=True))
    if out["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
