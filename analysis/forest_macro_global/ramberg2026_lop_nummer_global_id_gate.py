#!/usr/bin/env python3
"""Ramberg 2026 exact author Lop_nummer ↔ 150 beetle species-header column IDs.

Reads source author physical/effort metadata ONLY, Species FIRST HEADER ROW
ONLY. No original beetle abundance cells, taxon names/values, or regressions.
"""
import argparse, collections, io, json, re, zipfile
from pathlib import Path
import ramberg2026_zenodo_xlsx_firstheader_only as original
import ramberg2026_original_sample_identity_only as prior

FIELDS={"Lop_nummer","sample id","Pair_number","Site_code","Type","tree_species",
        "age","stump_diameter","stump_height","bark_coverage",
        "ground_moisture","sunexposure_stump","date"}

def run():
    raw=original.original_file()  # Publisher original SHA + MD5 + 56,235B enforced.
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        sheets=original.sheet_paths(z)
        hs=prior.original_row1(z,sheets["Samples"])
        hb=prior.original_row1(z,sheets["Species"])
        if len(hs)!=18 or len(hb)!=153:
            raise ValueError("SOURCE_HEADER_FIELDS_DIMENSIONS_STOP")
        refs={v for _,t,v in hs if t=="s"}
        shared=original.selected_sharedstrings(z,refs)
        names={c:prior.to_label((t,v),shared) for c,t,v in hs}
        cols={col:name for col,name in names.items() if name in FIELDS}
        if not {"Lop_nummer","sample id","Pair_number","Site_code","Type","tree_species"}.issubset(cols.values()):
            raise ValueError("SOURCE_REQUIRED_AUTHOR_GLOBAL_ID_FIELDS_NOT_PRESENT")
        if len(cols)!=len(set(cols.values())):
            raise ValueError("SOURCE_AUTHOR_DUPLICATE_METHOD_FIELD_NAMES")
        if any(t!="n" for _,t,_ in hb[3:]):
            raise ValueError("SOURCE_SPECIES_150_HEADER_NUMBER_TYPE_STOP")
        skeys=[prior.to_label((t,v),{}) for _,t,v in hb[3:]]
        if len(skeys)!=150 or any(not a for a in skeys) or len(set(skeys))!=150:
            raise ValueError("SOURCE_SPECIES_NUMERIC_SAMPLE_HEADERS_NOT_UNIQUE")
        rows,nxml=prior.read_samples_allowlisted_values(z,sheets["Samples"],cols)
        sst={val for row in rows for t,val in row.values() if t=="s"}
        vals=original.selected_sharedstrings(z,sst)
        records=[{field:prior.to_label(row.get(field,("str","")),vals)
                  for field in cols.values()} for row in rows]
    # Original field 'sample id' identifies local stump (within stand).
    sites=[x for x in records if x.get("sample id")]
    if len(sites)!=150:
        raise ValueError("SOURCE_ORIGINAL_SITE_LOCAL_SAMPLE_FRAME_UNEXPECTED")
    ids=[x.get("Lop_nummer","") for x in sites]
    freq=collections.Counter(ids)
    unique_ids=set(ids)-{""}
    species_set=set(skeys)
    matched=unique_ids&species_set
    matched_source=[row for row in sites if row.get("Lop_nummer") in matched]
    pair_ids=collections.Counter(row["Pair_number"] for row in matched_source)
    stand_ids=collections.Counter(row["Site_code"] for row in matched_source)
    pairs_per_stand=collections.defaultdict(set)
    types_per_pair=collections.defaultdict(set)
    pair_per_stand=collections.defaultdict(set)
    source_composite=collections.Counter()
    for row in matched_source:
        pairs_per_stand[row["Site_code"]].add(row["Pair_number"])
        pair_per_stand[row["Site_code"]].add(row["Pair_number"])
        types_per_pair[row["Pair_number"]].add(row["Type"])
        source_composite[(row["Site_code"],row["sample id"])]+=1
    observed_tree_types=set(row["tree_species"] for row in matched_source if row["tree_species"])
    n_missing_by_field={field:sum(
        row.get(field,"").strip().lower() in ("","na","nan","null","#n/a")
        for row in matched_source)
        for field in FIELDS}
    ids_ok=(
        len(skeys)==150 and len(matched)==150 and len(unique_ids)==150 and
        not (species_set-unique_ids) and not (unique_ids-species_set) and
        all(f==1 for f in freq.values()) and "" not in freq
    )
    hierarchy_ok=(
        len(pair_ids)==5 and len(stand_ids)==10 and
        all(v==30 for v in pair_ids.values()) and
        all(v==15 for v in stand_ids.values()) and
        all(len(v)==1 for v in pair_per_stand.values()) and
        all(len(v)==2 for v in types_per_pair.values()) and
        len(observed_tree_types)==1 and len(source_composite)==150 and
        all(v==1 for v in source_composite.values())
    )
    required_no_missing=all(n_missing_by_field[k]==0 for k in
        ("Lop_nummer","sample id","Pair_number","Site_code","Type","tree_species"))
    full=ids_ok and hierarchy_ok and required_no_missing
    return {
      "status":("SOURCE_AUTHOR_LOP_NUMMER_150_EXACT_STUMP_SPECIES_COLUMN_IDENTITY_PASS_NO_BIOLOGY"
                if full else "SOURCE_AUTHOR_GLOBAL_SAMPLE_ID_OR_HIERARCHY_HOLD_NO_BIOLOGY"),
      "original_samples_xml_data_rows":nxml,
      "original_site_local_sample_field_rows":len(sites),
      "n_species_matrix_150_sample_header_keys":len(skeys),
      "n_original_samples_author_global_serial_ids":len(unique_ids),
      "n_original_samples_global_serial_duplicates":sum(v>1 for v in freq.values()),
      "n_exact_author_Lop_nummer_vs_Species_header_ID_matches":len(matched),
      "n_species_headers_without_source_Lop_nummer":len(species_set-unique_ids),
      "n_original_Lop_nummer_without_species_header":len(unique_ids-species_set),
      "n_parent_Pair_number":len(pair_ids),
      "n_parent_Site_code":len(stand_ids),
      "per_pair_matched_stump_range":([min(pair_ids.values()),max(pair_ids.values())] if pair_ids else []),
      "per_stand_matched_stump_range":([min(stand_ids.values()),max(stand_ids.values())] if stand_ids else []),
      "every_stand_in_exactly_one_source_pair":bool(all(len(v)==1 for v in pair_per_stand.values())),
      "every_pair_has_two_type_categories":bool(all(len(v)==2 for v in types_per_pair.values())),
      "n_unique_original_tree_species":len(observed_tree_types),
      "n_unique_stand_and_local_sample_id_composites":len(source_composite),
      "nonresponse_method_field_missing_counts":{k:n_missing_by_field[k] for k in sorted(FIELDS)},
      "author_serial_and_parent_ID_gate_pass":full,
      "raw_sample_stump_site_or_taxon_names_released":False,
      "read_original_Species_observation_or_abundance_rows":0,
      "new_biological_effects_computed":0
    }

