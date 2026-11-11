"""Synthetic DATASAPROX metadata gate tests: never use species/abundance values."""
import csv,io,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import datasaprox_source_metadata_gate as m

COLS=["occurrenceID","eventID","datasetName","ownerInstitutionCode",
      "year","month","sampleSizeValue","sampleSizeUnit",
      "dynamicProperties","scientificName","organismQuantity"]

def make_archive(path,rows,fields=COLS):
    core=''.join('<field index="%d" term="http://rs.tdwg.org/dwc/terms/%s"/>'%(i,k) for i,k in enumerate(fields))
    meta=('<?xml version="1.0"?><archive xmlns="http://rs.tdwg.org/dwc/text/">'
          '<core rowType="http://rs.tdwg.org/dwc/terms/Occurrence" '
          'fieldsTerminatedBy="\\t" fieldsEnclosedBy="&quot;" ignoreHeaderLines="1">'
          '<files><location>occurrence.txt</location></files>'+core+'</core></archive>')
    data=io.StringIO();w=csv.writer(data,delimiter="\t",lineterminator="\n")
    w.writerow(fields);w.writerows(rows)
    with zipfile.ZipFile(path,"w") as z:
        z.writestr("meta.xml",meta);z.writestr("occurrence.txt",data.getvalue())
    return path

def sample(occ,event,project="D1",producer="P1",plot="A",layer="canopy",
           model="Polytrap",kind="window",year="2024",month="08",days="14",species="SECRET"):
    prop=json.dumps({"ID_plot":plot,"trap_stratum":layer,
                     "trap_model":model,"trap_type":kind,
                     "ID_condition":"control","trap_bait":"no","trap_colour":"transparent"})
    return [occ,event,project,producer,year,month,days,"day",prop,species,"999"]

def test_real_metadata_pairs_collapsed_by_event_and_response_opaque(tmp_path):
    rows=[sample(1,"e1"),sample(2,"e1",species="PRIVATE_X"),
          sample(3,"e2",layer="understorey"),
          sample(4,"e3",layer="ground",month="09"),
          sample(5,"e4",layer="ground",model="Lindgren")]
    r=m.run(make_archive(tmp_path/"in.zip",rows),tmp_path/"out")
    assert r["source_original_occurrence_rows_metadata_streamed"]==5
    assert r["original_unique_source_sample_IDs"]==4
    assert r["same_project_plot_month_method_treatment_paired_strata_nonindependent"]==1
    assert r["distinct_matched_original_project_plot_keys"]==1
    assert r["original_species_response_test_performed"] is False
    assert "SECRET" not in json.dumps(r)
    assert "PRIVATE_X" not in json.dumps(r)
    assert "Polytrap" not in json.dumps(r)
    assert '\"e1\"' not in json.dumps(r)  # quoted whole ID, not a SHA256 hex substring
    assert "P1" not in json.dumps(r)

def test_not_pooled_across_months_models_or_baits(tmp_path):
    a=sample(1,"e1")
    b=sample(2,"e2",layer="ground",year="2023")
    c=sample(3,"e3",layer="ground",model="Lindgren")
    d=sample(4,"e4",layer="ground",days="90")
    e=sample(5,"e5",layer="ground")
    e[8]=e[8].replace('"trap_bait": "no"','"trap_bait": "ethanol"')
    r=m.run(make_archive(tmp_path/"in.zip",[a,b,c,d,e]),tmp_path/"out")
    assert r["same_project_plot_month_method_treatment_paired_strata_nonindependent"]==0

def test_event_id_inconsistency_stops_before_pairing(tmp_path):
    rows=[sample(1,"e1",layer="canopy"),sample(2,"e1",layer="ground")]
    r=m.run(make_archive(tmp_path/"in.zip",rows),tmp_path/"out")
    assert r["status"]=="STOP_CONFLICTING_AUTHOR_EVENT_METADATA"
    assert r["conflicting_source_event_key_count"]==1
    assert r["conflicts_by_field_metadata_only"]=={"stratum":1}
    assert r["original_species_response_test_performed"] is False
    assert "distinct_matched_original_project_plot_keys" not in r

def test_missing_plot_never_inferred_from_lat_long(tmp_path):
    r=m.run(make_archive(tmp_path/"in.zip",[
       sample(1,"e1",plot=""),sample(2,"e2",plot="",layer="ground")
    ]),tmp_path/"out")
    assert r["distinct_matched_original_project_plot_keys"]==0

