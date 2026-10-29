"""v1.327 source-free known-truth original 664 site×season Events and rich taxa.

Genuine test of PRE-RESPONSE 42 trap, 70 matched island×calendar-quarter
strata, all 893 original Event rows, 14922 source Occurrence rows; mock source
names are never exported. Both habitat double contrast and stop gates work
without opening original SLAM v1.7 biological observations.
"""
import copy,hashlib,json,sys,zipfile,io
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import slam_forest_habitat_original_origin_score_v1_327 as score
from slam_forest_original_event_habitat_gate_v1_326 import audit as event_audit
from slam_forest_habitat_original_origin_score_v1_327 import (
    guild_score,score_original,reconstruct_event_sample,category,original_occurrence_rows
)

SITES={"FLO":(4,3),"PIC":(6,4),"TER":(14,2),
       "FAI":(3,0),"GRA":(2,0),"SMG":(3,0),"SMR":(1,0)}
ISLAND_NAMES={"FLO":"Flores","PIC":"Pico","TER":"Terceira","FAI":"Faial",
              "GRA":"Graciosa","SMG":"São Miguel","SMR":"Santa Maria"}

def cfg():
    def rd(name):return json.loads((ROOT/"development"/name).read_text(encoding="utf-8"))
    return (
        rd("slam_forest_origin_habitat_response_protocol_v1_327.json"),
        rd("slam_forest_explicit_habitat_original_event_gate_v1_326.json"),
        rd("slam_42forest_habitat_event_receipt_freeze_v1_326.json")
    )

def example_events():
    habitat_sites={}
    for island,(native,altered) in SITES.items():
        entries=[]
        for idx in range(native+altered):
            cat="native forest" if idx<native else "mixed forest"
            entries.append((f"TEST_FOREST_{island}_{idx:02d}",cat,idx))
        habitat_sites[island]=entries
    events=[]
    def evt(island,sid,cat,idx,year,quarter,extra):
        point=sorted((s,i) for code,v in habitat_sites.items() for s,_,i in v).index((sid,idx))
        return {
          "__original_coreid":f"E-{island}-{sid}-{year}-Q{quarter}-{extra:03d}",
          "eventID":f"event-test-{island}-{sid}-{year}-Q{quarter}-{extra:03d}",
          "island":ISLAND_NAMES[island],
          "locationID":sid,
          "habitat":cat,
          "samplingProtocol":"SLAM trap",
          "eventDate":f"{year}-{(quarter-1)*3+1:02d}-15",
          "year":str(year),
          "decimalLatitude":str(38.0+point*.001),
          "decimalLongitude":str(-27.0-point*.001)
        }
    specs={"FLO":6,"PIC":30,"TER":34}
    for island,quarters in specs.items():
        nat,alt=SITES[island]
        for t in range(quarters):
            year=2014+t//4
            q=t%4+1
            if island=="TER":
                # 16 quarters with 8 native; 18 quarters with 7 native:
                # exactly 254 native + 68 altered = 322 original Events.
                native_n=8 if t<16 else 7
                selected_native=[
                    habitat_sites[island][(t+i)%nat] for i in range(native_n)
                ]
            else:
                selected_native=habitat_sites[island][:nat]
            altered=habitat_sites[island][nat:]
            for sid,cat,idx in selected_native+altered:
                events.append(evt(island,sid,cat,idx,year,q,0))
    assert len(events)==664
    outside=[(isl,entry) for isl in ("FAI","GRA","SMG","SMR")
             for entry in habitat_sites[isl]]
    assert len(outside)==9
    for island,(sid,cat,idx) in outside:
        events.append(evt(island,sid,cat,idx,2012,1,0))
    for j in range(220):
        island="FAI";sid,cat,idx=habitat_sites[island][0]
        events.append(evt(island,sid,cat,idx,2012,1,j+1))
    assert len(events)==893 and len(set(q["__original_coreid"] for q in events))==893
    return events

def synthetic_original(monkeypatch):
    study,event,receipt=cfg()
    events=example_events()
    source_meta=event_audit(events,event)
    assert source_meta["status"]=="ORIGINAL_SLAM_FOREST_HABITAT_STRATA_ELIGIBLE_TAXON_RESPONSES_SEALED"
    assert source_meta["source_selected_original_Event_rows_in_matched_habitat_strata"]==664
    assert source_meta["source_selected_physical_plots_with_matched_habitat_period_method"]==33
    ssha=source_meta["source_selected_original_Event_coreids_SHA256"]
    psha=source_meta["source_selected_original_physical_plot_key_SHA256"]
    monkeypatch.setattr(score,"SOURCE_SELECT_SHA",ssha)
    monkeypatch.setattr(score,"SOURCE_SITE_SHA",psha)
    receipt["selected_source_Event_coreid_SHA256"]=ssha
    receipt["selected_original_physical_plot_key_SHA256"]=psha
    receipt["original_sampling_protocol_sha256"]=source_meta["source_dominant_original_method_SHA256"]
    selected,windows=reconstruct_event_sample(events,event,receipt)
    assert len(selected)==664
    assert {i:len(windows[i]) for i in ("FLO","PIC","TER")}=={"FLO":6,"PIC":30,"TER":34}
    occurrences=[]
    for core,(_,_,_,_,group,_) in selected.items():
        for taxon,origin,order in (
            ("Endemic shared","endemic","Coleoptera"),
            ("Native shared","native","Araneae"),
            ("Introduced shared","introduced","Coleoptera"),
            ("Endemic extra","endemic","Coleoptera") if group=="native"
                else ("Introduced extra","introduced","Coleoptera"),
            ("Native extra","native","Araneae") if group=="native"
                else ("Introduced second extra","introduced","Coleoptera"),
        ):
            occurrences.append({
                "__foreign_event_coreid":core,
                "scientificName":taxon,
                "taxonRank":"species",
                "order":order,
                "establishmentMeans":origin
            })
    other=next(x["__original_coreid"] for x in events if x["island"]=="Faial")
    for _ in range(14922-len(occurrences)):
        occurrences.append({
            "__foreign_event_coreid":other,
            "scientificName":"OTHER_PLOT_ONLY",
            "taxonRank":"species",
            "order":"Coleoptera",
            "establishmentMeans":"native"
        })
    assert len(occurrences)==14922
    return events,occurrences,study,event,receipt

