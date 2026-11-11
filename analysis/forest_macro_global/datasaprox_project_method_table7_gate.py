#!/usr/bin/env python3
"""Response-unopened DATASAPROX project/table-7 source-method crosswalk.

Input 1: original publisher v1.6 DwC-A (sampling metadata fields ONLY).
Input 2: original 2026 article JATS (published Table 7, project completeness).
No taxon, species, individual count, geographic coordinates or raw plot IDs
are read or exported. This is a retrospective design diagnostic, never an
independent biological effect or permission to ignore ID_condition.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,unicodedata,xml.etree.ElementTree as ET,zipfile
from collections import defaultdict
from pathlib import Path
from datasaprox_source_metadata_gate import schema,properties,layer,duration,localname

ARCHIVE_SHA="4163a2f8f72d756e74f64319b8e199b284ecc6414196147e4465d342d7dcb6d0"
PAPER_DOI="10.3897/bdj.14.e187021"
MAX_ARCHIVE_BYTES=80_000_000
MAX_XML_BYTES=18_000_000

def norm(s):
    return " ".join(unicodedata.normalize("NFKC",str(s or "")).split()).casefold()

def paper_table7(xml_bytes, *, return_audit=False):
    if len(xml_bytes)>MAX_XML_BYTES:raise ValueError("STOP_PAPER_XML_TOO_LARGE")
    root=ET.fromstring(xml_bytes)
    dois={
        norm("".join(e.itertext()))
        for e in root.iter()
        if localname(e.tag)=="article-id" and e.attrib.get("pub-id-type")=="doi"
    }
    if PAPER_DOI not in dois:raise ValueError("STOP_PAPER_DOI_IDENTITY_NOT_VERIFIED")
    tables=[]
    for t in root.iter():
        if localname(t.tag)!="table-wrap":continue
        label=next((e for e in t if localname(e.tag)=="label"),None)
        if label is not None and re.search(r"\btable\s*7\b","".join(label.itertext()),re.I):
            tables.append(t)
    if len(tables)!=1:raise ValueError("STOP_PUBLISHED_TABLE7_NOT_UNIQUE")
    results={}
    n_data_rows=0
    previous_provider=""
    identical_duplicate_rows=0
    ambiguous_duplicate_keys=set()
    for tr in tables[0].iter():
        if localname(tr.tag)!="tr":continue
        cells=[
            " ".join("".join(e.itertext()).split())
            for e in tr
            if localname(e.tag) in ("td","th")
        ]
        # Source JATS uses row-spanned or blank producer cells; the author
        # code must inherit the preceding data row, never the table header.
        if len(cells)==5 and previous_provider:
            cells=[previous_provider]+cells
        if len(cells)<6:continue
        provider,title,dominant,families,median,community=cells[:6]
        if norm(community) not in ("complete","partial"):continue
        if not provider:provider=previous_provider
        if provider:previous_provider=provider
        if not title:continue
        try:
            nfamilies=int(families)
            ntaxa=float(median.replace(",","."))
        except ValueError:raise ValueError("STOP_PAPER_TABLE7_NUMERIC_SCHEMA_CHANGED")
        if nfamilies<0 or ntaxa<0:raise ValueError("STOP_PAPER_TABLE7_INVALID_VALUES")
        k=norm(provider),norm(title)
        if not all(k):raise ValueError("STOP_PAPER_TABLE7_KEY_MISSING")
        if k in ambiguous_duplicate_keys:continue
        row_value={
            "published_project_community_scope":norm(community),
            "published_project_family_count":nfamilies,
            "published_project_median_taxa_per_sample":ntaxa,
            "published_project_dominant_family_record_share_source":dominant,
        }
        n_data_rows+=1
        if k in results:
            if results[k]==row_value:
                identical_duplicate_rows+=1
            else:
                ambiguous_duplicate_keys.add(k)
                results.pop(k)
            continue
        results[k]=row_value
    if not n_data_rows:raise ValueError("STOP_PAPER_TABLE7_NO_PROJECT_ROWS")
    audit={
        "source_article_table7_data_row_count":n_data_rows,
        "source_article_table7_identical_duplicate_rows":identical_duplicate_rows,
        "source_article_table7_conflicting_project_keys_excluded":len(ambiguous_duplicate_keys),
        "source_article_table7_unique_project_keys_unambiguous":len(results),
    }
    return (results,audit) if return_audit else results

def source_sample_events(archive):
    path=Path(archive)
    if not path.is_file() or path.stat().st_size>MAX_ARCHIVE_BYTES:
        raise ValueError("STOP_ORIGINAL_ARCHIVE_UNAVAILABLE_OR_OVERSIZE")
    if hashlib.sha256(path.read_bytes()).hexdigest()!=ARCHIVE_SHA:
        raise ValueError("STOP_PUBLISHER_V1_6_ARCHIVE_SHA_DRIFT")
    seen={};bad=set();source_rows=0
    with zipfile.ZipFile(path) as z:
        src=schema(z)
        fm=src["fields"]
        mandatory=("eventID","datasetName","ownerInstitutionCode","dynamicProperties","year","month","sampleSizeValue","sampleSizeUnit")
        if any(k not in fm for k in mandatory):raise ValueError("STOP_ORIGINAL_SAMPLING_SCHEMA_DRIFT")
        with z.open(src["file"]) as binary:
            file=io.TextIOWrapper(binary,encoding="utf-8-sig",newline="")
            rows=csv.reader(file,delimiter=src["delimiter"],quotechar=src["quote"] or '"',
                quoting=csv.QUOTE_MINIMAL if src["quote"] else csv.QUOTE_NONE)
            for _ in range(src["header"]):next(rows)
            for row in rows:
                if not row:continue
                source_rows+=1
                if source_rows>1_200_000:raise ValueError("STOP_SOURCE_ROW_LIMIT")
                def fld(k):
                    i=fm[k]
                    return row[i].strip() if i<len(row) else ""
                project=(fld("ownerInstitutionCode"),fld("datasetName"))
                eventid=fld("eventID")
                if not project[1] or not eventid:continue
                dp=properties(fld("dynamicProperties"))
                y,m=fld("year"),fld("month")
                sample=(
                    layer(dp.get("trap_stratum","")),
                    dp.get("id_plot",""),
                    dp.get("trap_model",""),
                    dp.get("trap_type",""),
                    dp.get("id_condition",""),
                    dp.get("trap_bait",""),
                    dp.get("trap_colour",""),
                    f"{y}-{m.zfill(2)}" if y and m else "",
                    duration(fld("sampleSizeValue"),fld("sampleSizeUnit")),
                )
                k=(*project,eventid)
                if k in seen and seen[k]!=sample:bad.add(k)
                else:seen[k]=sample
    if source_rows!=675525 or len(seen)!=65642 or len(bad)!=1133:
        raise ValueError("STOP_CANONICAL_SOURCE_EVENT_DENOMINATOR_DRIFT")
    return seen,bad,source_rows

def crosswalk(events,bad,published):
    # Same original response-blind 87 candidate design, including
    # original trap model/type, bait/colour and bounded sample duration.
    groups=defaultdict(lambda:{"upper":[],"lower":[]})
    for (producer,project,event),a in events.items():
        if (producer,project,event) in bad:continue
        stratum,plot,model,typ,condition,bait,colour,yearmonth,days=a
        if stratum not in ("upper","lower") or not (plot and model and yearmonth and days is not None):
            continue
        key=(producer,project,plot,yearmonth,model,typ,bait,colour)
        groups[key][stratum].append((days,condition))
    pairs={}
    for key,v in groups.items():
        if any(7<=x<=35 and 7<=y<=35 and abs(x-y)<=7
               for x,_ in v["upper"] for y,_ in v["lower"]):
            pairs[key]=v
    by_project=defaultdict(list)
    for key,v in pairs.items():by_project[key[:2]].append((key,v))
    if len(pairs)!=87 or len(by_project)!=3 or len({k[:3] for k in pairs})!=45:
        raise ValueError("STOP_SOURCE_SENSITIVE_DESIGN_DENOMINATORS_CHANGED")
    public=[]
    for i,(project,subset) in enumerate(sorted(by_project.items()),1):
        plot_count=len({k[2] for k,v in subset})
        upper_conditions=set();lower_conditions=set()
        for _,v in subset:
            upper_conditions.update(code for _,code in v["upper"] if code)
            lower_conditions.update(code for _,code in v["lower"] if code)
        key=(norm(project[0]),norm(project[1]))
        pub=published.get(key)
        public.append({
            "source_project_anonymous_index":i,
            "original_matched_plot_count":plot_count,
            "paired_plot_period_method_units_nonindependent":len(subset),
            "upper_ID_condition_distinct_nonempty_code_count":len(upper_conditions),
            "lower_ID_condition_distinct_nonempty_code_count":len(lower_conditions),
            "upper_lower_shared_ID_condition_nonempty_code_count":len(upper_conditions&lower_conditions),
            "journal_published_Table7_exact_source_project_match":pub is not None,
            "journal_published_Table7_scope":pub["published_project_community_scope"] if pub else "NOT_VERIFIED",
            "journal_published_family_count":pub["published_project_family_count"] if pub else None,
            "journal_published_median_taxa_per_sample":pub["published_project_median_taxa_per_sample"] if pub else None,
            "journal_published_dominant_family_record_share":pub["published_project_dominant_family_record_share_source"] if pub else None,
            "original_author_specific_treatment_semantics_verified":False,
            "original_independent_physical_forest_verified":False,
        })
    return {
        "schema":"structural.datasaprox_published_table7_source_method_crosswalk.v1",
        "source_original_occurrence_rows_metadata_only":675525,
        "original_source_sample_event_keys":len(events),
        "excluded_all_conflicting_source_event_keys":len(bad),
        "candidate_without_ID_condition_paired_units":len(pairs),
        "candidate_without_ID_condition_distinct_plot_keys":45,
        "candidate_without_ID_condition_distinct_source_projects":3,
        "published_Table7_total_project_rows_parsed":len(published),
        "candidate_projects_matched_to_published_Table7":sum(p["journal_published_Table7_exact_source_project_match"] for p in public),
        "candidate_projects_published_complete":sum(p["journal_published_Table7_scope"]=="complete" for p in public),
        "candidate_projects_published_partial":sum(p["journal_published_Table7_scope"]=="partial" for p in public),
        "candidate_project_metadata":public,
        "original_treatment_field_publisher_definition":"treatments of the sampling design",
        "source_treatment_codes_confirmed_as_just_layer_alias":False,
        "original_same_treatment_design_scientific_STOP_preserved":True,
        "no_taxon_species_abundance_geo_or_raw_field_ID_access":True,
        "no_biological_community_composition_result":True,
        "eBird_used":False,
    }

def run(archive,paper,out):
    pub,article_audit=paper_table7(Path(paper).read_bytes(),return_audit=True)
    events,bad,n=source_sample_events(archive)
    result=crosswalk(events,bad,pub)
    result["source_article_Table7_collision_audit"]=article_audit
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"datasaprox_published_table7_project_scope_crosswalk.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--archive",required=True)
    p.add_argument("--paper-xml",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    run(a.archive,a.paper_xml,a.out)
