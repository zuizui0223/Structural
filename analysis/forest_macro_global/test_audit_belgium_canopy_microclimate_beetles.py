"""Known-truth Dryad original 36-plot join without biological outcome inference."""
import csv,importlib.util,json
from pathlib import Path
import pytest

src=Path(__file__).with_name("audit_belgium_canopy_microclimate_beetles.py")
spec=importlib.util.spec_from_file_location("dryad_forest_beetle_source",src)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def write(path,columns,rows):
    with path.open("w",newline="",encoding="utf-8") as fd:
        w=csv.DictWriter(fd,fieldnames=columns,delimiter=";")
        w.writeheader()
        w.writerows(rows)

def fixture(tmp_path):
    plots=[{"PlotID":f"PRIVATE_PLOT_{i}", "TreeSpecies":"Oak" if i<25 else "Beech",
            "CanopyCover":str(20+i).replace(".",","),"BasalArea":"22,5",
            "DeadWood":"5,2","LitterDepth":"0,2"} for i in range(36)]
    micro=[]
    arth=[]
    for i in range(36):
        for dt in ("2022-06-01","2022-07-01","2022-08-01","2023-07-01"):
            micro.append({"PlotID":f"PRIVATE_PLOT_{i}","Date":dt,
                          "Tmacro":"28,5","Tmicro":"24,1","VWC":"0,15"})
        for dt in ("2022-06-15","2022-07-15","2022-08-15","2022-09-15"):
            arth.append({"PlotID":f"PRIVATE_PLOT_{i}","TrapID":"left",
                         "Date":dt,"Period":"1","SpeciesGroup":"Ground beetle",
                         "Species":"SECRET_TAXON_1","Count":"2"})
    p=tmp_path/"plot.csv";t=tmp_path/"temperature.csv";a=tmp_path/"beetles.csv"
    write(p,["PlotID","TreeSpecies","CanopyCover","BasalArea","DeadWood","LitterDepth"],plots)
    write(t,["PlotID","Date","Tmacro","Tmicro","VWC"],micro)
    write(a,["PlotID","TrapID","Date","Period","SpeciesGroup","Species","Count"],arth)
    return p,t,a

def test_36_plot_audit_not_36_independent_forests(tmp_path):
    p,t,a=fixture(tmp_path)
    r=m.run(p,t,a,tmp_path/"out")
    assert r["original_plot_characteristics_rows"]==36
    assert r["original_unique_plot_IDs_not_independent_forests"]==36
    assert r["source_plotday_Tmicro_Tmacro_both"]==144
    assert r["original_arthropod_rows"]==144
    assert r["source_microclimate_2022_plot_n"]==36
    assert r["site_overlap_2022_microclimate_vs_arthropod_2022_n"]==36
    assert r["all_36_field_plots_from_one_forest"]
    assert not r["new_thermal_effect_or_vertical_escape_scored"]
    report=(tmp_path/"out"/"belgium_original_climate_beetle_source_quality.json").read_text()
    assert "PRIVATE_PLOT" not in report and "SECRET_TAXON" not in report
    assert r["original_raw_plot_IDs_species_names_or_coordinates_exported"] is False

def test_missing_source_plot_or_duplicate_stops(tmp_path):
    p,t,a=fixture(tmp_path)
    rows,_=m.read_semicolon(t)
    rows[0]["PlotID"]="PRIVATE_PLOT_999"
    write(t,["PlotID","Date","Tmacro","Tmicro","VWC"],rows)
    with pytest.raises(ValueError,match="unmatched_original_microclimate_plot"):
        m.audit(p,t,a)
    p,t,a=fixture(tmp_path)
    rows,_=m.read_semicolon(p)
    rows[0]["PlotID"]=rows[1]["PlotID"]
    write(p,["PlotID","TreeSpecies","CanopyCover","BasalArea","DeadWood","LitterDepth"],rows)
    with pytest.raises(ValueError,match="duplicate"):
        m.audit(p,t,a)

def test_csv_decimal_comma_and_missing_na():
    assert m.parse_float("12,45")==12.45
    assert m.parse_float("NA") is None
    assert m.parse_float("-999") is None
    assert m.date_of("2022-07-14").year==2022
    with pytest.raises(ValueError,match="ambiguous_decimal_separator"):
        m.parse_float("12.345,67")
