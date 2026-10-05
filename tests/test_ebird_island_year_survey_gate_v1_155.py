from pathlib import Path
import importlib.util,json,sqlite3

ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/build_ebird_island_year_survey_surface_v1_155.py"
    spec=importlib.util.spec_from_file_location("eb155",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_contract_freezes_current_schema_survey_rule():
    x=json.loads((ROOT/"development/ebird_island_year_survey_contract_v1_155.json").read_text())
    q=x["annual_survey_quality_rule"]
    assert q["complete_deduplicated_checklists_min"]==10
    assert q["distinct_months_min"]==4
    assert q["threshold_change_after_species_access_authorized"] is False
    assert x["island_geometry"]["doi"]=="10.5066/P91ZCSGM"
    assert x["island_geometry"]["nearest_island_rescue_allowed"] is False
    assert x["identity_binding"]["v1_154_schema_audit_and_v1_155_surface_must_use_identical_SED_bytes"] is True
    assert x["response_access_authorized"] is False

def test_modern_and_legacy_protocol_schema_are_supported():
    m=load_module()
    c=json.loads((ROOT/"development/ebird_island_year_survey_contract_v1_155.json").read_text())
    modern={k:k for k in [
      "OBSERVATION TYPE","PROTOCOL NAME","PROTOCOL CODE"
    ]}
    name,otype,pname=m.resolve_protocol_schema(c,modern)
    assert name=="modern_v1_16_plus"
    assert otype=="OBSERVATION TYPE" and pname=="PROTOCOL NAME"
    legacy={k:k for k in ["PROTOCOL TYPE","PROTOCOL CODE"]}
    name,otype,pname=m.resolve_protocol_schema(c,legacy)
    assert name=="legacy_pre_v1_16"
    assert otype=="PROTOCOL TYPE" and pname is None

def test_shared_group_event_key_and_conflict_handling():
    m=load_module()
    assert m.event_key("S1","G100")=="G:G100"
    assert m.event_key("S2","G100")=="G:G100"
    assert m.event_key("S3","")=="S:S3"
    conn=sqlite3.connect(":memory:");m.init_db(conn)
    base={
      "event_key":"G:G1","sid":"S2","year":2010,"month":5,"lat":10.0,"lon":20.0,
      "complete":True,"duration":30.0,"distance":1.0,"area":None,"observers":2,
      "observation_type":"Traveling","protocol_name":"Traveling","protocol_code":"P21"
    }
    m.insert_or_merge(conn,base)
    same=dict(base);same["sid"]="S1";m.insert_or_merge(conn,same)
    assert conn.execute("SELECT sid,conflict FROM events").fetchone()==("S1",0)
    bad=dict(base);bad["sid"]="S3";bad["lat"]=10.01;m.insert_or_merge(conn,bad)
    assert conn.execute("SELECT conflict FROM events").fetchone()==(1,)

def test_island_year_requires_ten_complete_events_and_four_months():
    m=load_module()
    rows=[]
    for i in range(10):
        rows.append({
          "OBJECTID":"7","year":2012,"month":(i%4)+1,
          "duration":30.0,"distance":1.0,"area":None,"observers":1,
          "observation_type":"Traveling","protocol_name":"Traveling","protocol_code":"P21"
        })
    assert m.aggregate(rows,10,4)[0]["surveyed"]==1
    assert m.aggregate(rows[:9],10,4)[0]["surveyed"]==0
    three=[dict(r,month=(i%3)+1) for i,r in enumerate(rows)]
    assert m.aggregate(three,10,4)[0]["surveyed"]==0

def test_script_retains_species_firewall():
    s=(ROOT/"scripts/build_ebird_island_year_survey_surface_v1_155.py").read_text()
    for x in ("SCIENTIFIC NAME","OBSERVATION COUNT","species_detection_read","annual_species_occupancy_constructed","source_loss_events_constructed"):
        assert x in s
    assert "nearest_island" not in s.lower()

def test_priority_keeps_ebird_on_hold_until_official_sed():
    x=json.loads((ROOT/"development/structural_active_priority_v1_155.json").read_text())
    assert x["confirmatory_lane"]["candidate_id"]=="ebird_global_islands_2002_2019"
    assert x["confirmatory_lane"]["status"]=="HOLD_OFFICIAL_SAMPLING_EVENT_DATA_NOT_PRESENT"
    assert x["frozen_next_rules"]["species_response_opened"] is False
