from pathlib import Path
import csv, json, subprocess, sys, tempfile

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/audit_ebird_sampling_event_metadata_v1_149.py"
CONTRACT=ROOT/"development/ebird_sampling_event_metadata_audit_contract_v1_149.json"

HEADERS=[
    "SAMPLING EVENT IDENTIFIER","OBSERVATION DATE","LATITUDE","LONGITUDE",
    "PROTOCOL TYPE","PROTOCOL CODE","DURATION MINUTES","EFFORT DISTANCE KM",
    "EFFORT AREA HA","NUMBER OBSERVERS","ALL SPECIES REPORTED","GROUP IDENTIFIER"
]

def write_sed(path,rows,headers=HEADERS):
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=headers,delimiter="\t",lineterminator="\n")
        w.writeheader(); w.writerows(rows)

def run(path,out):
    return subprocess.run(
        [sys.executable,str(SCRIPT),str(path),"--output-dir",str(out)],
        cwd=ROOT,text=True,capture_output=True
    )

def test_contract_keeps_species_response_closed():
    x=json.loads(CONTRACT.read_text())
    assert x["status"]=="RESPONSE_UNOPENED_SED_SCHEMA_AND_COVERAGE_AUDIT_FROZEN"
    assert x["privacy_and_response_boundary"]["species_identity_may_be_read"] is False
    assert x["privacy_and_response_boundary"]["species_nondetection_may_be_constructed"] is False
    assert x["response_access_authorized"] is False
    assert x["next_gate"].startswith("only after this audit succeeds")

def test_sed_audit_aggregates_complete_effort_and_groups(tmp_path):
    sed=tmp_path/"sed.tsv"
    rows=[
      {
        "SAMPLING EVENT IDENTIFIER":"S1","OBSERVATION DATE":"2002-01-10",
        "LATITUDE":"10","LONGITUDE":"20","PROTOCOL TYPE":"Stationary","PROTOCOL CODE":"P21",
        "DURATION MINUTES":"5","EFFORT DISTANCE KM":"0","EFFORT AREA HA":"",
        "NUMBER OBSERVERS":"1","ALL SPECIES REPORTED":"1","GROUP IDENTIFIER":"G1"
      },
      {
        "SAMPLING EVENT IDENTIFIER":"S2","OBSERVATION DATE":"2002-01-10",
        "LATITUDE":"10.1","LONGITUDE":"20.1","PROTOCOL TYPE":"Traveling","PROTOCOL CODE":"P22",
        "DURATION MINUTES":"30","EFFORT DISTANCE KM":"2.5","EFFORT AREA HA":"",
        "NUMBER OBSERVERS":"2","ALL SPECIES REPORTED":"TRUE","GROUP IDENTIFIER":"G1"
      },
      {
        "SAMPLING EVENT IDENTIFIER":"S3","OBSERVATION DATE":"2003-06-01",
        "LATITUDE":"-5","LONGITUDE":"120","PROTOCOL TYPE":"Historical","PROTOCOL CODE":"P20",
        "DURATION MINUTES":"","EFFORT DISTANCE KM":"","EFFORT AREA HA":"",
        "NUMBER OBSERVERS":"","ALL SPECIES REPORTED":"0","GROUP IDENTIFIER":""
      },
      {
        "SAMPLING EVENT IDENTIFIER":"S4","OBSERVATION DATE":"2020-01-01",
        "LATITUDE":"0","LONGITUDE":"0","PROTOCOL TYPE":"Stationary","PROTOCOL CODE":"P21",
        "DURATION MINUTES":"60","EFFORT DISTANCE KM":"0","EFFORT AREA HA":"",
        "NUMBER OBSERVERS":"3","ALL SPECIES REPORTED":"FALSE","GROUP IDENTIFIER":""
      },
    ]
    write_sed(sed,rows)
    out=tmp_path/"out"
    p=run(sed,out)
    assert p.returncode==0,p.stderr+p.stdout
    r=json.loads((out/"ebird_sed_schema_receipt.json").read_text())
    assert r["checklist_rows"]==4
    assert r["complete_checklists"]==2
    assert r["incomplete_checklists"]==2
    assert r["rows_outside_2002_2019"]==1
    assert r["repeated_group_identifiers"]==1
    assert r["rows_in_repeated_groups"]==2
    assert r["species_values_read"]==0
    assert r["species_nondetections_constructed"]==0
    years=list(csv.DictReader((out/"ebird_sed_year_support.csv").open()))
    y2002=next(x for x in years if x["year"]=="2002")
    assert y2002["checklists"]=="2"
    assert y2002["complete_checklists"]=="2"
    assert y2002["distinct_months"]=="1"

def test_sed_audit_rejects_species_response_columns(tmp_path):
    sed=tmp_path/"wrong.tsv"
    headers=HEADERS+["SCIENTIFIC NAME"]
    row={h:"" for h in headers}
    row.update({
      "SAMPLING EVENT IDENTIFIER":"S1","OBSERVATION DATE":"2002-01-10",
      "LATITUDE":"10","LONGITUDE":"20","PROTOCOL TYPE":"Stationary","PROTOCOL CODE":"P21",
      "DURATION MINUTES":"10","EFFORT DISTANCE KM":"0","EFFORT AREA HA":"",
      "NUMBER OBSERVERS":"1","ALL SPECIES REPORTED":"1","GROUP IDENTIFIER":"",
      "SCIENTIFIC NAME":"Example species"
    })
    write_sed(sed,[row],headers)
    out=tmp_path/"out"
    p=run(sed,out)
    assert p.returncode!=0
    assert "species-response headers found" in (p.stderr+p.stdout)

def test_sed_audit_rejects_duplicate_sampling_event_id(tmp_path):
    sed=tmp_path/"dup.tsv"
    base={
      "OBSERVATION DATE":"2002-01-10","LATITUDE":"10","LONGITUDE":"20",
      "PROTOCOL TYPE":"Stationary","PROTOCOL CODE":"P21","DURATION MINUTES":"10",
      "EFFORT DISTANCE KM":"0","EFFORT AREA HA":"","NUMBER OBSERVERS":"1",
      "ALL SPECIES REPORTED":"1","GROUP IDENTIFIER":""
    }
    a=dict(base,**{"SAMPLING EVENT IDENTIFIER":"S1"})
    b=dict(base,**{"SAMPLING EVENT IDENTIFIER":"S1"})
    write_sed(sed,[a,b])
    p=run(sed,tmp_path/"out")
    assert p.returncode!=0
    assert "duplicate sampling event identifier" in (p.stderr+p.stdout)