def test_raw_stratum_and_invalid_duration_not_rescued():
    assert m.layer("canopy")=="upper"
    assert m.layer("upper canopy")=="upper"
    assert m.layer("sous-bois")=="lower"
    assert m.layer("ground")=="lower"
    assert m.layer("5m unknown level")=="unclassified"
    assert m.duration("12","days")==12
    assert m.duration("12","litres") is None
    assert m.duration("nan","days") is None
    assert m.properties('ID_plot: X; trap_stratum: sous-bois; trap_model: Polytrap')["trap_stratum"]=="sous-bois"

def test_30_physical_plots_across_three_original_projects_is_only_candidate(tmp_path):
    rows=[];x=0
    for proj in ("PR1","PR2","PR3"):
        for k in range(10):
            for layer in ("canopy","understorey"):
                x+=1
                rows.append(sample(x,"event"+str(x),project=proj,plot="plot"+str(k),layer=layer))
    r=m.run(make_archive(tmp_path/"in.zip",rows),tmp_path/"out")
    assert r["distinct_matched_original_project_plot_keys"]==30
    assert r["distinct_matched_original_project_keys"]==3
    assert r["frozen_exploratory_design_gate_passed"] is True
    assert not r["original_plot_independence_field_hierarchy_verified"]
    assert not r["original_species_response_test_performed"]

def test_author_event_identity_missing_is_not_fabricated():
    fields={"datasetName":0,"dynamicProperties":1}
    r=m.inspect_rows(iter([]),fields)
    assert r["status"]=="STOP_NO_AUTHOR_EVENT_ID"

def test_conflicting_original_events_all_excluded_without_erasing_original_stop(tmp_path):
    rows=[];x=0
    for project in ("S1","S2","S3"):
        for i in range(10):
            for layer in ("canopy","understorey"):
                x+=1;rows.append(sample(x,"evt"+str(x),project=project,
                                       plot="plot"+str(i),layer=layer))
    # A separate source-defined event key is internally contradictory.
    # It must be removed entirely, not relabeled by its taxon rows.
    rows.append(sample(61,"collision",project="S1",plot="bad",layer="canopy"))
    rows.append(sample(62,"collision",project="S1",plot="bad",layer="ground"))
    q=m.run(make_archive(tmp_path/"in.zip",rows),tmp_path/"out")
    assert q["status"]=="STOP_CONFLICTING_AUTHOR_EVENT_METADATA"
    assert q["conflicting_source_event_key_count"]==1
    assert q["post_qa_conservatively_retained_consistent_source_event_keys"]==60
    assert q["post_qa_excluded_entire_conflicting_source_event_keys"]==1
    assert q["post_qa_distinct_project_plot_keys_candidate_only"]==30
    assert q["post_qa_distinct_source_project_keys_candidate_only"]==3
    assert q["post_qa_meets_numerical_30_plot_3_project_threshold_only"]
    assert not q["post_qa_original_independent_physical_forest_verification"]
    assert not q["post_qa_species_response_scored"]
    assert not q["original_species_response_test_performed"]

def test_progressive_design_gate_locates_model_mismatch_without_specimen_rows(tmp_path):
    rows=[
        sample(1,"upper",plot="A",layer="canopy",model="Polytrap"),
        sample(2,"lower",plot="A",layer="ground",model="Lindgren"),
        sample(3,"bad",plot="B",layer="canopy"),
        sample(4,"bad",plot="B",layer="ground")
    ]
    q=m.run(make_archive(tmp_path/"in.zip",rows),tmp_path/"out")
    assert q["status"]=="STOP_CONFLICTING_AUTHOR_EVENT_METADATA"
    stages=q["post_qa_unpaired_progressive_design_support_groups_nonindependent"]
    assert stages["01_shared_original_project_plot"]==1
    assert stages["02_plus_same_year_month"]==1
    assert stages["03_plus_same_trap_model"]==0
    assert q["post_qa_metadata_availability_by_field_source_event_keys"]["original_plot"]==2
    assert q["post_qa_source_event_canonical_stratum_counts"]=={"lower":1,"upper":1}
    assert not q["post_qa_species_response_scored"]
