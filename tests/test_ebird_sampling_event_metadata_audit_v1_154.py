from pathlib import Path
import csv, json, subprocess, sys

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/audit_ebird_sampling_event_metadata_v1_154.py"
CONTRACT=ROOT/"development/ebird_sampling_event_metadata_audit_contract_v1_154.json"

COMMON=[
    "SAMPLING EVENT IDENTIFIER","OBSERVATION DATE","LATITUDE","LONGITUDE",
    "PROTOCOL CODE","DURATION MINUTES","EFFORT DISTANCE KM","EFFORT AREA HA",
    "NUMBER OBSERVERS","ALL SPECIES REPORTED","GROUP IDENTIFIER"
]
MODERN=COMMON+["OBSERVATION TYPE","PROTOCOL NAME"]
LEGACY=COMMON+["PROTOCOL TYPE"]

def write_sed(path,rows,headers):
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=headers,delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(rows)

def run(path,out):
    return subprocess.run(
        [sys.executable,str(SCRIPT),str(path),"--output-dir",str(out)],
        cwd=ROOT,text=True,capture_output=True
    )

def base_row():
    return {
      "SAMPLING EVENT IDENTIFIER":"S1","OBSERVATION DATE":"2002-01-10",
      "LATITUDE":"10","LONGITUDE":"20","PROTOCOL CODE":"P22",
      "DURATION MINUTES":"30","EFFORT DISTANCE KM":"2.5","EFFORT AREA HA":"",
      "NUMBER OBSERVERS":"2","ALL SPECIES REPORTED":"TRUE","GROUP IDENTIFIER":"G1"
    }

def test_contract_keeps_species_response_closed_and_declares_schema_aliases():
    x=json.loads(CONTRACT.read_text())
    assert x["status"]=="RESPONSE_UNOPENED_SED_SCHEMA_AND_COVERAGE_AUDIT_CURRENT_SCHEMA_COMPATIBILITY_FROZEN"
    assert x["privacy_and_response_boundary"]["species_identity_may_be_read"] is False
    assert x["privacy_and_response_boundary"]["species_nondetection_may_be_constructed"] is False
    assert x["response_access_authorized"] is False
    assert x["schema_compatibility"]["scientific_semantics_changed"] is False
    assert set(x["input"]["protocol_schema_variants"])=={"modern_v1_16_plus","legacy_pre_v1_16"}

def test_modern_v116_schema_is_accepted(tmp_path):
    sed=tmp_path/"modern.tsv"
    row=base_row(); row.update({"OBSERVATION TYPE":"Traveling","PROTOCOL NAME":"Traveling"})
    write_sed(sed,[row],MODERN)
    out=tmp_path/"out"
    p=run(sed,out)
    assert p.returncode==0,p.stderr+p.stdout
    r=json.loads((out/"ebird_sed_schema_receipt.json").read_text())
    assert r["detected_protocol_schema"]=="modern_v1_16_plus"
    assert r["species_values_read"]==0
    prot=list(csv.DictReader((out/"ebird_sed_protocol_counts.csv").open()))
    assert prot[0]["observation_type"]=="Traveling"
    assert prot[0]["protocol_name"]=="Traveling"
    assert prot[0]["protocol_code"]=="P22"

def test_legacy_protocol_type_schema_is_still_accepted(tmp_path):
    sed=tmp_path/"legacy.tsv"
    row=base_row(); row.update({"PROTOCOL TYPE":"Stationary"})
    write_sed(sed,[row],LEGACY)
    out=tmp_path/"out"
    p=run(sed,out)
    assert p.returncode==0,p.stderr+p.stdout
    r=json.loads((out/"ebird_sed_schema_receipt.json").read_text())
    assert r["detected_protocol_schema"]=="legacy_pre_v1_16"
    prot=list(csv.DictReader((out/"ebird_sed_protocol_counts.csv").open()))
    assert prot[0]["observation_type"]=="Stationary"
    assert prot[0]["protocol_name"]==""

def test_sed_audit_rejects_species_response_columns(tmp_path):
    sed=tmp_path/"wrong.tsv"
    headers=MODERN+["SCIENTIFIC NAME"]
    row=base_row(); row.update({"OBSERVATION TYPE":"Traveling","PROTOCOL NAME":"Traveling","SCIENTIFIC NAME":"Example species"})
    write_sed(sed,[row],headers)
    p=run(sed,tmp_path/"out")
    assert p.returncode!=0
    assert "species-response headers found" in (p.stderr+p.stdout)

def test_sed_audit_rejects_missing_protocol_schema(tmp_path):
    sed=tmp_path/"missing.tsv"
    write_sed(sed,[base_row()],COMMON)
    p=run(sed,tmp_path/"out")
    assert p.returncode!=0
    assert "no supported SED protocol-header schema matched" in (p.stderr+p.stdout)

def test_sed_audit_rejects_ambiguous_modern_and_legacy_headers(tmp_path):
    sed=tmp_path/"ambiguous.tsv"
    headers=MODERN+["PROTOCOL TYPE"]
    row=base_row(); row.update({"OBSERVATION TYPE":"Traveling","PROTOCOL NAME":"Traveling","PROTOCOL TYPE":"Traveling"})
    write_sed(sed,[row],headers)
    p=run(sed,tmp_path/"out")
    assert p.returncode!=0
    assert "ambiguous SED protocol-header schema" in (p.stderr+p.stdout)

def test_sed_audit_rejects_duplicate_sampling_event_id(tmp_path):
    sed=tmp_path/"dup.tsv"
    a=base_row(); a.update({"OBSERVATION TYPE":"Traveling","PROTOCOL NAME":"Traveling"})
    b=dict(a)
    write_sed(sed,[a,b],MODERN)
    p=run(sed,tmp_path/"out")
    assert p.returncode!=0
    assert "duplicate sampling event identifier" in (p.stderr+p.stdout)
