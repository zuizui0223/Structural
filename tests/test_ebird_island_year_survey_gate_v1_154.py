from pathlib import Path
import importlib.util,json,sqlite3,tempfile

ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/build_ebird_island_year_survey_surface_v1_154.py"
    spec=importlib.util.spec_from_file_location("eb154",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_contract_freezes_response_independent_survey_rule():
    x=json.loads((ROOT/"development/ebird_island_year_survey_contract_v1_154.json").read_text())
    q=x["annual_survey_quality_rule"]
    assert q["complete_deduplicated_checklists_min"]==10
    assert q["distinct_months_min"]==4
    assert q["threshold_change_after_species_access_authorized"] is False
    assert x["island_geometry"]["doi"]=="10.5066/P91ZCSGM"
    assert x["island_geometry"]["nearest_island_rescue_allowed"] is False
    assert x["response_access_authorized"] is False

def test_shared_group_event_key_deduplicates_observers():
    m=load_module()
    assert m.make_event_key("S1","G100")=="G:G100"
    assert m.make_event_key("S2","G100")=="G:G100"
    assert m.make_event_key("S3","")=="S:S3"

def test_conflicting_shared_group_is_flagged():
    m=load_module()
    conn=sqlite3.connect(":memory:");m.init_db(conn)
    base={
      "event_key":"G:G1","sid":"S2","year":2010,"month":5,"lat":10.0,"lon":20.0,
      "complete":True,"duration":30.0,"distance":1.0,"area":None,"observers":2,
      "protocol_type":"Traveling","protocol_code":"P21"
    }
    m.insert_or_merge(conn,base,1e-6)
    same=dict(base);same["sid"]="S1"
    m.insert_or_merge(conn,same,1e-6)
    row=conn.execute("SELECT sid,conflict FROM events WHERE event_key='G:G1'").fetchone()
    assert row==("S1",0)
    bad=dict(base);bad["sid"]="S3";bad["lat"]=10.01
    m.insert_or_merge(conn,bad,1e-6)
    row=conn.execute("SELECT conflict FROM events WHERE event_key='G:G1'").fetchone()
    assert row==(1,)

def test_island_year_requires_ten_checklists_and_four_months():
    m=load_module()
    rows=[]
    for i in range(10):
        rows.append({
          "OBJECTID":"7","year":2012,"month":(i%4)+1,
          "duration":30.0,"distance":1.0,"area":None,"observers":1,
          "protocol_type":"Traveling","protocol_code":"P21"
        })
    out=m.aggregate_mapped_rows(rows,10,4)
    assert len(out)==1 and out[0]["surveyed"]==1
    rows2=[dict(r) for r in rows[:9]]
    out2=m.aggregate_mapped_rows(rows2,10,4)
    assert out2[0]["surveyed"]==0
    rows3=[dict(r,month=(i%3)+1) for i,r in enumerate(rows)]
    out3=m.aggregate_mapped_rows(rows3,10,4)
    assert out3[0]["surveyed"]==0

def test_script_has_no_species_outcome_construction():
    s=(ROOT/"scripts/build_ebird_island_year_survey_surface_v1_154.py").read_text()
    assert "SCIENTIFIC NAME" in s
    assert "OBSERVATION COUNT" in s
    assert "species_detection_read" in s
    assert "annual_species_occupancy_constructed" in s
    assert "source_loss_events_constructed" in s
    assert "nearest" not in s.lower() or "nearest" not in s.lower().split("map_events",1)[1]

def test_active_priority_leaves_ebird_on_hold_until_official_sed():
    x=json.loads((ROOT/"development/structural_active_priority_v1_154.json").read_text())
    assert x["confirmatory_lane"]["candidate_id"]=="ebird_global_islands_2002_2019"
    assert x["confirmatory_lane"]["status"]=="HOLD_OFFICIAL_SAMPLING_EVENT_DATA_NOT_PRESENT"
    assert x["frozen_next_rules"]["species_response_opened"] is False
