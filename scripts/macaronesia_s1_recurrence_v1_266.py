#!/usr/bin/env python3
"""Published Macaronesian S1 case-only recurrence; no risk/causal inference.

Uses already-consumed Table S1 only. Primary results preserve literal source
names. Numeric-annotation removal is an explicitly labelled sensitivity, not
synonym reconciliation or authority to change a taxonomic backbone.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import statistics
import unicodedata

NEEDED=('Species','Extinction category','Category','Island','Archipelago','Date',
        'Pollination mechanism','Seed dispersal mechanism','Habit','Endemicity')
TRAITS=('Pollination mechanism','Seed dispersal mechanism','Habit','Endemicity')
SOURCE_SHA='767f9ea095660d77babb8eb74b2eb714e8cdc38cb0c6861051416a7c0039b0e1'
SOURCE_URL='https://digital.csic.es/bitstream/10261/377677/5/Extinct_species_biogeographical_variables_%26_biological_traits_Macaronesian_flora.xlsx'


def clean(value):
    return ' '.join(str(value or '').split())


def normalize_name(value,strip_annotations=False):
    name=clean(value).casefold()
    if strip_annotations:
        name=unicodedata.normalize('NFKC',name)
        name=re.sub(r'[0-9]+$','',name).rstrip()
    return name


def year(value):
    v=clean(value)
    if not re.fullmatch(r'(17|18|19|20)\d{2}(?:\.0+)?',v):
        return None
    n=int(float(v))
    return n if 1753<=n<=2026 else None


def count_dict(values):
    return dict(sorted(Counter(values).items()))


def one_report(records,strip_annotations=False):
    eligible=[r for r in records
              if clean(r['Extinction category']).casefold()=='extirpation (island level)'
              and clean(r['Category']).casefold()=='well-supported']
    invalid=[r for r in eligible if not all(clean(r[x]) for x in ('Species','Island','Archipelago'))]
    if invalid:
        raise ValueError('Strict qualifying record without taxon/island/archipelago identity')
    grouped=defaultdict(list)
    cross=defaultdict(Counter)
    for r in records:
        cross[clean(r['Extinction category']) or '[MISSING]'][clean(r['Category']) or '[MISSING]']+=1
    for r in eligible:
        grouped[(normalize_name(r['Species'],strip_annotations),
                 clean(r['Archipelago']),clean(r['Island']))].append(r)
    bytax=defaultdict(list)
    byarch=defaultdict(list)
    for key,rs in grouped.items():
        bytax[key[0]].append((key,rs))
        byarch[key[1]].append((key,rs))
    repeat={k:v for k,v in bytax.items() if len(v)>1}
    pair_dates={key:{clean(r['Date']) for r in rs} for key,rs in grouped.items()}
    conflicting=sum(len(d)>1 for d in pair_dates.values())
    exact_two=[v for v in bytax.values() if len(v)==2]
    gaps=[]
    for entries in exact_two:
        ys=[]
        for key,_ in entries:
            dates=pair_dates[key]
            ys.append(year(next(iter(dates))) if len(dates)==1 else None)
        if all(y is not None for y in ys):
            gaps.append(abs(ys[0]-ys[1]))
    gaps.sort()
    out_arch={}
    for arch,entries in sorted(byarch.items()):
        tc=Counter(k[0] for k,_ in entries)
        ic=Counter(k[2] for k,_ in entries)
        out_arch[arch]={
            'taxon_island_pairs':len(entries),'distinct_taxa':len(tc),
            'named_islands':len(ic),'repeat_taxa':sum(v>=2 for v in tc.values()),
            'taxa_by_number_of_islands':{str(k):v for k,v in sorted(Counter(tc.values()).items())},
            'case_counts_by_island_descending':sorted(ic.values(),reverse=True)}
    unique_traits={}
    event_traits={}
    for field in TRAITS:
        unique=[]
        for tax,entries in bytax.items():
            values={clean(r[field]) or '[MISSING]' for _,rs in entries for r in rs}
            unique.append(next(iter(values)) if len(values)==1 else '[INCONSISTENT]')
        unique_traits[field]=count_dict(unique)
        event=[]
        for rs in grouped.values():
            values={clean(r[field]) or '[MISSING]' for r in rs}
            event.append(next(iter(values)) if len(values)==1 else '[INCONSISTENT]')
        event_traits[field]=count_dict(event)
    out={
        'raw_strict_rows':len(eligible),'taxon_island_pairs':len(grouped),
        'duplicate_pair_records':len(eligible)-len(grouped),
        'distinct_taxa':len(bytax),'repeat_taxa':len(repeat),
        'single_island_loss_taxa':sum(len(v)==1 for v in bytax.values()),
        'loss_pairs_belonging_to_repeat_taxa':sum(len(v) for v in repeat.values()),
        'taxa_by_number_of_islands':{str(k):v for k,v in sorted(Counter(map(len,bytax.values())).items())},
        'cross_archipelago_repeat_taxa':sum(len({k[1] for k,_ in v})>=2 for v in bytax.values()),
        'conflicting_pair_dates':conflicting,
        'confidence_by_status':{k:dict(sorted(v.items())) for k,v in sorted(cross.items())},
        'archipelagos':out_arch,
        'event_weighted_traits':event_traits,
        'unique_taxon_weighted_traits':unique_traits,
        'last_record_gaps_years':{
            'exact_two_island_taxa':len(exact_two),'parseable_pairs':len(gaps),
            'sorted_gaps':gaps,'median':statistics.median(gaps) if gaps else None,
            'minimum':min(gaps) if gaps else None,'maximum':max(gaps) if gaps else None,
            'same_recorded_year':sum(g==0 for g in gaps),
            'within_10_years':sum(g<=10 for g in gaps),
            'over_50_years':sum(g>50 for g in gaps),
            'not_observed_extinction_time_differences':True},
        'historically_occupied_persisting_islands_observed':False,
        'independent_at_risk_denominator_available':False}
    assert sum(x['taxon_island_pairs'] for x in out_arch.values())==len(grouped)
    assert sum(int(k)*v for k,v in out['taxa_by_number_of_islands'].items())==len(grouped)
    return out


def recurrence_report(records):
    if not records or any(not set(NEEDED)<=set(r) for r in records):
        raise ValueError('Source S1 required fields missing or empty input')
    raw_names={normalize_name(r['Species']) for r in records if clean(r['Species'])}
    normalized={normalize_name(r['Species'],True) for r in records if clean(r['Species'])}
    mapping=defaultdict(set)
    for n in raw_names:
        mapping[normalize_name(n,True)].add(n)
    return {
        'schema':'structural.macaronesia_S1_recurrence.v1_266',
        'evidence_class':'RETROSPECTIVE_CASE_ONLY_S1_DESCRIPTIVE_EXTENSION',
        'source_rows':len(records),
        'all_S1_raw_distinct_taxon_strings':len(raw_names),
        'all_S1_annotation_normalized_distinct_taxa':len(normalized),
        'names_changed_by_numeric_suffix_removal':sum(normalize_name(n,True)!=n for n in raw_names),
        'numeric_suffix_name_collision_groups':sum(len(v)>1 for v in mapping.values()),
        'raw_names':one_report(records,False),
        'numeric_annotation_sensitivity':one_report(records,True),
        'numeric_annotation_removal_is_not_taxonomic_synonym_validation':True,
        'species_names_or_individual_event_rows_exported':False,
        'S2_S3_S4_cells_read':0,'previous_protected_responses_reopened':False,
        'GEB_scientific_HOLD':True,'new_confirmatory_systems':0,'eBird_used':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,help='Local SHA-locked source; otherwise exact original URL')
    parser.add_argument('--out',required=True,type=Path)
    args=parser.parse_args()
    from macaronesia_local_loss_pilot_v1_265 import parse_sheet_s1
    from macaronesia_extirpation_source_profile_v1_263 import download_original
    raw=(args.source.read_bytes() if args.source else download_original(SOURCE_URL,332776,5_000_000))
    if len(raw)!=332776 or hashlib.sha256(raw).hexdigest()!=SOURCE_SHA:
        raise ValueError('Original CSIC source bytes/SHA differ; refuse biology access')
    records=parse_sheet_s1(raw)
    result=recurrence_report(records)
    result['source_sha256']=SOURCE_SHA
    result['source_url']=SOURCE_URL
    if result['source_rows']!=168 or result['raw_names']['taxon_island_pairs']!=62:
        raise ValueError('Frozen first-pass 168/62 source accounting changed')
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'status':'EXECUTED_S1_ONLY','source_records':168,
         'primary_pairs':result['raw_names']['taxon_island_pairs'],
         'primary_taxa':result['raw_names']['distinct_taxa'],
         'primary_repeat_taxa':result['raw_names']['repeat_taxa'],
         'annotation_sensitivity_taxa':result['numeric_annotation_sensitivity']['distinct_taxa']},sort_keys=True))

if __name__=='__main__':
    main()
