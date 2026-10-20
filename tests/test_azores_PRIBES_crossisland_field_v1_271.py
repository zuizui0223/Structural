"""New dated field Event+Occurrence archives for Pico, Graciosa and Santa Maria.

Synthetic original-source fixtures only; no protected biological outcomes.
"""
import io,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_PRIBES_crossisland_field_v1_271 import read_dated_field, synthesize_observations

NS="http://rs.tdwg.org/dwc/text/"
DWC="http://rs.tdwg.org/dwc/terms/"

def archive_for(events,occurrences):
    emet=[
        ("eventDate","eventDate"),("island","island"),
        ("habitat","habitat"),("samplingProtocol","samplingProtocol"),
    ]
    omet=[("scientificName","scientificName"),("taxonRank","taxonRank"),
          ("occurrenceStatus","occurrenceStatus"),
          ("establishmentMeans","establishmentMeans"),
          ("basisOfRecord","basisOfRecord")]
    xml=f'''<archive xmlns="{NS}">
      <core rowType="{DWC}Event" encoding="UTF-8" ignoreHeaderLines="1">
        <files><location>event.txt</location></files><id index="0"/>
        {''.join(f'<field index="{n+1}" term="{DWC}{term}"/>' for n,(_,term) in enumerate(emet))}
      </core>
      <extension rowType="{DWC}Occurrence" encoding="UTF-8" ignoreHeaderLines="1">
        <files><location>occurrence.txt</location></files><coreid index="0"/>
        {''.join(f'<field index="{n+1}" term="{DWC}{term}"/>' for n,(_,term) in enumerate(omet))}
      </extension></archive>'''
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr("meta.xml",xml)
        z.writestr("event.txt","id\teventDate\tisland\thabitat\tsamplingProtocol\n" +
                    "".join("\t".join(map(str,e))+"\n" for e in events))
        z.writestr("occurrence.txt",
                   "coreid\tscientificName\ttaxonRank\toccurrenceStatus\testablishmentMeans\tbasisOfRecord\n"+
                   "".join("\t".join(map(str,occ))+"\n" for occ in occurrences))
    return b.getvalue()

def S1(name,island):
    return {"Species":name,"Island":island,"Archipelago":"Azores",
            "Extinction category":"Extirpation (Island level)",
            "Category":"Well-supported","Date":"1890"}

def sample_sources():
    pico=archive_for(
        [("a","2020-07-21","Pico","forest","trap"),
         ("b","2021-06-05","Pico","forest","trap"),
         ("c","2010","Pico","forest","trap")],
        [("a","Alpha alba","species","present","native","HumanObservation"),
         ("b","Beta beta","species","present","native","HumanObservation"),
         ("c","Never nominal","species","present","native","HumanObservation"),
         ("a","Excluded unknown","variety","present","native","HumanObservation"),
         ("a","Alpha alba","species","absent","native","HumanObservation")]
    )
    both=archive_for(
        [("g","2020-08-03","Graciosa","field","sweep"),
         ("s","2020-08-04","Santa Maria","field","sweep"),
         ("bad","2020-08-08","Pico","field","sweep")],
        [("g","Alpha alba","species","present","native","HumanObservation"),
         ("s","Gamma gamma","species","present","native","HumanObservation"),
         ("bad","Alpha alba","species","present","native","HumanObservation"),
         ("g","Unlinked unrelated","species","present","introduced","HumanObservation")])
    return pico,both

def test_event_to_occurrence_id_binding_and_day_level_island_validation():
    p,b=sample_sources()
    x=read_dated_field(p,{"Pico"})
    assert x["raw_event_rows"]==3
    assert x["valid_dated_event_rows"]==2
    assert x["excluded_invalid_dates"]==1
    assert x["valid_field_species_observations"]==2
    assert x["field_event_year_counts"]=={"2020":1,"2021":1}
    assert len(x["field_taxa"])==2
    try:
        read_dated_field(b,{"Graciosa","Santa Maria"})
    except ValueError as e:
        assert "island" in str(e).lower()
    else:
        raise AssertionError("Unknown third island in 2-island author archive must be rejected")

def test_two_island_source_preserves_distinct_island_and_deduplicates_same_taxon_island():
    both=archive_for(
        [("g","2020-08-03","Graciosa","forest","sweep"),
         ("s","2020-08-04","Santa Maria","forest","sweep")],
        [("g","Alpha alba","species","present","native","HumanObservation"),
         ("g","Alpha alba","species","present","native","HumanObservation"),
         ("s","Beta beta","species","present","native","HumanObservation")])
    x=read_dated_field(both,{"Graciosa","Santa Maria"})
    assert x["raw_occurrence_rows"]==3
    assert len(x["field_taxa"])==2
    assert x["island_event_counts"]=={"Graciosa":1,"Santa Maria":1}
    assert x["unique_species_island_positive_pairs"]==2

def test_cross_island_one_loss_case_other_field_positive_not_recolonization():
    p=archive_for([("p","2020-07-21","Pico","forest","trap")],
                  [("p","Alpha alba","species","present","native","HumanObservation")])
    g=archive_for([("g","2020-08-03","Graciosa","forest","sweep"),
                   ("s","2020-08-04","Santa Maria","forest","sweep")],
                  [("g","Alpha alba","species","present","native","HumanObservation"),
                   ("s","Gamma gamma","species","present","native","HumanObservation")])
    summaries={
        "Pico":read_dated_field(p,{"Pico"}),
        "Graciosa and Santa Maria":read_dated_field(g,{"Graciosa","Santa Maria"})
    }
    losses=[S1("Alpha alba","São Jorge"),S1("Beta beta","Pico"),
            S1("Gamma gamma","Santa Maria")]
    result=synthesize_observations(summaries,losses,{"Pico","Graciosa","Santa Maria"})
    assert result["S1_strict_azores_taxa_in_synthetic_loss_input"]==3
    assert result["S1_taxa_with_dated_field_detection_on_other_island"]==1
    assert result["S1_cases_same_island_dated_field_detection"]==1
    assert result["S1_taxa_with_dated_field_positive_on_2plus_islands"]==1
    assert result["unrecorded_taxa_are_never_negative_labels"] is True
    assert result["confirmed_demographic_recolonization_events"]==0
    assert "Alpha alba" not in str(result)
    assert "Beta beta" not in str(result)
