#!/usr/bin/env python3
"""Frozen 2026 Ramberg Zenodo original Samples IDs <-> Species HEADER ID gate.

Reads only original source Samples physical method/ID columns and Species FIRST
HEADER ROW numeric sample-column keys. Reads ZERO Species organism/taxon rows.
No original sample IDs or site names exported; source-only anonymous counts.
"""
import argparse, collections, io, json, re, xml.etree.ElementTree as ET, zipfile
from pathlib import Path
import ramberg2026_zenodo_xlsx_firstheader_only as base

MAIN="{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
ALLOW={
    "sample id","Pair_number","Site_code","site_name","tree_species",
    "age","stump_diameter","stump_height","sunexposure_stump","date",
}
REQUIRED={"sample id","Pair_number","Site_code","tree_species"}

def col_letters(ref):
    m=re.fullmatch(r"([A-Z]+)\d+",ref)
    if not m:raise ValueError("SOURCE_CELL_COORDINATE_FORMAT_STOP")
    return m.group(1)

def original_row1(z,path):
    with z.open(path) as fh:
        for _,element in ET.iterparse(fh,events=("end",)):
            if element.tag != MAIN+"row": continue
            if element.attrib.get("r")!="1":
                raise ValueError("SOURCE_AUTHOR_ROW1_HEADER_NOT_PRESENT")
            cells=[]
            for cell in element.findall(MAIN+"c"):
                t=cell.attrib.get("t","n")
                x=cell.find(MAIN+"v")
                if t=="s":
                    if x is None or not (x.text or "").isdigit():
                        raise ValueError("SOURCE_SST_HEADER_REFERENCE_STOP")
                    v=int(x.text)
                elif t=="inlineStr":
                    v="".join(e.text or "" for e in cell.iter(MAIN+"t"))
                elif t=="n":
                    v=(x.text or "") if x is not None else ""
                else:
                    v=""
                cells.append((col_letters(cell.attrib.get("r","")),t,v))
            return cells
    raise ValueError("SOURCE_ROW1_HEADER_MISSING")

def read_samples_allowlisted_values(z,path,allow_cols):
    # Only explicitly source-frozen METHOD columns; do not read all cells.
    source=[]
    nrows=0
    with z.open(path) as fh:
        for _,element in ET.iterparse(fh,events=("end",)):
            if element.tag!=MAIN+"row":continue
            rownum=element.attrib.get("r")
            if not rownum or not rownum.isdigit():
                raise ValueError("SOURCE_EXCEL_ROW_NUMBER_MALFORMED")
            if int(rownum)<=1:
                element.clear()
                continue
            nrows+=1
            vals={}
            for cell in element.findall(MAIN+"c"):
                key=col_letters(cell.attrib.get("r",""))
                if key not in allow_cols:
                    continue
                typ=cell.attrib.get("t","n")
                if typ not in ("s","n","str","inlineStr"):
                    raise ValueError("SOURCE_NONRESPONSE_METHOD_TYPE_STOP")
                value=cell.find(MAIN+"v")
                if typ=="s":
                    if value is None or not (value.text or "").isdigit():
                        raise ValueError("SOURCE_METHOD_SST_INDEX_STOP")
                    v=int(value.text)
                elif typ=="inlineStr":
                    v="".join(t.text or "" for t in cell.iter(MAIN+"t"))
                else:
                    v=value.text if value is not None and value.text is not None else ""
                vals[allow_cols[key]]=(typ,v)
            source.append(vals)
            element.clear()
    return source,nrows

def to_label(value,shared):
    typ,val=value
    if typ=="s":
        return shared.get(val,"").strip()
    s=str(val).strip()
    if typ=="n" and re.fullmatch(r"[0-9]+(?:\.0+)?",s):
        return str(int(float(s)))
    return s

