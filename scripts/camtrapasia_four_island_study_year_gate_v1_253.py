#!/usr/bin/env python3
"""All 78 fixed camera-study year metadata ONLY, source 2017 vintage eligibility, no captures."""
import argparse,csv,io,json,re,math,sys
from collections import defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from camtrapasia_sites_vs_mammal_heldout_grid_v1_239 import get_source
ISLANDS={"65489":("Bawean",2),"65360":("Buton",2),"65554":("Java",25),"70378":("Sumatra",49)}
def year(x):
    v=(x or "").strip()
    if not re.fullmatch(r"\d{4}",v):return None
    q=int(v)
    return q if 1980<=q<=2026 else None
def summarize(geography,metadata):
    if geography.get("status")!="PASS_RESPONSE_SAFE_FULL239_POLYGON_IDENTITY_PRESCREEN" or (
      geography.get("retained_geography_candidate_study_count"),
      geography.get("distinct_candidate_original_heldout_islands"))!=(79,5):
        raise ValueError("Old original heldout geography source not immutable PASS")
    groups=defaultdict(set)
    blocks=defaultdict(set)
    for rec in geography.get("geography_only_candidate_studies",[]):
        iid=rec["candidate_original_heldout_ID"]
        if iid not in ISLANDS:continue
        groups[iid].add(rec["survey_id"])
        blocks[iid].add(rec["original_heldout_block_id"])
    if any(len(groups[iid])!=expected or len(blocks[iid])!=1 for iid,(name,expected) in ISLANDS.items()):
        raise ValueError("Geographic original island survey denominator drift")
    if len(set().union(*groups.values()))!=78:raise ValueError("Unexpected duplicated survey IDs")
    selected={sid:iid for iid,ids in groups.items() for sid in ids}
    rows={}
    with io.StringIO(metadata.decode("utf-8-sig")) as stream:
        reader=csv.DictReader(stream)
        needed={"survey_id","year_start","year_end","effort"}
        if not needed.issubset(reader.fieldnames or []):
            raise ValueError("Source metadata study year/effort schema changed")
        for rec in reader:
            sid=rec["survey_id"]
            if sid not in selected:continue
            if sid in rows:raise ValueError("Duplicate selected campaign ID")
            start,end=year(rec["year_start"]),year(rec["year_end"])
            try:effort=float(rec["effort"])
            except (TypeError,ValueError):raise ValueError("Missing source study effort")
            if not math.isfinite(effort) or effort<0:raise ValueError("Invalid source effort")
            label=("unknown" if start is None or end is None or start>end
                else "before_2017" if end<2017
                else "after_2017" if start>2017
                else "includes_2017")
            rows[sid]={"start":start,"end":end,"effort":effort,"group":label}
    if set(rows)!=set(selected):raise ValueError("Source study campaign identities missing")
    out=[];after_blocks=set()
    for iid,(name,n) in ISLANDS.items():
        arr=[rows[sid] for sid in groups[iid]]
        cnt={key:sum(x["group"]==key for x in arr) for key in ("before_2017","includes_2017","after_2017","unknown")}
        if sum(cnt.values())!=n:raise ValueError("Failed to partition campaign years")
        if cnt["after_2017"]:after_blocks|=blocks[iid]
        valid=[x for x in arr if x["group"]!="unknown"]
        out.append({"island":name,"original_heldout_island_ID":iid,"original_heldout_block":next(iter(blocks[iid])),
          "study_campaign_ids":n,"calendar_study_intervals":cnt,
          "campaign_earliest_start":min((z["start"] for z in valid),default=None),
          "campaign_latest_end":max((z["end"] for z in valid),default=None),
          "source_total_full_campaign_effort":sum(x["effort"] for x in arr),
          "full_campaign_effort_by_era":{key:sum(x["effort"] for x in arr if x["group"]==key)
              for key in cnt}})
    return {"schema":"structural.camtrapasia_four_island_campaign_year_eligibility_result.v1_253",
        "status":"PASS_METADATA_ONLY_2017_CAMPAIGN_ERA_ELIGIBILITY",
        "island_camera_studies":78,
        "all_original_island_blocks":len({z["original_heldout_block"] for z in out}),
        "candidate_islands_with_entirely_post2017_camera_studies":sum(z["calendar_study_intervals"]["after_2017"]>0 for z in out),
        "candidate_original_heldout_blocks_with_post2017_campaigns":len(after_blocks),
        "per_island_geographic_camera_campaign_years":out,
        "source_species_photo_rows_opened":0,
        "original_IUCN_heldout_species_values_read":0,
        "original_mammal_predictions_read":0,
        "2017_map_is_not_field_survey_baseline":True,
        "ecological_persistence_or_disappearance_not_inferred":True}
def main():
    p=argparse.ArgumentParser();p.add_argument("geography",type=Path);p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True)
    try:x=summarize(json.loads(a.geography.read_text()),get_source())
    except Exception as e:x={"schema":"structural.camtrapasia_four_island_campaign_year_eligibility_result.v1_253",
        "status":"STOP_STUDY_ERA_GEO_SOURCE_SCHEMA","reason_type":type(e).__name__,
        "source_species_photo_rows_opened":0,"original_IUCN_heldout_species_values_read":0}
    a.out.write_text(json.dumps(x,sort_keys=True,indent=2)+"\n")
    print(json.dumps(x,sort_keys=True))
    if x["status"].startswith("STOP"):raise SystemExit(2)
if __name__=="__main__":main()
