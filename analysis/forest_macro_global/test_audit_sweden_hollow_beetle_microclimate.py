"""Known-truth TSV source privacy and multi-table join QC for Sweden beetle."""
import csv,importlib.util,json
from pathlib import Path
import pytest

p=Path(__file__).with_name("audit_sweden_hollow_beetle_microclimate.py")
spec=importlib.util.spec_from_file_location("sweden_hollow_beetle_source",p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def source(path,header,n=120,other=False):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=header,delimiter="\t")
        w.writeheader()
        for i in range(n):
            data=dict.fromkeys(header,"")
            for k in header:
                if k in ("Time","Timestamp"):data[k]=f"2020-01-{(i%28)+1:02d} 00:00"
                elif k=="Tree":data[k]="SECRET_TREE_ID"
                elif k=="SpecimenID":data[k]=str(i)
                elif k=="Species":data[k]="SECRET_Beetle"
                else:data[k]="20.0" if not other else "21.0"
            w.writerow(data)

def test_source_inventory_without_raw_temperature_species_or_tree_values(tmp_path):
    a=tmp_path/"ambient.tsv";b=tmp_path/"internal.tsv"
    c=tmp_path/"individual.tsv";d=tmp_path/"recapture.tsv"
    source(a,["Time","Temperature","Tree"])
    source(b,["Time","Temperature","CavityTemp","Tree"],other=True)
    source(c,["SpecimenID","Tree","Species","BodyLength"])
    source(d,["SpecimenID","Tree","RecaptureCount"])
    q=m.run(a,b,c,d,tmp_path/"out")
    assert q["source_DOI"]=="10.5878/856g-v725"
    assert q["original_data_files"]["ambient"]["data_rows"]==120
    assert q["climate_sample_row_count_match"]
    assert q["first_four_records_first_field_match"]
    assert not q["candidate_tree_and_time_join_verified"]
    assert not q["new_ecological_microclimate_effect_or_thermal_refuge_test_scored"]
    txt=(tmp_path/"out"/"Sweden_hollow_beetle_climate_source_manifest.json").read_text()
    assert "SECRET_TREE_ID" not in txt and "SECRET_Beetle" not in txt
    assert "2020-01-" not in txt
    assert q["original_raw_beetle_or_logger_values_and_site_identifiers_exported"] is False

def test_source_missing_and_bad_delimiter_not_accepted(tmp_path):
    f=tmp_path/"bad.tsv"
    f.write_text("a,b,c\n1,2,3\n",encoding="utf-8")
    with pytest.raises(ValueError,match="unexpectedly_tiny"):
        m.source_table(f)
    f.write_text("a,b,c\n"+"1,2,3\n"*130,encoding="utf-8")
    with pytest.raises(ValueError,match="TAB_delimited"):
        m.source_table(f)
