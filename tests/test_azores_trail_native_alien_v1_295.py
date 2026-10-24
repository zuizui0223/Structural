"""Synthetic-only v1.295 native/alien original trail-v1.4 response-gate regressions."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from test_azores_trail_plants_event_hierarchy_v1_292 import records
from azores_trail_new_event_frame_v1_294 import profile
from azores_trail_native_alien_v1_295 import score_from_records,frame_membership

def case():
    events=records()
    physical=json.loads((ROOT/"development/azores_trail_new_event_frame_v1_294.json").read_text(encoding="utf-8"))
    physical["source"]["original_event_rows"]=len(events)
    freeze=profile(events,physical)
    receipt={
        "status":"RETROSPECTIVE_MATCHED_FRAME_PASS_ONLY_OCCURRENCE_STILL_SEALED",
        "source_original_Event_rows":len(events),
        "future_scoring_event_coreids_sha256":freeze["future_scoring_event_coreids_sha256"],
        "number_original_Event_rows_eligible_for_score":len(events)
    }
    contract=json.loads((ROOT/"development/azores_trail_native_alien_response_contract_v1_295.json").read_text(encoding="utf-8"))
    occ=[]
    for e in events:
        core=e["original_coreid"]
        plot=e["eventID"].split(".")[-2]
        names=([("Nativa alba","native"),("Alienus rubra","introduced"),("Alienus minor","introduced")]
            if plot=="1" else
            [("Nativa alba","native"),("Nativa beta","native"),("Nativa gamma","native")])
        for name,status in names:
            occ.append({"original_coreid":core,"scientificName":name,
                        "taxonRank":"species","establishmentMeans":status})
    return events,occ,contract,physical,receipt

def test_source_response_matches_physical_original_fingerprint_before_score():
    e,o,c,p,r=case()
    ids,_,groups,frame=frame_membership(e,p)
    assert len(ids)==54
    assert frame["future_scoring_event_coreids_sha256"]==r["future_scoring_event_coreids_sha256"]
    assert len(groups)==6
    out=score_from_records(e,o,c,p,r)
    assert out["status"]=="SOURCE_OBSERVATIONAL_TRAIL_COMPOSITION_DESCRIPTIVE_SCORE"
    assert out["score"]["trails_positive_direction"]==3
    assert out["score"]["independent_trails"]==3
    assert out["score"]["mean_across_original_independent_trails_log_native_vs_alien_interior_minus_edge"]>0
    assert out["per_island"]["Terceira"]["distinct_trails"]==2
    assert out["per_island"]["São Miguel"]["distinct_trails"]==1
    assert out["frozen_eligible_Event_rows"]==54
    assert out["source_Event_join_coverage"]==1.
    assert out["species_rank_unknown_nativeness_count"]==0
    assert out["new_confirmatory_systems"]==0
    assert out["GEB_scientific_HOLD"] and not out["eBird_used"]
    assert "Nativa alba" not in json.dumps(out) and "mist.negros" not in json.dumps(out)

def test_unknown_status_causes_score_stop_not_posthoc_reclassification():
    e,o,c,p,r=case()
    for x in o[:50]:x["establishmentMeans"]="UNVERIFIED"
    out=score_from_records(e,o,c,p,r)
    assert out["status"]=="STOP_ORIGINAL_BIOLOGICAL_QUALITY_OR_SUPPORT"
    assert out["stop_reason"]=="unclassified_native_introduced_status_exceeds_frozen_gate"
    assert out["score"] is None
    assert out["new_confirmatory_systems"]==0

def test_low_biological_join_fraction_prevents_scoring():
    e,o,c,p,r=case()
    for x in o[:30]: x["original_coreid"]="wrong.coreid"
    out=score_from_records(e,o,c,p,r)
    assert out["status"]=="STOP_ORIGINAL_BIOLOGICAL_QUALITY_OR_SUPPORT"
    assert out["stop_reason"]=="insufficient_original_occurrence_Event_join_coverage"
    assert out["score"] is None

def test_event_receipt_hash_change_is_fail_before_scoring():
    e,o,c,p,r=case()
    r=copy.deepcopy(r)
    r["future_scoring_event_coreids_sha256"]="deadbeef"
    try:score_from_records(e,o,c,p,r)
    except ValueError as error: assert "receipt mismatch" in str(error)
    else:raise AssertionError("Source-ID footprint was not enforced")

def test_absent_intro_species_on_one_island_has_no_primary():
    e,o,c,p,r=case()
    for x in o:
        if x["original_coreid"].startswith("2019.malhadas") and x["establishmentMeans"]=="introduced":
            x["establishmentMeans"]="native"
    out=score_from_records(e,o,c,p,r)
    assert out["status"]=="STOP_ORIGINAL_BIOLOGICAL_QUALITY_OR_SUPPORT"
    assert out["stop_reason"]=="insufficient_native_or_introduced_species_on_one_island"
    assert out["score"] is None
