#!/usr/bin/env python3
"""DATASAPROX v1.6: source-metadata-only vertical sampling audit.

Publisher archive: https://ipt.gbif.fr/archive.do?r=datasaprox&v=1.6
DO NOT inspect taxonomy, abundances, raw identities, or species responses.
Raw source archive and identifiers remain local to the CI runner.
"""
import argparse,csv,hashlib,io,json,math,re,xml.etree.ElementTree as ET,zipfile
from collections import Counter,defaultdict
from pathlib import Path

UUID="d050a143-2e62-4908-9d9e-a7f541eab94d"
MAX_COMPRESSED=80_000_000
MAX_UNCOMPRESSED=550_000_000
MAX_ROWS=1_200_000
META_COLS=frozenset(("eventID","fieldNumber","materialSampleID","datasetName",
 "ownerInstitutionCode","year","month","eventDate","sampleSizeValue",
 "sampleSizeUnit","dynamicProperties","samplingProtocol"))

def localname(raw):
    return re.split(r"[/#}]",raw)[-1]

def schema(z):
    if "meta.xml" not in z.namelist():raise ValueError("STOP_META_XML_MISSING")
    root=ET.fromstring(z.read("meta.xml"))
    core=next((e for e in root.iter() if localname(e.tag)=="core"),None)
    if core is None:raise ValueError("STOP_CORE_MISSING")
    rowtype=localname(core.attrib.get("rowType",""))
    if rowtype!="Occurrence":raise ValueError("STOP_NOT_ORIGINAL_OCCURRENCE_CORE")
    location=next((e.text for e in core.iter() if localname(e.tag)=="location"),None)
    if not location or location not in z.namelist():raise ValueError("STOP_CORE_FILE_MISSING")
    f={}
    for e in core:
        if localname(e.tag)=="field" and "index" in e.attrib:
            k=localname(e.attrib.get("term",""))
            if k in f:raise ValueError("STOP_DUPLICATE_FIELD")
            f[k]=int(e.attrib["index"])
    if len(f)!=len(set(f.values())):raise ValueError("STOP_DUPLICATE_COLUMN_INDEX")
    sep=core.attrib.get("fieldsTerminatedBy",r"\t")
    sep="\t" if sep in (r"\t","\t") else sep
    if sep not in ("\t",",",";"):raise ValueError("STOP_DELIMITER_UNKNOWN")
    quote=core.attrib.get("fieldsEnclosedBy",'"')
    if quote not in ('"',"",r'\"'):raise ValueError("STOP_QUOTING_UNKNOWN")
    return dict(file=location,fields=f,delimiter=sep,
        quote='"' if quote else None,header=int(core.attrib.get("ignoreHeaderLines",0)))

def properties(raw):
    if not raw:return {}
    try:
        q=json.loads(raw)
        if isinstance(q,dict):
            return {str(k).strip().lower():str(v).strip() for k,v in q.items()}
    except (ValueError,TypeError):pass
    out={}
    for k in ("ID_plot","ID_subplot","trap_stratum","trap_model","trap_type","ID_condition","trap_bait","trap_colour"):
        m=re.search(r'(?i)(?:^|[;|,{])\s*["\']?'+re.escape(k)+
                    r'["\']?\s*[:=]\s*["\']?([^;|,}\r\n]+)',raw)
        if m:out[k.lower()]=m.group(1).strip().strip('"\' ')
    return out

def layer(raw):
    s=str(raw).casefold().strip()
    if not s or s in ("none","na","nan","unknown","non renseigné"):return "unclassified"
    if any(x in s for x in ("understorey","understory","sous-bois","sous bois")):return "lower"
    if any(x in s for x in ("ground","forest floor","terrestre","au sol")):return "lower"
    if s in ("sol","bas"):return "lower"
    if any(x in s for x in ("canopy","canopée","canop","houppier","cime","couronne")):return "upper"
    return "unclassified"