def test_three_island_664_source_sampling_known_truth_and_origin_habitat_contrast(monkeypatch):
    e,o,study,event,receipt=synthetic_original(monkeypatch)
    r=score_original(e,o,study,event,receipt)
    assert r["status"]=="SOURCE_OBSERVED_THREE_ISLAND_NATIVE_ALTERED_HABITAT_ORIGIN_CONTRAST_COMPLETE"
    assert r["source_original_Event_rows_reexamined"]==893
    assert r["source_original_Occurrence_rows_opened_once"]==14922
    assert r["original_selected_matched_source_Event_rows"]==664
    assert r["original_source_Event_Occurrence_join_fraction"]==1
    assert r["original_selected_source_Event_record_coverage_fraction"]==1
    assert r["source_origin_UNCLASSIFIED_fraction_selected_named_species"]==0
    main=r["main_all_arthropods"]
    assert main["status"]=="OBSERVED_ORIGIN_SPECIFIC_HABITAT_RICHNESS_CONTRAST"
    assert main["original_island_equal_season_mean"]["indigenous_richness_native_minus_altered"]==2
    assert main["original_island_equal_season_mean"]["introduced_richness_native_minus_altered"]==-2
    assert main["original_island_equal_season_mean"]["origin_habitat_double_contrast"]==4
    assert r["secondary_coleoptera"]["status"]=="OBSERVED_ORIGIN_SPECIFIC_HABITAT_RICHNESS_CONTRAST"
    assert r["secondary_coleoptera"]["original_island_equal_season_mean"]["origin_habitat_double_contrast"]>0
    assert "OTHER_PLOT_ONLY" not in json.dumps(r)
    assert "TEST_FOREST" not in json.dumps(r)
    assert r["GEB_scientific_HOLD"] and r["new_confirmatory_systems"]==0 and not r["eBird_used"]

def test_source_unclassified_origin_gt_20_percent_stops_without_changing_ontology(monkeypatch):
    e,o,study,event,receipt=synthetic_original(monkeypatch)
    for row in o[:1800]:
        row["establishmentMeans"]="source_unknown"
    r=score_original(e,o,study,event,receipt)
    assert r["status"]=="STOP_ORIGINAL_SPECIES_STATUS_OR_CAPTURE_QUALITY"
    assert r["source_origin_UNCLASSIFIED_fraction_selected_named_species"]>.2
    assert r["main_all_arthropods"] is None

def test_original_same_island_taxon_conflicting_origin_is_terminal(monkeypatch):
    e,o,study,event,receipt=synthetic_original(monkeypatch)
    o[0]["establishmentMeans"]="introduced"
    r=score_original(e,o,study,event,receipt)
    assert r["status"]=="STOP_ORIGINAL_SPECIES_STATUS_OR_CAPTURE_QUALITY"
    assert r["source_taxon_biogeographic_origin_conflicts_among_islands"]>=1
    assert r["main_all_arthropods"] is None

def test_original_source_identity_preflight_before_any_taxon_access(monkeypatch):
    e,o,study,event,receipt=synthetic_original(monkeypatch)
    receipt["selected_source_Event_coreid_SHA256"]="tampered"
    with pytest.raises(ValueError,match="fingerprint"):
        score_original(e,o,study,event,receipt)

def test_frozen_source_origin_taxonrank_rules():
    study,_,_=cfg()
    assert category("introduced",study)=="introduced"
    assert category("Native",study)=="native"
    assert category("Endemic",study)=="endemic"
    assert category("cryptic status not independently reported",study) is None

def test_synthetic_occurrence_DWCA_reader_parses_original_coreid_once():
    fields=["scientificName","taxonRank","order","establishmentMeans"]
    xml='<archive xmlns="http://rs.tdwg.org/dwc/text/"><extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence"><files><location>occ.txt</location></files><coreid index="0"/>'
    xml+=''.join(f'<field term="http://rs.tdwg.org/dwc/terms/{key}" index="{i}"/>' for i,key in enumerate(fields,1))
    xml+='</extension></archive>'
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
        z.writestr("meta.xml",xml)
        z.writestr("occ.txt","SOURCE_CORE_ID\\tTestus florus\\tspecies\\tColeoptera\\tendemic\n".replace("\\t","\t"))
    rows=original_occurrence_rows(buf.getvalue())
    assert rows==[{"__foreign_event_coreid":"SOURCE_CORE_ID","scientificName":"Testus florus",
                    "taxonRank":"species","order":"Coleoptera","establishmentMeans":"endemic"}]