def test():
    assert len(FIELDS)==13
    assert {"Lop_nummer","Type","bark_coverage"}.issubset(FIELDS)
    assert prior.to_label(("n","101.0"),{})=="101"
    print("RAMBERG2026_GLOBAL_AUTHOR_SERIAL_KEY_KNOWN_TRUTH_PASS")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",default="ramberg2026_global_serial_id_sourceonly/receipt.json")
    args=ap.parse_args()
    test()
    if not args.test:
        receipt={"schema":"structural.ramberg2026_author_lop_nummer_source_global_join.v1",
          "official_original_file_sha256":original.SHA,
          "sample_id_prior_15_of_150_failure_unmodified":True,
          "original_species_abundance_numeric_rows_read":0,
          "new_ecological_effects":0,
          "status":"SOURCE_GLOBAL_KEY_IDENTITY_UNOPENED"}
        try:
            o=run();receipt["source_identity"]=o;receipt["status"]=o["status"]
        except Exception as e:
            receipt["status"]="SOURCE_ORIGINAL_GLOBAL_KEY_SCHEMA_OR_TRANSPORT_STOP"
            receipt["error_type"]=type(e).__name__
            receipt["error_code"]=str(e)[:125] if isinstance(e,ValueError) else ""
        dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(json.dumps(receipt,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
        print("ORIGINAL_GLOBAL_STUMP_ID_GATE",receipt["status"])
        print("ORIGINAL_SPECIES_ABUNDANCE_ROWS_OPENED",receipt["original_species_abundance_numeric_rows_read"])
