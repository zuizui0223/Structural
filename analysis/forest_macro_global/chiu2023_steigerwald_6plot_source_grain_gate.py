#!/usr/bin/env python3
"""Only six site / shade / host / year ORIGINAL method fields, no beetle responses."""
from __future__ import annotations
import argparse, csv, hashlib, io, json
import urllib.request, urllib.error
from collections import Counter, defaultdict
from pathlib import Path

URL="https://raw.githubusercontent.com/AnneChao/PTB_iNEXT.link/e4fec0ba4d22a50f8b20553dc7da03a715d52bfe/Data_tree-beetle_interaction_frequency.csv"
SIZE=309247
BLOB="0d935bc5c5fbf64528aa34607ce72b0beab6d7d4"
HEADERS=["ID","species","plot","treatment","tree_spec","year",
         "abundance","tree_species","inte"]
EXPECTED_YEARS={"2016","2017","2018","2019"}
EXPECTED_TREATMENTS={"G","N","O"}
EXPECTED_PLOTS={"A","B","C","D","E","F"}
EXPECTED_HOSTS={"A","E","H","K","R","T"}
METHOD_FIELDS={"ID","plot","treatment","tree_spec","year","tree_species"}
class SourceStop(Exception):pass

def original_pub():
    request=urllib.request.Request(URL,method="GET",headers={
        "User-Agent":"Structural-author-Chao-Chiu-2023-source-method-only/1.0"})
    try:
        with urllib.request.urlopen(request,timeout=38) as fh:
            data=fh.read(SIZE+1)
            status=fh.status
            final=fh.url
    except urllib.error.HTTPError as exc:
        raise SourceStop("SOURCE_GITHUB_HTTP_"+str(exc.code)) from exc
    except (urllib.error.URLError,OSError,TimeoutError) as exc:
        raise SourceStop("SOURCE_GITHUB_TRANSPORT_"+type(exc).__name__) from exc
    if final!=URL or status!=200 or len(data)!=SIZE:
        raise SourceStop("SOURCE_PUBLISHER_PINNED_SIZE_REDIRECT_OR_HTTP_STOP")
    digest=hashlib.sha1(b"blob "+str(len(data)).encode("ascii")+b"\x00"+data).hexdigest()
    if digest!=BLOB:
        raise SourceStop("SOURCE_GIT_BLOB_SHA1_FAILED")
    return data

def method_only(raw):
    try:
        r=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""))
    except UnicodeError as exc:
        raise SourceStop("SOURCE_CSV_NON_UTF8") from exc
    if r.fieldnames!=HEADERS:
        raise SourceStop("SOURCE_ORIGINAL_HEADER_DRIFT")
    sites=set();hosts=set();treatments=set();years=set()
    contexts=set();year_contexts=set();id_contexts=defaultdict(set)
    cell_years=defaultdict(set);year_per_site=defaultdict(set)
    rows=0;host_disagreement=0
    try:
        for row in r:
            rows+=1
            if rows>5000 or None in row or any(row[k] is None for k in METHOD_FIELDS):
                raise SourceStop("SOURCE_ORIGINAL_CSV_ROW_FORMAT_OR_LIMIT")
            # No access to row["species"], row["abundance"], row["inte"].
            d={k:row[k].strip() for k in METHOD_FIELDS}
            if not all(d.values()):
                raise SourceStop("SOURCE_EMPTY_AUTHOR_METHOD_FIELD")
            if d["tree_spec"]!=d["tree_species"]:
                host_disagreement+=1
            plot,treat,host,year=d["plot"],d["treatment"],d["tree_spec"],d["year"]
            sites.add(plot);treatments.add(treat);hosts.add(host);years.add(year)
            base=(plot,treat,host);yearctx=base+(year,)
            contexts.add(base);year_contexts.add(yearctx)
            id_contexts[d["ID"]].add(yearctx)
            cell_years[base].add(year)
            year_per_site[plot].add(yearctx)
    except csv.Error as exc:
        raise SourceStop("SOURCE_ORIGINAL_CSV_PARSE") from exc
    if rows<100:
        raise SourceStop("SOURCE_FEWER_THAN_100_RECORD_ROWS")
    key_collisions=sum(len(s)>1 for s in id_contexts.values())
    results={
        "original_author_file_bytes":len(raw),
        "original_author_git_blob_sha1_VERIFIED":True,
        "original_source_field_count":len(HEADERS),
        "source_species_abundance_inte_columns_UNTOUCHED":True,
        "source_method_records_NOT_unique_traps_or_individuals":rows,
        "source_author_distinct_original_ID_labels":len(id_contexts),
        "source_author_ID_cross_context_collisions":key_collisions,
        "source_host_code_tree_spec_vs_tree_species_conflicts":host_disagreement,
        "source_distinct_parent_plots":len(sites),
        "source_distinct_treatment_levels":len(treatments),
        "source_distinct_original_host_types":len(hosts),
        "source_distinct_collection_years":len(years),
        "source_positive_recorded_plot_treat_host_contexts":len(contexts),
        "source_positive_recorded_plot_treat_host_year_contexts":len(year_contexts),
        "source_site_year_contexts_count_SORTED_NO_SITE_LABELS":
            sorted(len(v) for v in year_per_site.values()),
        "source_year_support_count_per_positive_cell_MIN_MAX":[
            min(map(len,cell_years.values())),
            max(map(len,cell_years.values()))],
        "source_original_site_host_year_IDs_values_NOT_EXPORTED":True,
        "complete_nonpositive_sampling_opportunities_NOT_VERIFIED":True,
        "no_original_biodiversity_or_model_estimator_executed":True,
    }
    if sites!=EXPECTED_PLOTS or treatments!=EXPECTED_TREATMENTS or (
       hosts!=EXPECTED_HOSTS or years!=EXPECTED_YEARS):
        results["status"]="SOURCE_ORIGINAL_AUTHOR_FIELD_LEVELS_NOT_PUBLISHED_6_3_6_4"
    elif host_disagreement>0 or key_collisions>0:
        results["status"]="SOURCE_HOST_OR_SAMPLE_ID_CONFLICT_STOP"
    elif len(contexts)!=108 or len(year_contexts)!=432:
        results["status"]="SOURCE_METHOD_OPPORTUNITY_COVERAGE_NOT_FULL_STOP"
    else:
        results["status"]="SOURCE_SIXPLOT_3TREATMENT_6HOST_FOURYEAR_FULL_POSITIVE_RECORD_SUPPORT"
    return results