def duration(raw,unit):
    try:d=float(raw)
    except (ValueError,TypeError):return None
    return d if math.isfinite(d) and d>0 and str(unit).casefold().strip() in ("day","days","jour","jours") else None

def conservative_consistent_event_subset(events, conflicted):
    """Post-schema response-unopened diagnostic only; never replaces strict STOP.

    Entire conflicting original event keys are excluded. Other original keys
    remain untouched. This is not an independent-site certification.
    """
    assert conflicted <= set(events)
    remaining={k:v for k,v in events.items() if k not in conflicted}
    # Progressive source-only estimability ledger. It is NOT a series
    # of biological tests or an invitation to choose a favorable threshold.
    counts=Counter(v[0] for v in remaining.values())
    fields_available={
        "original_plot":sum(bool(v[1]) for v in remaining.values()),
        "trap_model":sum(bool(v[2]) for v in remaining.values()),
        "trap_type":sum(bool(v[3]) for v in remaining.values()),
        "year_month":sum(bool(v[7]) for v in remaining.values()),
        "duration_in_days":sum(v[8] is not None for v in remaining.values()),
        "duration_between_7_and_35_days":sum(v[8] is not None and 7<=v[8]<=35 for v in remaining.values()),
    }
    stage_defs=[
        ("01_shared_original_project_plot",(1,)),
        ("02_plus_same_year_month",(1,7)),
        ("03_plus_same_trap_model",(1,7,2)),
        ("04_plus_same_trap_type",(1,7,2,3)),
        ("05_plus_same_treatment",(1,7,2,3,4)),
        ("06_plus_same_bait_and_colour",(1,7,2,3,4,5,6))
    ]
    stages={}
    for label,ixs in stage_defs:
        blocks=defaultdict(set)
        for (producer,project,eid),v in remaining.items():
            if v[0] not in ("upper","lower"):
                continue
            if any(not v[i] for i in ixs if i in (1,2,7)):
                continue
            k=(producer,project)+tuple(v[i] for i in ixs)
            blocks[k].add(v[0])
        stages[label]=sum(len(z)==2 for z in blocks.values())
    grouped=defaultdict(lambda:defaultdict(list))
    for (producer,project,eventid),desc in remaining.items():
        stratum,plot,model,traptype,condition,bait,colour,ym,days=desc
        if stratum=="unclassified" or not (plot and model and ym and days is not None):
            continue
        g=(producer,project,plot,ym,model,traptype,condition,bait,colour)
        grouped[g][stratum].append(days)
    candidates=[]
    for g,st in grouped.items():
        if any(7<=hi<=35 and 7<=lo<=35 and abs(hi-lo)<=7
               for hi in st["upper"] for lo in st["lower"]):
            candidates.append(g)
    physical={(g[0],g[1],g[2]) for g in candidates}
    projects={(g[0],g[1]) for g in physical}
    return {
        "post_qa_diagnostic_status":"EXPLORATORY_CONSISTENT_EVENT_KEYS_ONLY_NOT_PRIMARY_ADMISSION",
        "post_qa_conservatively_retained_consistent_source_event_keys":len(remaining),
        "post_qa_excluded_entire_conflicting_source_event_keys":len(conflicted),
        "post_qa_source_event_canonical_stratum_counts":dict(sorted(counts.items())),
        "post_qa_metadata_availability_by_field_source_event_keys":fields_available,
        "post_qa_unpaired_progressive_design_support_groups_nonindependent":stages,
        "post_qa_paired_project_plot_month_method_treatment_strata":len(candidates),
        "post_qa_distinct_project_plot_keys_candidate_only":len(physical),
        "post_qa_distinct_source_project_keys_candidate_only":len(projects),
        "post_qa_meets_numerical_30_plot_3_project_threshold_only":len(physical)>=30 and len(projects)>=3,
        "post_qa_original_independent_physical_forest_verification":False,
        "post_qa_species_response_scored":False,
        "post_qa_never_relabels_strict_source_stop":True,
    }


