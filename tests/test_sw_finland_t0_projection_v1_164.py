from pathlib import Path
import csv,importlib.util,json,hashlib

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/project_sw_finland_t0_state_v1_164.py"
CONTRACT=ROOT/"development/sw_finland_t0_projection_contract_v1_164.json"
FIREWALL=ROOT/"development/sw_finland_plant_colonization_column_firewall_v1_162.json"

def load():
    spec=importlib.util.spec_from_file_location("swf164",SCRIPT);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_script_never_indexes_outcome_value():
    s=SCRIPT.read_text()
    assert 'row[outcome_index]' not in s
    assert 'outcome_values_read":0' in s

def test_projection_reconstructs_complement_without_outcome(tmp_path):
    m=load();c=json.loads(CONTRACT.read_text());f=json.loads(FIREWALL.read_text())
    # Relax published-size invariants only for this synthetic unit test.
    c=dict(c);c["expected_support"]={"potential_event_rows":3,"island_count":3,"species_count":2}
    island_cols=["Euref_X_original","Euref_Y_original","Euref_X","Euref_Y","Residents_per_area_log","Area_log",
      "Buffer_2_km_log","Buffer_5_km_log","Shannon_habitats","Convolution","Limestone","Buildings","Meadow_or_pasture",
      "Deciduous_forest","Coniferous_forest","Mixed_forest","Scrub","Sand","Open_rock_or_bare_ground","Marsh","Shore_meadow"]
    species_cols=["Historical_total_log","North_limit","Ellenberg_Light","Ellenberg_Temperature","Ellenberg_Moisture","Ellenberg_Reaction",
      "Ellenberg_Nitrogen","Eklund_culture","Life_cycle","Life_form","SLA","Plant_height_log","Dispersal_vector","Seed_bank","Seed_mass_log",
      "Pollen_vector","Apomictic","Veg_repr","Family","Genus"]
    fields=["outcome","spp.name","holmkod","Dist_to_historical_log"]+island_cols+species_cols
    p=tmp_path/"x.csv"
    with p.open("w",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields);w.writeheader()
        baseI={x:"1" for x in island_cols}; baseS={x:"2" for x in species_cols}
        for out,sp,isl in [("SECRET_A","sp1","A"),("SECRET_B","sp1","B"),("SECRET_C","sp2","C")]:
            row={"outcome":out,"spp.name":sp,"holmkod":isl,"Dist_to_historical_log":"0.5",**baseI,**baseS}
            # island identity must be reflected by at least coordinates while still constant within island
            row["Euref_X_original"]={"A":"1","B":"2","C":"3"}[isl]
            w.writerow(row)
    sha=hashlib.sha256(p.read_bytes()).hexdigest()
    hr={"schema":"structural.sw_finland_plant_colonization_header_audit.v1_163",
        "status":"HEADER_ONLY_AUDIT_COMPLETE_FUTURE_OUTCOME_ROWS_UNREAD","t0_projection_authorized":True,
        "outcome_values_read":0,"file_sha256":sha}
    out=tmp_path/"out";r=m.project(p,hr,c,f,out)
    assert r["outcome_values_read"]==0
    occ=list(csv.DictReader((out/"sw_finland_t0_historical_occupied_pairs.csv").open()))
    # sp1 absent A/B -> historically occupied C; sp2 absent C -> occupied A/B.
    assert {(x["spp.name"],x["holmkod"]) for x in occ}=={("sp1","C"),("sp2","A"),("sp2","B")}
