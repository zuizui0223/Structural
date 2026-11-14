"""Synthetic sPlotOpen source-level forest eligibility and traceability tests."""
import csv
import importlib.util
import io
from pathlib import Path
import zipfile

FILE=Path(__file__).with_name("audit_splotopen_forest_cohort.py")
spec=importlib.util.spec_from_file_location("splotopen_original_forest",FILE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

FIELDS=["is_plot","name","forest","is_forest","givd_id","dataset","biome",
        "country","plant_recorded","height_trees_highest","cover_tree_layer",
        "releve_area","species_richness","soilclim_pc1","soilclim_pc2",
        "latitude","longitude","location_uncertainty","naturalness","date"]

def source_file(p,duplicate=False):
    payload=io.StringIO()
    writer=csv.DictWriter(payload,fieldnames=FIELDS)
    writer.writeheader()
    for i in range(1050):
        src={
            "is_plot":"True","name":"private-plot-"+str(i),"forest":"True" if i%3!=0 else "False",
            "is_forest":"False" if i%7==0 else "True",
            "givd_id":"forest-network-"+str(i%3),"biome":"temperate" if i%2 else "tropical",
            "country":"JP" if i%3==0 else "BR","plant_recorded":"All vascular plants",
            "height_trees_highest":"12.0" if i%4 else "",
            "cover_tree_layer":"75.0" if i%5 else "",
            "releve_area":"100","species_richness":"23","soilclim_pc1":"0",
            "soilclim_pc2":"0","latitude":"34.5","longitude":"130.5",
            "location_uncertainty":"100","naturalness":"1","date":"946684800",
        }
        if duplicate and i==1049:src["name"]="private-plot-10"
        writer.writerow(src)
    with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("nodes.csv",payload.getvalue())
        z.writestr("edges.csv","source,target,original_species\n1,2,PRIVATE SPECIES\n")

def test_forest_eligibility_not_from_species_growth_form():
    x=m.plot_row({"is_plot":"true","name":"hidden-id","forest":"false",
        "is_forest":"true","height_trees_highest":"20","cover_tree_layer":"40"})
    assert x["primary_source_forest"] is False
    y=m.plot_row({"is_plot":"true","name":"hidden-id","forest":"true",
        "is_forest":"false"})
    assert y["primary_source_forest"] is True
    assert y["tree_height_valid"] is False
    assert m.flag("") is None
    assert m.number("nan") is None

def test_metadata_audit_counts_not_an_ecological_result(tmp_path):
    archive=tmp_path/"source.zip"
    source_file(archive)
    report,by_biome=m.audit(archive,tmp_path/"out")
    assert report["plot_nodes_unduplicated"]==1050
    assert report["source_contributor_forest_plots"]==700
    assert report["species_growth_form_selection_leakage_avoided"] is True
    assert report["original_taxon_edges_read"]==0
    assert report["independent_forest_regions_verified"]==0
    assert sum(x["field_contributor_forest_plots"] for x in by_biome)==700
    contents=" ".join(x.read_text() for x in (tmp_path/"out").iterdir())
    assert "PRIVATE SPECIES" not in contents
    assert "private-plot-10" not in contents
    assert "130.5" not in contents

def test_duplicate_original_plot_id_is_not_independent(tmp_path):
    archive=tmp_path/"bad.zip"
    source_file(archive,duplicate=True)
    try:
        m.audit(archive,tmp_path/"out")
        assert False
    except ValueError as e:
        assert "duplicate" in str(e)
