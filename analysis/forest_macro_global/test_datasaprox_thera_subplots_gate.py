"""Metadata-only THERA source-height physical hierarchy tests; never score taxa."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import datasaprox_thera_subplots_gate as t

def make():
    events={}
    extra={}
    for i in range(62):
        plot="PrivatePlot"+str(i%20)
        month="2024-"+str(i//20+1).zfill(2)
        for layer in ("upper","lower"):
            name="PrivateEvent"+str(i)+layer
            condition=("Lind noir Supra canopee" if layer=="upper"
                       else "Lind noir Infra canopee")
            key=(*t.TARGET,name)
            events[key]=(layer,plot,"lindgren","multi-funnel",condition,
                         "control","black",month,14)
            extra[key]={("SUBPLOT"+str(i),"TrapNum"+layer,"TrapName"+layer)}
    return events,extra

def test_original_thera_height_codes_and_same_subplots_are_only_design():
    events,extra=make()
    r=t.audit_subplots(events,set(),extra)
    assert r["status"]=="THERA_SOURCE_METHOD_METADATA_EVALUATED_AUTHOR_PROTOCOL_NOT_CONFIRMED"
    assert r["original_plot_month_method_bait_colour_effort_matched_strata"]==62
    assert r["distinct_original_THERA_plot_keys"]==20
    assert r["source_author_condition_labels_outside_exact_four_canopy_Lindgren_labels"]==0
    assert r["source_subplots_comparability_of_62_paired_strata"]["upper_lower_share_nonempty_author_subplots"]==62
    assert r["source_events_with_subplot_metadata"]==124
    assert r["publisher_original_THERA_independent_field_hierarchy_confirmed"] is False
    assert r["source_Thera_taxon_scoring_authorized"] is False
    assert "PrivatePlot" not in str(r)
    assert "PrivateEvent" not in str(r)
    assert "TrapName" not in str(r)

def test_subplots_disjoint_source_design_is_not_equivalent():
    events,extra=make()
    k=(*t.TARGET,"PrivateEvent0lower")
    extra[k]={("OTHER_SUBPLOT","num","name")}
    r=t.audit_subplots(events,set(),extra)
    assert r["source_subplots_comparability_of_62_paired_strata"]["both_subplots_nonempty_but_disjoint"]==1
    assert r["source_subplots_comparability_of_62_paired_strata"]["upper_lower_share_nonempty_author_subplots"]==61

def test_stratum_and_source_condition_code_mismatch_blocks_metadata_gate():
    events,extra=make()
    k=(*t.TARGET,"PrivateEvent0upper")
    v=list(events[k]);v[4]="generic treatment";events[k]=tuple(v)
    r=t.audit_subplots(events,set(),extra)
    assert r["source_author_condition_labels_outside_exact_four_canopy_Lindgren_labels"]==1
    assert r["source_Thera_taxon_scoring_authorized"] is False

def test_inconsistent_source_event_optional_subplot_metadata_excluded():
    events,extra=make()
    k=(*t.TARGET,"PrivateEvent0upper")
    extra[k].add(("DIFFERENT","num","name"))
    r=t.audit_subplots(events,set(),extra)
    assert r["status"]=="STOP_THERA_PROJECT_PAIR_DESIGN_DRIFT"
    assert r["original_species_values_read"] is False