def synthetic():
    writer=io.StringIO()
    w=csv.DictWriter(writer,fieldnames=HEADERS);w.writeheader()
    for site in sorted(EXPECTED_PLOTS):
        for tr in sorted(EXPECTED_TREATMENTS):
            for host in sorted(EXPECTED_HOSTS):
                for year in sorted(EXPECTED_YEARS):
                    for spp in ("SP1","SP2"):
                        row={"ID":site+tr+host+"_"+year,
                             "species":spp,"plot":site,"treatment":tr,
                             "tree_spec":host,"year":year,"abundance":"999",
                             "tree_species":host,"inte":"PROTECTED"}
                        w.writerow(row)
    x=method_only(writer.getvalue().encode())
    assert x["status"]=="SOURCE_SIXPLOT_3TREATMENT_6HOST_FOURYEAR_FULL_POSITIVE_RECORD_SUPPORT"
    assert x["source_positive_recorded_plot_treat_host_year_contexts"]==432
    assert x["source_author_distinct_original_ID_labels"]==432
    assert x["source_method_records_NOT_unique_traps_or_individuals"]==864
    assert "SP1" not in json.dumps(x) and "999" not in json.dumps(x)
    assert "PROTECTED" not in json.dumps(x)
    print("SYNTHETIC_CHIU_SIXPLOT_3TREAT_6HOST_4YEAR_METHOD_ONLY_SOURCE_GATE_PASS")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--test",action="store_true")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    synthetic()
    if args.test:return
    if args.out is None:p.error("--out needed")
    out={"schema":"structural.ChiuVogel2023_original_Steigerwald_sixplot_method_only.v1",
      "precommit":"docs/FOREST_BEETLE_CHIU2023_STEIGERWALD_SIXPLOT_HOST_SHADE_SOURCE_GRAIN_PRESPEC_20261117.md",
      "original_species_abundance_values_NOT_READ":True,
      "ecological_beta_or_p_NOT_TESTED":True,
      "prior_Piccini_Finland_Burner_Thai_BALA_GEB_UNCHANGED":True,
      "eBird_used":False,"TinyFish_used":False}
    try:
        raw=original_pub()
        out["source_method_only"]=method_only(raw)
        out["status"]=out["source_method_only"]["status"]
    except SourceStop as exc:
        out["status"]=str(exc)
        out["SOURCE_ACCESS_OR_ID_STOP_NOT_ECOLOGICAL_NULL"]=True
    args.out.mkdir(parents=True,exist_ok=True)
    (args.out/"Chiu2023_Steigerwald6plot_source_method_only.json").write_text(
        json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(out,indent=2,ensure_ascii=False))

if __name__=="__main__":main()