def score_source_keys(binary):
    with zipfile.ZipFile(io.BytesIO(binary)) as z:
        paths=base.sheet_paths(z)
        samp_header=original_row1(z,paths["Samples"])
        species_header=original_row1(z,paths["Species"])
        if len(samp_header)!=18 or len(species_header)!=153:
            raise ValueError("SOURCE_AUTHOR_HEADER_DIMENSION_STOP")
        hdr_sst=({value for _,t,value in samp_header if t=="s"} |
                 {value for _,t,value in species_header[:3] if t=="s"})
        hdr_shared=base.selected_sharedstrings(z,hdr_sst)
        names={c:to_label((t,v),hdr_shared) for c,t,v in samp_header}
        colmap={c:name for c,name in names.items() if name in ALLOW}
        if set(names.values()) & REQUIRED != REQUIRED:
            raise ValueError("SOURCE_REQUIRED_METHOD_FIELDS_MISSING_STOP")
        if len(colmap)!=len(set(colmap.values())):
            raise ValueError("SOURCE_METHOD_FIELDS_NONUNIQUE_STOP")
        spprefix=species_header[:3]
        spids=species_header[3:]
        if len(spids)!=150 or any(t!="n" for _,t,_ in spids):
            raise ValueError("SOURCE_ORIGINAL_SPECIES_COL_ID_SCHEMA_STOP")
        spid=[to_label((t,v),{}) for _,t,v in spids]
        if any(not value or value=="nan" for value in spid) or len(set(spid))!=150:
            raise ValueError("SOURCE_ORIGINAL_SPECIES_SAMPLE_IDS_NONUNIQUE_STOP")
        original_rows,nrows=read_samples_allowlisted_values(z,paths["Samples"],colmap)
        needed={v for row in original_rows for t,v in row.values() if t=="s"}
        meta_shared=base.selected_sharedstrings(z,needed)
        resolved=[{key:to_label(row.get(key,("str","")),meta_shared)
                   for key in colmap.values()} for row in original_rows]
    nonempty=[x for x in resolved if x["sample id"]]
    keycounts=collections.Counter(x["sample id"] for x in nonempty)
    duplicates={key for key,n in keycounts.items() if n>1}
    keyset=set(keycounts)
    spkeys=set(spid)
    matched=spkeys&keyset
    mapped=[row for row in nonempty if row["sample id"] in matched]
    missing={field:sum(not row.get(field) for row in mapped) for field in REQUIRED}
    pair=[row["Pair_number"] for row in mapped if row.get("Pair_number")]
    site=[row["Site_code"] for row in mapped if row.get("Site_code")]
    trees=[row["tree_species"] for row in mapped if row.get("tree_species")]
    paired=collections.Counter(pair)
    sites=collections.Counter(site)
    groupkeys=[(row.get("Pair_number",""),row.get("Site_code","")) for row in mapped]
    group_n=collections.Counter(groupkeys)
    full=(len(matched)==150 and not duplicates and not (spkeys-keyset) and
          not any(missing.values()) and len(sites)==10 and len(paired)==5 and
          len(set(trees))==1 and len(groupkeys)==len(set(spid)) and
          len(group_n)==10)
    # No raw names, keys, dates, geographic coordinates, phenology or taxa exported.
    return {
      "all_original_Samples_18_first_row_field_labels_only":[names[k] for k,_,_ in samp_header],
      "original_Species_3_first_row_descriptor_labels_only":[to_label((t,v),hdr_shared) for _,t,v in species_header[:3]],
      "source_samples_sheet_used_range":"A1:R168",
      "source_species_sheet_used_range":"A1:EW68",
      "n_samples_sheet_original_xml_data_rows":nrows,
      "n_samples_rows_nonempty_sample_id":len(nonempty),
      "n_unique_source_samples_ids":len(keyset),
      "n_source_sample_ids_duplicated":len(duplicates),
      "n_original_species_matrix_numeric_sample_column_headers":150,
      "n_species_columns_exactly_matching_source_sample_id":len(matched),
      "n_species_column_headers_absent_from_samples":len(spkeys-keyset),
      "n_samples_keys_unreferenced_by_species_columns":len(keyset-spkeys),
      "original_required_method_columns_present":sorted(REQUIRED),
      "read_additional_allowlisted_nonresponse_columns":sorted(set(colmap.values())-REQUIRED),
      "matched_missingness_counts":missing,
      "matched_distinct_site_pairs":len(paired),
      "matched_distinct_original_stand_code":len(sites),
      "matched_distinct_wood_types":len(set(trees)),
      "matched_stand_samples_minmax":([min(group_n.values()),max(group_n.values())]
                                       if group_n else []),
      "matched_pair_samples_minmax":([min(paired.values()),max(paired.values())]
                                       if paired else []),
      "source_sample_and_parent_identifiers_exported":False,
      "original_species_row_or_abundance_values_parsed":0,
      "field_parent_identity_gate_pass":full,
      "status":("SOURCE_150_SPECIES_COLUMN_IDENTITY_AND_FIVE_PAIR_STAND_HIERARCHY_PASS_NO_BIOLOGY"
               if full else "SOURCE_ORIGINAL_SAMPLE_OR_HIERARCHY_IDENTITY_HOLD_NO_BIOLOGY")
    }

def test():
    assert to_label(("n","12.0"),{})=="12"
    assert to_label(("str"," 012 "),{})=="012"
    assert to_label(("str"," P04-S3 "),{})=="P04-S3"
    assert col_letters("AB200")=="AB"
    assert len(ALLOW)==10
    print("SOURCE_ONLY_RAMBERG_ID_CONTRACT_KNOWN_TRUTH_PASS")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--out",default="ramberg2026_sample_identity_sourceonly/receipt.json")
    args=ap.parse_args()
    test()
    if args.test:return
    result={
      "schema":"structural.ramberg2026_original_150stump_sample_species_header_crosswalk.v1",
      "record":"10.5281/zenodo.23021809",
      "original_file_sha256":base.SHA,
      "read_original_species_abundance_rows":0,
      "ecological_effects_computed":0,
      "old_Ecuador_2026_Frostgard_2026_and_Ramberg2025_effects_unchanged":True,
      "status":"SOURCE_ORIGINAL_SAMPLE_IDENTITY_HOLD"
    }
    try:
        result["anonymous_sample_key_and_stand_gate"]=score_source_keys(base.original_file())
        result["status"]=result["anonymous_sample_key_and_stand_gate"]["status"]
    except Exception as e:
        result["status"]="SOURCE_ORIGINAL_SAMPLE_ID_SCHEMA_OR_TRANSPORT_STOP"
        result["error_class"]=type(e).__name__
        result["error_code"]=str(e)[:120] if isinstance(e,ValueError) else ""
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(result,sort_keys=True,ensure_ascii=False,indent=2)+"\n")
    print("SOURCE_IDENTITY_STATUS",result["status"])
    x=result.get("anonymous_sample_key_and_stand_gate",{})
    print("SPECIES_COLUMNS_PHYSICAL_SAMPLE_ID_MATCHES",x.get("n_species_columns_exactly_matching_source_sample_id"))
    print("NO_ORIGINAL_SPECIES_RESPONSE_READ",result["read_original_species_abundance_rows"]==0)

if __name__=="__main__":
    main()