def inspect_rows(reader,fields,maxrows=MAX_ROWS):
    if "dynamicProperties" not in fields:return {"status":"STOP_NO_STRATUM_FIELD","rows":0}
    identity=next((k for k in ("eventID","fieldNumber","materialSampleID") if k in fields),None)
    if identity is None:return {"status":"STOP_NO_AUTHOR_EVENT_ID","rows":0}
    if "datasetName" not in fields:return {"status":"STOP_NO_ORIGINAL_PROJECT_FIELD","rows":0}
    events={};rows=0;conflicts=0;empty=0;strata_raw=0;duration_n=0
    conflict_fields=Counter(); conflicting_event_keys=set()
    source_event_raw_stratum_labels=Counter()
    descriptor_fields=("stratum","original_plot","trap_model","trap_type","treatment","bait","colour","year_month","duration")
    for row in reader:
        if not row:continue
        rows+=1
        if rows>maxrows:raise ValueError("STOP_SOURCE_ROWS_EXCEED_CAP")
        def val(k):
            j=fields.get(k)
            return row[j].strip() if j is not None and j<len(row) else ""
        k=(val("ownerInstitutionCode"),val("datasetName"),val(identity))
        if not k[1] or not k[2]:empty+=1;continue
        p=properties(val("dynamicProperties"))
        rawlayer=p.get("trap_stratum","")
        strata_raw+=int(bool(rawlayer))
        y,m=val("year"),val("month")
        dt=val("eventDate")
        if (not y or not m) and re.match(r"^\d{4}-\d{2}",dt):
            y,m=y or dt[:4],m or dt[5:7]
        ym=f"{y}-{m.zfill(2)}" if y and m else ""
        d=duration(val("sampleSizeValue"),val("sampleSizeUnit"))
        duration_n+=int(d is not None)
        # Sample-level plot and method must be original, never inferred from coordinates.
        desc=(layer(rawlayer),p.get("id_plot",""),p.get("trap_model",""),
              p.get("trap_type",""),p.get("id_condition",""),
              p.get("trap_bait",""),p.get("trap_colour",""),ym,d)
        if k not in events:
            source_event_raw_stratum_labels[rawlayer.strip().casefold()]+=1
        if k in events and events[k]!=desc:
            conflicts+=1
            conflicting_event_keys.add(k)
            for field,was,now in zip(descriptor_fields,events[k],desc):
                if was!=now: conflict_fields[field]+=1
        else:events[k]=desc
    if conflicts:
        return dict(status="STOP_CONFLICTING_AUTHOR_EVENT_METADATA",
            source_original_occurrence_rows_metadata_streamed=rows,
            original_unique_source_event_key_count=len(events),
            conflicting_source_event_key_count=len(conflicting_event_keys),
            conflicting_original_occurrence_rows=conflicts,
            conflicts_by_field_metadata_only=dict(sorted(conflict_fields.items())),
            original_source_event_stratum_declared_nonempty=sum(v for k,v in source_event_raw_stratum_labels.items() if k),
            original_source_event_stratum_empty=source_event_raw_stratum_labels.get("",0),
            original_source_stratum_distinct_nonempty_labels=sum(bool(k) for k in source_event_raw_stratum_labels),
            original_source_stratum_top_public_category_labels=[
                {"source_original_category":k if re.fullmatch(r"[a-zà-ÿ0-9 .+_()/\\-]{1,48}",k) else "[masked_metadata_category]",
                 "source_event_key_count":v}
                for k,v in source_event_raw_stratum_labels.most_common(20)
                if k and v>=3],
            original_independent_layer_matched_plots_yet_counted=0,
            no_species_response_or_inferred_independence=True,
            **conservative_consistent_event_subset(events,conflicting_event_keys))
    status=Counter(v[0] for v in events.values())
    by_plot=defaultdict(lambda:defaultdict(list))
    candidate_events=0
    for (producer,project,eid),q in events.items():
        v,plot,model,traptype,condition,bait,colour,ym,days=q
        if v=="unclassified" or not (plot and model and ym and days is not None):
            continue
        candidate_events+=1
        # Same source project/plot/period/trap model and treatment, type, bait/colour.
        key=(producer,project,plot,ym,model,traptype,condition,bait,colour)
        by_plot[key][v].append(days)
    pairs=[]
    for k,g in by_plot.items():
        if any(7<=a<=35 and 7<=b<=35 and abs(a-b)<=7
               for a in g["upper"] for b in g["lower"]):
            pairs.append(k)
    distinct={(k[0],k[1],k[2]) for k in pairs}
    projects={(k[0],k[1]) for k in distinct}
    qualified=len(distinct)>=30 and len(projects)>=3
    if not duration_n:decision="STOP_NO_SOURCE_DURATION_DAYS"
    elif not strata_raw:decision="STOP_NO_SOURCE_STRATUM_VALUES"
    elif not pairs:decision="STOP_NO_COMPARABLE_PAIRED_STRATA"
    elif not qualified:decision="STOP_LT30_PLOTS_OR_LT3_PROJECTS"
    else:decision="METADATA_PAIRS_CANDIDATE_FURTHER_SOURCE_VERIFICATION"
    return dict(
        status=decision,
        source_original_occurrence_rows_metadata_streamed=rows,
        source_rows_missing_project_or_event_ID=empty,
        original_unique_source_sample_IDs=len(events),
        original_sample_stratum_counts=dict(sorted(status.items())),
        source_original_stratum_field_nonempty_occurrence_rows=strata_raw,
        source_original_duration_days_available_occurrence_rows=duration_n,
        original_event_descriptors_with_candidate_layer_effort=candidate_events,
        same_project_plot_month_method_treatment_paired_strata_nonindependent=len(pairs),
        distinct_matched_original_project_plot_keys=len(distinct),
        distinct_matched_original_project_keys=len(projects),
        frozen_exploratory_design_gate_passed=qualified,
        original_plot_independence_field_hierarchy_verified=False,
        data_origin="France_mainland_and_Corsica_not_global",
        original_occurrence_species_values_read=False,
        original_species_response_test_performed=False,
        raw_sample_plot_project_taxon_or_coordinate_identifiers_exported=False,
    )

