#!/usr/bin/env python3
"""Pure response-opaque external validation support gate."""
import argparse,json
from pathlib import Path
def adjudicate(taxa,sites,geo):
 if taxa["exact_shared_species_count"]!=len(taxa["matched_species"]):
  raise ValueError("Taxon corrected evidence internally inconsistent")
 t=taxa["exact_shared_species_count"]
 g=geo["result"]
 n=g["original_heldout_islands_4126_in_box"]
 b=g["geographical_heldout_blocks"]
 named=g["island_site_codes_of_39_surveyed_mapped_to_original_heldout"]
 if (t,n,b,named)!=(5,3,1,0):
  raise ValueError("Frozen v1.233 source evidence differs")
 if sites["source"]["internal_island_codes"]!=[
   "s"+str(i).zfill(2) for i in range(1,40)]:
  raise ValueError("Frozen 39 site codes changed")
 if g["max_possible_taxon_island_pairs_at_five_verified_taxa"]!=t*n:
  raise ValueError("Product bound does not match source identity")
 return {
 "schema":"structural.external_mammal_response_safe_support_result.v1_234",
 "status":"STOP_DIRECT_ORIGINAL_529_MAMMAL_FIELD_SCORE_SUPPORT_INSUFFICIENT",
 "published_field_study":"Zhan 2024 Zhoushan 39 marine island mammals",
 "frozen_exact_species_overlap":t,
 "regional_original_selected_islands":g["selected_model_islands_5401_in_box"],
 "regional_original_heldout_islands":n,
 "independent_geographic_heldout_blocks":b,
 "crosswalk_verified_study_sites":named,
 "current_scoring_cells_with_verified_taxon_and_island":0,
 "maximum_if_all_regional_original_heldout_islands_matched":t*n,
 "can_measure_between_geographic_block_replicability":b>=2,
 "read_field_species_by_island_values":False,
 "opened_original_mammal_heldout_species_values":False,
 "can_admit_direct_original_model_validation":False,
 "statement":"No evidence for or against model performance; sample-frame eligibility STOP only."
 }
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("taxa",type=Path);p.add_argument("sites",type=Path)
 p.add_argument("geography",type=Path);p.add_argument("--out",type=Path,required=True)
 a=p.parse_args();result=adjudicate(json.loads(a.taxa.read_text()),
    json.loads(a.sites.read_text()),json.loads(a.geography.read_text()))
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
 print(json.dumps(result,sort_keys=True))
