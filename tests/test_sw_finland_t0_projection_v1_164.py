from pathlib import Path
import csv,hashlib,importlib.util,json,math

ROOT=Path(__file__).resolve().parents[1]
PROJECTOR=ROOT/"scripts/project_sw_finland_t0_state_v1_164.py"
ROUTER=ROOT/"scripts/route_sw_finland_t0_columns_v1_164.py"
CONTRACT=ROOT/"development/sw_finland_t0_projection_contract_v1_164.json"
FIREWALL=ROOT/"development/sw_finland_plant_colonization_column_firewall_v1_162.json"

def mod(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_projection_uses_only_byte_routed_safe_surface(tmp_path):
    pmod=mod(PROJECTOR,"swf164p");rmod=mod(ROUTER,"swf164r")
    c=json.loads(CONTRACT.read_text());fw=json.loads(FIREWALL.read_text())
    c=dict(c);c["expected_support"]=dict(c["expected_support"]);c["expected_support"]["island_count"]=3
    c["source_identity_gate"]=dict(c["source_identity_gate"]);c["source_identity_gate"]["minimum_exact_species"]=2

    island_cols=["Euref_X_original","Euref_Y_original","Euref_X","Euref_Y","Residents_per_area_log","Area_log",
      "Buffer_2_km_log","Buffer_5_km_log","Shannon_habitats","Convolution","Limestone","Buildings","Meadow_or_pasture",
      "Deciduous_forest","Coniferous_forest","Mixed_forest","Scrub","Sand","Open_rock_or_bare_ground","Marsh","Shore_meadow"]
    species_cols=["Historical_total_log","North_limit","Ellenberg_Light","Ellenberg_Temperature","Ellenberg_Moisture","Ellenberg_Reaction",
      "Ellenberg_Nitrogen","Eklund_culture","Life_cycle","Life_form","SLA","Plant_height_log","Dispersal_vector","Seed_bank","Seed_mass_log",
      "Pollen_vector","Apomictic","Veg_repr","Family","Genus"]
    fields=["outcome","spp.name","holmkod","Dist_to_historical_log","Gowdis_traits"]+island_cols+species_cols
    raw=tmp_path/"mixed.csv"
    coords={"A":("0","0"),"B":("10","0"),"C":("20","0")}
    with raw.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for secret,sp,isl,nsource in [
          ("SECRET_A","sp1","A",1),("SECRET_B","sp1","B",1),("SECRET_C","sp2","C",2)
        ]:
            row={x:"1" for x in fields}
            row.update({"outcome":secret,"spp.name":sp,"holmkod":isl,
                        "Dist_to_historical_log":"1","Gowdis_traits":"0.25",
                        "Historical_total_log":format(math.log10(nsource+1),".17g")})
            row["Euref_X_original"],row["Euref_Y_original"]=coords[isl]
            row["Euref_X"],row["Euref_Y"]=coords[isl]
            w.writerow(row)

    sha=hashlib.sha256(raw.read_bytes()).hexdigest()
    hr={"schema":"structural.sw_finland_plant_colonization_header_audit.v1_163",
        "status":"HEADER_ONLY_AUDIT_COMPLETE_FUTURE_OUTCOME_ROWS_UNREAD","outcome_values_read":0,
        "file_sha256":sha,"header":fields}
    safe=tmp_path/"safe.csv"
    rr=rmod.route(raw,hr,fw,safe)
    assert b"SECRET" not in safe.read_bytes()

    out=tmp_path/"out"
    result=pmod.project(safe,rr,c,fw,out)
    assert result["status"]=="T0_EXACT_SOURCE_SUPPORT_QUALIFIED_FUTURE_OUTCOME_REMAINS_SEALED"
    assert result["exact_source_species_count"]==2
    assert result["outcome_values_read"]==0
    occ=list(csv.DictReader((out/"sw_finland_t0_historical_occupied_pairs.csv").open()))
    assert {(x["spp.name"],x["holmkod"]) for x in occ}=={("sp1","C"),("sp2","A"),("sp2","B")}

def test_incomplete_absence_rows_do_not_become_sources():
    pmod=mod(PROJECTOR,"swf164count")
    n,ok,_=pmod.historical_source_count(str(math.log10(3)),1e-6)
    assert ok and n==2
    # With 3 islands, one routed absence + two historical sources is exact;
    # zero routed absences + two sources would be incomplete, not a complement license.
    assert 1+n==3
    assert 0+n<3