def run(archive,out):
    src=Path(archive)
    if not src.is_file() or src.stat().st_size>MAX_COMPRESSED:
        raise ValueError("STOP_ARCHIVE_MISSING_OR_OVERSIZE")
    with zipfile.ZipFile(src) as z:
        if sum(i.file_size for i in z.infolist())>MAX_UNCOMPRESSED:
            raise ValueError("STOP_UNCOMPRESSED_ARCHIVE_OVERSIZE")
        meta=schema(z)
        with z.open(meta["file"]) as f:
            raw=io.TextIOWrapper(f,encoding="utf-8-sig",errors="strict",newline="")
            rdr=csv.reader(raw,delimiter=meta["delimiter"],quotechar=meta["quote"] or '"',
                quoting=csv.QUOTE_MINIMAL if meta["quote"] else csv.QUOTE_NONE)
            for _ in range(meta["header"]):next(rdr)
            result=inspect_rows(rdr,meta["fields"])
    report={"schema":"structural.datasaprox_source_metadata_vertical_gate.v1",
      "source_uuid":UUID,"source_release":"DATASAPROX_v1.6",
      "original_archive_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),
      "original_occurrence_core_metadata_fields":sorted(META_COLS & set(meta["fields"])),
      "original_occurrence_species_values_read":False,
      "original_species_response_test_performed":False,
      "raw_sample_plot_project_taxon_or_coordinate_identifiers_exported":False,
      "original_plot_independence_field_hierarchy_verified":False,
      **result}
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    (out/"datasaprox_vertical_metadata_gate.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--archive",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();run(a.archive,a.out)
