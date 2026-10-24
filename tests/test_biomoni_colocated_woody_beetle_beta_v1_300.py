"""v1.300 response-free synthetic known-truth cross-taxon spatial beta-transfer."""
import copy,io,json,math,random,sys,zipfile
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
sys.path.insert(0,str(ROOT/"tests"))
from biomoni_colocated_woody_beetle_beta_v1_300 import (
    analyse_sets,score_original,original_occurrence_body,PERMUTATIONS
)
from biomoni_common_method_terceira_v1_299 import evaluate
from test_biomoni_terceira_event_colocation_v1_298 import fixtures

def protocols():
    c=json.loads((ROOT/"development/biomoni_colocated_woody_beetle_beta_transfer_protocol_v1_300.json").read_text(encoding="utf-8"))
    e=json.loads((ROOT/"development/biomoni_terceira_colocated_event_gate_v1_298.json").read_text(encoding="utf-8"))
    m=json.loads((ROOT/"development/biomoni_common_method_study_design_v1_299.json").read_text(encoding="utf-8"))
    return c,e,m

def known_truth_sets():
    # Alternating taxonomic landscapes across a spatial gradient. The same
    # plot-label parity in two taxon groups is information beyond distance.
    w=[{"woody_shared","woody_even" if i%2==0 else "woody_odd"} for i in range(10)]
    b=[{"beetle_shared","beetle_even" if i%2==0 else "beetle_odd"} for i in range(10)]
    coords=[(38.700+i*.004,-27.200-i*.003) for i in range(10)]
    return w,b,coords

def synthetic_event_fixture():
    t,b=fixtures()
    for n in range(10):
        site=[r for r in b if r["source_coreid"].startswith(f"b-ter-{n}-")]
        site.sort(key=lambda r:r["source_coreid"])
        for i,rec in enumerate(site):
            if i==0:rec["samplingProtocol"]="AAS"
            elif i<5:rec["samplingProtocol"]="PIT"
            elif i==5:rec["samplingProtocol"]="GWS"
            else:rec["samplingProtocol"]=f"local{n}-only"
    return t,b

def synthetic_occurrences(tree_events,beetle_events):
    t=[];b=[]
    for i in range(10):
        tree=next(x for x in tree_events if x["source_coreid"]==f"tree-ter-{i}")
        for taxon in ("Woody shared","Woody even" if i%2==0 else "Woody odd"):
            t.append({"source_coreid":tree["source_coreid"],
                      "scientificName":taxon,"taxonRank":"species"})
        beetle_eligible=sorted(
            [x for x in beetle_events if x["source_coreid"].startswith(f"b-ter-{i}-") and
             x["samplingProtocol"] in ("AAS","PIT","GWS")],
            key=lambda x:x["source_coreid"])
        assert len(beetle_eligible)==6
        for ix,taxon in enumerate(("Beetle shared","Beetle even" if i%2==0 else "Beetle odd")):
            b.append({"source_coreid":beetle_eligible[ix]["source_coreid"],
                      "scientificName":taxon,"taxonRank":"species"})
    t.extend([{"source_coreid":tree_events[10]["source_coreid"],
               "scientificName":"Unmatched other island","taxonRank":"species"}]*(402-len(t)))
    b.extend([{"source_coreid":beetle_events[-1]["source_coreid"],
               "scientificName":"Pico-only beetle","taxonRank":"species"}]*(539-len(b)))
    assert len(t)==402 and len(b)==539
    return t,b

def test_same_plot_cross_taxon_known_truth_adds_spatial_predictive_info():
    c,_,_=protocols()
    w,b,coords=known_truth_sets()
    result=analyse_sets(w,b,coords,c)
    assert result["status"]=="SOURCE_OBSERVED_COLOCATED_BETA_PREDICTIVE_CONGRUENCE_SCORED"
    assert result["plot_pair_n"]==45 and result["physically_independent_plot_n"]==10
    assert result["baseline_geo_only_LOPO_MSE"]>result["added_beetle_LOPO_MSE"]
    assert result["primary_beetle_incremental_LOPO_MSE_gain"]>0
    assert result["fixed_permutation_label_shuffle_n"]==999
    assert result["permutation_fixed_seed"]==20261024
    assert result["descriptive_positive_cross_taxon_information"]
    assert 0<result["permutation_plot_label_exceedance_rank"]<=1

