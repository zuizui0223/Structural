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


def test_manifest_published_saojorge_uses_bytes_key_pico_uses_expected_bytes():
    from azores_PRIBES_crossisland_field_v1_271 import locked_archive_size
    assert locked_archive_size({"bytes":261438})==261438
    assert locked_archive_size({"expected_bytes":568461})==568461
    assert locked_archive_size({"expected_bytes":568461,"bytes":568461})==568461
    for record in ({}, {"bytes":261438,"expected_bytes":261439}):
        try:
            locked_archive_size(record)
        except ValueError:
            pass
        else:
            raise AssertionError("Do not silently choose an unsupported/mismatched original source length")


def test_original_author_source_receipts_use_one_canonical_verified_size_access():
    from azores_PRIBES_crossisland_field_v1_271 import format_author_source_receipt
    data={"raw_event_rows":1655,"raw_occurrence_rows":4523,
          "valid_dated_event_rows":1655,"excluded_invalid_dates":0,
          "field_event_year_counts":{"2020":1655},
          "island_event_counts":{"São Jorge":1655},
          "valid_field_species_observations":4250,
          "excluded_occurrence_rows":{}}
    early={"url":"original","bytes":261438,"sha256":"older"}
    later={"url":"original","expected_bytes":568461,"sha256":"newer"}
    s=format_author_source_receipt("Sao Jorge PRIBES",early,data)
    p=format_author_source_receipt("Pico PRIBES",later,data)
    assert s["original_bytes"]==261438
    assert p["original_bytes"]==568461
    assert s["valid_dated_events"]==1655
    assert p["field_event_years"]=={"2020":1655}
    assert "field_taxa" not in s


def archive_pico_original_MDY_rows():
    ns="http://rs.tdwg.org/dwc/text/"
    term="http://rs.tdwg.org/dwc/terms/"
    meta=f'''<archive xmlns="{ns}">
        <core rowType="{term}Event" encoding="UTF-8" ignoreHeaderLines="1">
            <files><location>event.txt</location></files>
            <id index="0"/>
            <field index="1" term="{term}eventDate"/>
            <field index="2" term="{term}year"/>
            <field index="3" term="{term}month"/>
            <field index="4" term="{term}day"/>
            <field index="5" term="{term}island"/>
        </core>
        <extension rowType="{term}Occurrence" encoding="UTF-8" ignoreHeaderLines="1">
            <files><location>occurrence.txt</location></files>
            <coreid index="0"/>
            <field index="1" term="{term}scientificName"/>
            <field index="2" term="{term}taxonRank"/>
            <field index="3" term="{term}establishmentMeans"/>
        </extension>
    </archive>'''
    src=io.BytesIO()
    with zipfile.ZipFile(src,"w") as z:
        z.writestr("meta.xml",meta)
        z.writestr("event.txt",(
          "id\teventDate\tyear\tmonth\tday\tisland\n"
          "A\t8/11/2020\t2020\t8\t11\tPico\n"
          "B\t8/12/2020\t2020\t8\t12\tPico\n"
          "C\t8/13/2020\t2020\t11\t13\tPico\n"
        ))
        z.writestr("occurrence.txt",(
          "coreid\tscientificName\ttaxonRank\testablishmentMeans\n"
          "A\tAlpha alba\tspecies\tnative\n"
          "B\tAlpha alba\tspecies\tnative\n"
          "C\tNot reliable\tspecies\tnative\n"
        ))
    return src.getvalue()

def test_original_pico_MDY_recovery_requires_independent_author_components():
    r=read_dated_field(archive_pico_original_MDY_rows(),{"Pico"})
    assert r["raw_event_rows"]==3
    assert r["valid_dated_event_rows"]==2
    assert r["source_MDY_recovered_events"]==2
    assert r["excluded_invalid_dates"]==1
    assert r["field_event_year_counts"]=={"2020":2}
    assert r["unique_species_island_positive_pairs"]==1
    assert len(r["field_taxa"])==1
