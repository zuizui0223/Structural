"""Historical local-loss taxon recurrence on Pico within true author-dated years."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from azores_Pico_repeated_field_positives_v1_274 import repeated_pico_detection

def S1(name,island="São Jorge",certainty="Well-supported",status="Extirpation (Island level)"):
    return {"Species":name,"Island":island,"Archipelago":"Azores",
            "Category":certainty,"Extinction category":status}

def obs(name,year,island="Pico",native=True):
    return {"name":name,"island":island,"year":year,"native":native}

def test_two_or_three_year_positive_taxa_not_conflated_with_population_recolonization():
    field={
       "Pico PRIBES":{"field_taxa":[
            obs("alpha alba",2020),obs("alpha alba",2021),obs("alpha alba",2024),
            obs("beta beta",2024),
            obs("gamma gamma",2020),obs("gamma gamma",2021),
            obs("gamma gamma",2021),
            obs("unrelated",2022)
       ]},
       "Other":{"field_taxa":[obs("delta delta",2019,"Graciosa")]}
    }
    losses=[S1("Alpha alba"),S1("Beta beta"),S1("Gamma gamma"),S1("Delta delta")]
    r=repeated_pico_detection(field,losses)
    assert r["historically_loss_affected_Azores_taxa"]==4
    assert r["historically_loss_affected_taxa_seen_on_Pico"]==3
    assert r["historic_loss_taxa_seen_in_2plus_Pico_years"]==2
    assert r["historic_loss_taxa_seen_in_3plus_Pico_years"]==1
    assert r["historic_loss_taxa_seen_in_4_Pico_years"]==0
    assert r["Pico_positive_taxa_by_number_of_survey_years"]=={"1":1,"2":1,"3":1}
    assert r["per_Pico_year_historic_loss_taxa_positive"]=={"2020":2,"2021":2,"2024":2}
    assert r["not_population_persistence_or_colonization"] is True
    assert "alpha alba" not in str(r)

def test_no_pico_observation_returns_unknown_not_surveyed_absence():
    r=repeated_pico_detection({"Pico PRIBES":{"field_taxa":[]}},[S1("Alpha alba")])
    assert r["historically_loss_affected_taxa_seen_on_Pico"]==0
    assert r["missing_Pico_taxa_record_is_not_confirmed_absence"] is True
    assert r["per_Pico_year_historic_loss_taxa_positive"]=={}