def test_true_plot_unit_required_non_detected_plot_is_stop_not_jaccard_similarity():
    c,_,_=protocols()
    w,b,coords=known_truth_sets()
    b[0]=set()
    out=analyse_sets(w,b,coords,c)
    assert out["status"]=="STOP_FROZEN_BIOLOGICAL_ESTIMABILITY_NO_CROSS_TAXON_SCORE"
    assert "plot" in out["stop_reason"].lower()

def test_original_event_subset_fingerprint_and_source_roles_reconcile_on_synthetic():
    c,e,m=protocols()
    t,b=synthetic_event_fixture()
    source_only=evaluate(t,b,m,e)
    assert source_only["status"]=="EXPLORATORY_TEN_PLOTS_SIX_COMMON_METHOD_BEETLE_EVENTS_EACH_RESPONSE_SEALED"
    c["frozen_event_receipt"]["original_full_site_woody_beetle_crosswalk_sha256"]=source_only["full_original_tree_beetle_Event_crosswalk_SHA256"]
    c["frozen_event_receipt"]["selected_beetle_Event_coreids_sha256"]=source_only["selected_original_Event_coreids_sha256"]
    c["frozen_event_receipt"]["selected_tree_beetle_method_site_fingerprint"]=source_only["selected_cross_taxon_site_tree_beetle_method_fingerprint"]
    tw,bb=synthetic_occurrences(t,b)
    result=score_original(t,b,tw,bb,e,m,c)
    assert result["status"]=="SOURCE_OBSERVED_COLOCATED_BETA_PREDICTIVE_CONGRUENCE_SCORED"
    assert result["source_selected_equal_effort_beetle_Events"]==60
    assert result["original_woody_occurrence_rows_opened"]==402
    assert result["original_beetle_occurrence_rows_opened"]==539
    assert result["original_woody_coreid_join_fraction"]==1
    assert result["original_beetle_coreid_join_fraction"]==1
    assert result["old_v1_298_original_full_method_gate_remains_TERMINAL"]
    assert result["no_plot_IDs_coordinates_taxon_names_or_original_raw_records_exported"]
    assert result["new_confirmatory_systems"]==0
    assert result["GEB_scientific_HOLD"] and not result["eBird_used"]
    for secret in ("Woody shared","Beetle shared","TER_NFBF","tree-ter-"):
        assert secret not in json.dumps(result)

def test_invalid_beetle_original_source_taxon_join_is_stop():
    c,e,m=protocols()
    t,b=synthetic_event_fixture()
    source_only=evaluate(t,b,m,e)
    c["frozen_event_receipt"]["original_full_site_woody_beetle_crosswalk_sha256"]=source_only["full_original_tree_beetle_Event_crosswalk_SHA256"]
    c["frozen_event_receipt"]["selected_beetle_Event_coreids_sha256"]=source_only["selected_original_Event_coreids_sha256"]
    c["frozen_event_receipt"]["selected_tree_beetle_method_site_fingerprint"]=source_only["selected_cross_taxon_site_tree_beetle_method_fingerprint"]
    tw,bb=synthetic_occurrences(t,b)
    for k in range(30):bb[k]["source_coreid"]="bad-source-core-id"
    r=score_original(t,b,tw,bb,e,m,c)
    assert r["status"]=="STOP_FROZEN_ORIGINAL_TAXON_DATA_QUALITY"
    assert r["original_beetle_coreid_join_fraction"]<.98

def test_meta_xml_extension_only_reader_does_not_invent_taxon_rows():
    meta=('<?xml version="1.0"?>'
          '<archive xmlns="http://rs.tdwg.org/dwc/text/">'
          '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence">'
          '<files><location>occurrence.txt</location></files><coreid index="0"/>'
          '<field term="http://rs.tdwg.org/dwc/terms/scientificName" index="1"/>'
          '<field term="http://rs.tdwg.org/dwc/terms/taxonRank" index="2"/>'
          '</extension></archive>')
    fp=io.BytesIO()
    with zipfile.ZipFile(fp,"w") as z:
        z.writestr("meta.xml",meta)
        z.writestr("occurrence.txt","ID1\tTaxonus beata\tspecies\n")
    rows=original_occurrence_body(fp.getvalue())
    assert rows==[{"source_coreid":"ID1","scientificName":"Taxonus beata","taxonRank":"species"}]
