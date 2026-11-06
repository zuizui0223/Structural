"""Synthetic only: BALA three-decade species replacement vs net richness change."""
from pathlib import Path
import json,sys,io,zipfile,math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from bala_original_species_replacement_v1_314 import (
    site_beta,_summary_by_guild_and_method,original_occurrence_rows
)

def test_balanced_species_replacement_despite_exact_same_richness():
    # Two lost species are balanced by two newly recorded species; net
    # richness change is zero but composition replacement is large.
    out=site_beta({"a","b","c"},{"a","d","e"})
    assert out["B1_richness"]==out["B3_richness"]==3
    assert out["net_species_richness_change"]==0
    assert out["shared_taxa"]==1
    assert out["B1_only_taxa"]==2 and out["B3_only_taxa"]==2
    assert out["balanced_replacement_taxon_incidence"]==4
    assert out["balanced_replacement_share"]==1
    assert math.isclose(out["sorensen_beta_total"],2/3)
    assert math.isclose(out["simpson_beta_replacement"],2/3)
    assert out["nestedness_related_component"]==0

def test_nestedness_dominant_species_loss_without_replacement():
    out=site_beta({"a","b","c"},{"a"})
    assert out["net_species_richness_change"]==-2
    assert out["balanced_replacement_taxon_incidence"]==0
    assert out["balanced_replacement_share"]==0
    assert out["simpson_beta_replacement"]==0
    assert math.isclose(out["nestedness_related_component"],0.5)
    assert site_beta(set(),{"a"}) is None
    assert site_beta(set(),set()) is None

def test_7_island_equal_weight_sampling_uses_site_not_trap_replicates():
    islands=["fai","flo","pic","sjg","smg","smr","ter"]
    sites=set((i,"site0") for i in islands)
    detected={}
    for island,site in sites:
        detected[(island,site,"Pitfall solution","araneae","B1")]={"a","b","c"}
        detected[(island,site,"Pitfall solution","araneae","B3")]={"a","d","e"}
    s=_summary_by_guild_and_method(
      detected,sites,"Pitfall solution","araneae","B1","B3")
    assert s["eligible_with_both_period_taxon_detections"]==7
    assert s["islands_with_at_least_one_valid_site"]==7
    assert s["island_equal_mean_balanced_replacement_share"]==1
    assert s["island_equal_mean_signed_net_richness_change"]==0
    assert math.isclose(s["island_equal_mean_simpson_replacement_beta"],2/3)
    assert s["total_sites_with_species_replacement_but_nearly_stable_richness"]==7
    assert "site0" not in json.dumps(s)

def test_source_DarwinCore_original_coreid_bridge_by_meta_indices():
    meta=('<archive xmlns="http://rs.tdwg.org/dwc/text/">'
       '<extension rowType="http://rs.tdwg.org/dwc/terms/Occurrence">'
       '<files><location>occurrence.txt</location></files><coreid index="0"/>'
       '<field index="1" term="http://rs.tdwg.org/dwc/terms/scientificName"/>'
       '<field index="2" term="http://rs.tdwg.org/dwc/terms/order"/>'
       '<field index="3" term="http://rs.tdwg.org/dwc/terms/taxonRank"/>'
       '<field index="4" term="http://rs.tdwg.org/dwc/terms/establishmentMeans"/>'
       '</extension></archive>')
    blob=io.BytesIO()
    with zipfile.ZipFile(blob,"w") as z:
        z.writestr("meta.xml",meta)
        z.writestr("occurrence.txt","source-id-1\tAraneae testia\tAraneae\tspecies\tendemic\n")
    rows=original_occurrence_rows(blob.getvalue())
    assert rows==[{"__foreign_coreid":"source-id-1","scientificName":"Araneae testia",
      "order":"Araneae","taxonRank":"species","establishmentMeans":"endemic"}]
