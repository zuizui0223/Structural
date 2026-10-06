from pathlib import Path
import importlib.util,json,csv

ROOT=Path(__file__).resolve().parents[1]

def load_module():
    p=ROOT/"scripts/build_ebird_three_wave_design_v1_158.py"
    spec=importlib.util.spec_from_file_location("ebird_v158",p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def contract():
    return json.loads((ROOT/"development/ebird_three_wave_design_contract_v1_158.json").read_text())

def synthetic_rows(eligible_windows=6):
    c=contract()
    rows=[]
    for idx,w in enumerate(c["candidate_windows"]):
        n=30 if idx < eligible_windows else 10
        ids=[str(i) for i in range(1,n+1)]
        for year in (w["t0"],w["t1"],w["t2"]):
            for oid in ids:
                rows.append((oid,int(year),1))
    return rows

def test_six_fixed_nonoverlapping_windows_cover_2002_2019_once():
    c=contract()
    years=[]
    for w in c["candidate_windows"]:
        years.extend([w["t0"],w["t1"],w["t2"]])
    assert years==list(range(2002,2020))
    assert len(set(years))==18

def test_response_independent_support_floor_and_partition_are_fixed():
    c=contract()
    assert c["window_support_rule"]["minimum_common_surveyed_islands"]==25
    assert c["window_qualification"]["minimum_eligible_windows"]==4
    assert c["partition_rule"]["rank_key"]=="SHA256('ebird-three-wave-v1.158|' + window_id)"
    assert c["partition_rule"]["manual_reassignment_authorized"] is False
    assert c["response_boundary"]["species_identity_may_open"] is False
    assert c["response_boundary"]["source_loss_events_may_be_constructed"] is False

def test_all_six_eligible_yields_two_pilot_four_confirmatory():
    m=load_module();c=contract()
    windows,islands=m.build(synthetic_rows(6),c)
    pilot=[r for r in windows if r["partition"]=="pilot"]
    conf=[r for r in windows if r["partition"]=="confirmatory"]
    assert len(pilot)==2
    assert len(conf)==4
    assert len(islands)==6*30

def test_four_eligible_yields_one_pilot_three_confirmatory():
    m=load_module();c=contract()
    windows,islands=m.build(synthetic_rows(4),c)
    assert sum(r["partition"]=="pilot" for r in windows)==1
    assert sum(r["partition"]=="confirmatory" for r in windows)==3
    assert sum(r["partition"]=="ineligible" for r in windows)==2
    assert len(islands)==4*30

def test_three_eligible_stops_before_species_access():
    m=load_module();c=contract()
    try:
        m.build(synthetic_rows(3),c)
    except m.Stop as e:
        assert "eligible windows 3 < required 4" in str(e)
    else:
        raise AssertionError("expected response-independent STOP")

def test_script_contains_no_species_response_fields():
    s=(ROOT/"scripts/build_ebird_three_wave_design_v1_158.py").read_text()
    # Historical v1.158 may name unopened downstream products in negative
    # receipt fields; it must not contain species-level data columns.
    for forbidden in ("SCIENTIFIC NAME","OBSERVATION COUNT"):
        assert forbidden not in s
    assert '"annual_species_occupancy_constructed":False' in s
    assert '"source_loss_events_constructed":False' in s

def test_priority_orders_acquisition_then_support_then_window_design():
    x=json.loads((ROOT/"development/structural_active_priority_v1_158.json").read_text())
    joined="\n".join(x["do_now"])
    assert joined.index("v1.157 acquisition") < joined.index("v1.156 same-byte") < joined.index("v1.158")
    assert x["live_candidate"]["species_response_access_authorized"] is False
