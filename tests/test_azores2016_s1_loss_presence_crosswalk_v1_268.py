"""Synthetic-only cross-source 2016 island checklist vs Macaronesian S1 loss audit."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores2016_s1_loss_presence_crosswalk_v1_268 import (
    normalized_locality,canonical_binomial,summary_join)


def tax(i,name,rank="species",phylum="Magnoliophyta"):
    return {"taxonID":str(i),"scientificName":name,"taxonRank":rank,
            "kingdom":"Plantae","phylum":phylum,
            "acceptedNameUsageID":str(i)}

def occur(i,place,status="present",means="native"):
    return {"taxonID":str(i),"locality":place,
            "occurrenceStatus":status,"establishmentMeans":means,
            "countryCode":"PT","eventDate":""}

def loss(name,island,arch="Azores",confidence="Well-supported",
         outcome="Extirpation (Island level)"):
    return {"Species":name,"Island":island,"Archipelago":arch,
            "Category":confidence,"Extinction category":outcome,"Date":"1898"}

def fixture():
    taxa=[
      tax(1,"Alpha alba L."),
      tax(2,"Beta beta"),
      tax(3,"Gamma gamma"),
      tax(4,"Epsilon epsilo","subspecies"),
      tax(5,"Alpha minor"),
    ]
    observations=[
      occur(1,"Azores"),occur(1,"Flores"),occur(1,"Pico"),
      occur(1,"Pico","absent"),occur(1,"Terceira",means="introduced"),
      occur(2,"Santa Maria"),occur(2,"Faial","absent"),
      occur(3,"São Miguel",status="absent"),occur(3,"Pico / Faial"),
      occur(4,"Faial"),
      occur(5,"São Jorge"),
    ]
    lost=[
      loss("Alpha alba","Pico"), loss("Alpha alba","São Jorge"),
      loss("Beta beta","Faial"),
      loss("Gamma gamma","Terceira"),
    ]
    return taxa,observations,lost

def test_normalize_single_island_no_fake_archipelago_or_multi_island():
    assert normalized_locality("Pico")=="Pico"
    assert normalized_locality(" Ilha de São Jorge ")=="São Jorge"
    assert normalized_locality("Sao Miguel Island")=="São Miguel"
    assert normalized_locality("Azores - Terceira")=="Terceira"
    assert normalized_locality("Azores") is None
    assert normalized_locality("Pico / Faial") is None
    assert normalized_locality("Pico, Flores") is None

def test_canonical_binomial_requires_true_genus_species():
    assert canonical_binomial("Alpha alba L.")=="alpha alba"
    assert canonical_binomial("Alpha alba1")=="alpha alba" # frozen citation-digit sensitivity
    assert canonical_binomial("Alpha sp.") is None
    assert canonical_binomial("Unknown") is None

def test_detects_published_survivor_elsewhere_and_same_island_status_conflict():
    taxa,records,losses=fixture()
    x=summary_join(taxa,records,losses)
    assert x["strict_S1_azores_source_loss_pairs"]==4
    assert x["strict_S1_azores_source_taxa"]==3
    assert x["S1_taxa_uniquely_joined_to_2016_species"]==3
    assert x["confirmed_native_other_island_present_loss_taxa"]==2
    assert x["confirmed_other_island_present_loss_taxa"]==2
    assert x["loss_pairs_with_2016_same_island_present"]==1
    assert x["current_present_species_island_pairs"]==5
    assert x["current_present_island_located_native_species_pairs"]==4
    assert x["unlocated_archipelago_distribution_rows"]==1
    assert x["multi_island_or_ambiguous_locality_rows"]>=1
    assert x["2016_missing_is_never_filled_as_absent"] is True
    assert "Alpha alba" not in str(x)
    assert "Beta beta" not in str(x)

def test_ambiguous_2016_taxonomy_is_never_force_merged():
    taxa,records,losses=fixture()
    taxa.append(tax(10,"Alpha alba Smith"))
    records.append(occur(10,"Graciosa"))
    x=summary_join(taxa,records,losses)
    assert x["S1_taxa_uniquely_joined_to_2016_species"]==2
    assert x["S1_taxa_with_ambiguous_2016_species_identity"]==1
    assert x["confirmed_other_island_present_loss_taxa"]==1
    assert x["no_manual_synonym_or_fuzzy_matching"] is True

def test_extinct_and_doubtful_cases_do_not_expand_loss_denominator():
    taxa,records,losses=fixture()
    losses.extend([
       loss("Epsilon epsilo","Faial",confidence="Doubtful"),
       loss("Alpha alba","Graciosa",outcome="Globally extinct"),
       loss("Beta beta","Pico",arch="Canary Islands"),
    ])
    x=summary_join(taxa,records,losses)
    assert x["strict_S1_azores_source_loss_pairs"]==4
    assert x["strict_S1_azores_source_taxa"]==3

def test_malformed_duplicate_taxon_ID_cannot_be_assigned_opportunistically():
    taxa,records,losses=fixture()
    taxa.append(tax(1,"Different different"))
    try:
       summary_join(taxa,records,losses)
    except ValueError as exc:
       assert "Duplicate" in str(exc)
    else:
       raise AssertionError("Must not choose conflicting name on same taxonID")


def test_author_dwca_coreid_links_extension_not_different_taxonid_field():
    """Darwin Core extension coreid points to core ID index 0, not taxonID index 1."""
    import zipfile,io
    from azores2016_s1_loss_presence_crosswalk_v1_268 import _read_author_tables
    core_ns="http://rs.tdwg.org/dwc/terms/"
    dist_ns="http://rs.gbif.org/terms/1.0/"
    xml='''<?xml version="1.0"?>
<archive xmlns="http://rs.tdwg.org/dwc/text/">
  <core rowType="http://rs.tdwg.org/dwc/terms/Taxon" encoding="UTF-8" ignoreHeaderLines="1">
    <files><location>taxon.txt</location></files><id index="0"/>
    <field index="1" term="'''+core_ns+'''taxonID"/>
    <field index="2" term="'''+core_ns+'''scientificName"/>
    <field index="3" term="'''+core_ns+'''kingdom"/>
    <field index="4" term="'''+core_ns+'''phylum"/>
    <field index="5" term="'''+core_ns+'''taxonRank"/>
    <field index="6" term="'''+core_ns+'''acceptedNameUsageID"/>
  </core>
  <extension rowType="'''+dist_ns+'''Distribution" encoding="UTF-8" ignoreHeaderLines="1">
    <files><location>distribution.txt</location></files><coreid index="0"/>
    <field index="1" term="'''+core_ns+'''locality"/>
    <field index="2" term="'''+core_ns+'''occurrenceStatus"/>
    <field index="3" term="'''+core_ns+'''establishmentMeans"/>
    <field index="4" term="'''+core_ns+'''eventDate"/>
  </extension>
</archive>'''
    b=io.BytesIO()
    with zipfile.ZipFile(b,"w") as z:
        z.writestr("meta.xml",xml)
        z.writestr("taxon.txt",
                   ("id\\ttaxonID\\tscientificName\\tkingdom\\tphylum\\trank\\taccepted\\n"
                    "CORE-101\\tDIFFERENT-999\\tAlpha alba L.\\tPlantae\\tMagnoliophyta\\tspecies\\tCORE-101\\n").replace("\\t","\t").replace("\\n","\n"))
        z.writestr("distribution.txt",
                   ("coreid\\tlocality\\toccurrenceStatus\\testablishmentMeans\\teventDate\\n"
                    "CORE-101\\tFlores\\tpresent\\tnative\\t\\n").replace("\\t","\t").replace("\\n","\n"))
    taxa,distributions,keys=_read_author_tables(b.getvalue())
    assert taxa[0]["taxonID"]=="CORE-101"
    assert distributions[0]["taxonID"]=="CORE-101"
    assert keys["published_taxonID_field_differs_from_coreid"]==1
    result=summary_join(taxa,distributions,[loss("Alpha alba","Pico")])
    assert result["confirmed_other_island_present_loss_taxa"]==1
    assert result["strict_S1_azores_source_taxa"]==1


def test_last_record_year_not_conflated_with_2016_date_of_live_population():
    taxa,records,losses=fixture()
    x=summary_join(taxa,records,losses)
    assert x["loss_pairs_with_2016_same_island_present"]==1
    assert x["2016_same_island_present_source_records_without_eventDate"]>=1
    assert x["same_island_2016_present_and_S1_last_record_pre_2010"]==1
    assert x["2016_published_present_is_not_confirmed_contemporaneous_survival"] is True

def test_explicit_eventdate_is_not_silently_filled_from_publication_year():
    taxa,records,losses=fixture()
    for x in records:x["eventDate"]=""
    records[1]["eventDate"]="2008-06-12"
    x=summary_join(taxa,records,losses)
    assert x["all_2016_distribution_rows_with_explicit_eventDate"]==1
    assert x["2016_published_present_is_not_confirmed_contemporaneous_survival"] is True


def test_archive_eventdate_vocabulary_prevents_assuming_one_observation_year():
    taxa,records,losses=fixture()
    for rec in records:rec["eventDate"]="2010-01-01"
    records[1]["eventDate"]="2008-06-12"
    x=summary_join(taxa,records,losses)
    assert x["all_2016_distribution_rows_with_explicit_eventDate"]==len(records)
    assert x["source_eventDate_values_top"][0]=={"date":"2010-01-01","count":len(records)-1}
    assert {"date":"2008-06-12","count":1} in x["source_eventDate_values_top"]
    assert x["S1_loss_island_published_present_eventDate_values"]=={"2010-01-01":1}
    assert x["2016_published_present_is_not_confirmed_contemporaneous_survival"] is True
