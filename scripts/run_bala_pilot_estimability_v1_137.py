#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,decimal,hashlib,json,math
from collections import Counter,defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT=ROOT/"development/bala_pilot_estimability_contract_v1_137.json"
class Stop(RuntimeError): pass

def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def dec(raw:bytes)->str:
    try:return raw.decode("utf-8").strip()
    except UnicodeDecodeError as e:raise Stop("pilot UTF-8 decode failed") from e

def load_manifest(path:Path):
    with path.open("r",encoding="utf-8",newline="") as h:rows=list(csv.DictReader(h))
    out={}
    for r in rows:
        tok=str(r["MF_token"])
        if tok in out:raise Stop("duplicate pilot MF token manifest row")
        out[tok]=int(r["occurrence_rows"])
    return out

def load_event_map(path:Path):
    with path.open("r",encoding="utf-8",newline="") as h:rows=list(csv.DictReader(h))
    out={};islands=set();phases=set()
    for r in rows:
        eid=str(r["eventID"]).strip()
        if not eid:raise Stop("blank pitfall eventID")
        key=(str(r["phase"]).strip(),str(r["island"]).strip())
        if eid in out and out[eid]!=key:raise Stop("pitfall eventID maps to conflicting phase/island")
        out[eid]=key;phases.add(key[0]);islands.add(key[1])
    if phases!={"BALA1","BALA2","BALA3"}:raise Stop("pitfall phase set drift")
    if len(islands)!=7:raise Stop("pitfall island count drift")
    return out,sorted(islands)

def unique_nonblank(vals):
    return sorted({str(x).strip() for x in vals if str(x).strip()})

def eligible_taxon(tax):
    sci=unique_nonblank(tax["scientificName"])
    order=unique_nonblank(tax["order"])
    family=unique_nonblank(tax["family"])
    rank=unique_nonblank(tax["taxonRank"])
    if any(len(x)>1 for x in (sci,order,family,rank)):
        return False,"taxonomy_conflict",sci,order,family,rank
    if len(order)!=1:
        return False,"order_missing",sci,order,family,rank
    o=order[0].casefold();f=family[0].casefold() if len(family)==1 else ""
    mentions=" ".join(sci+order+family+rank).casefold()
    if "acari" in mentions or "collembola" in mentions:
        return False,"metadata_excluded_group",sci,order,family,rank
    if o=="diptera":
        return False,"diptera_not_morphospecies_resolved",sci,order,family,rank
    if o=="hymenoptera" and f!="formicidae":
        return False,"non_formicidae_hymenoptera_not_morphospecies_resolved",sci,order,family,rank
    return True,"eligible",sci,order,family,rank

def qnum(s):
    try:x=decimal.Decimal(s)
    except decimal.InvalidOperation as e:raise Stop(f"nonnumeric organismQuantity: {s!r}") from e
    if not x.is_finite() or x<0:raise Stop(f"invalid organismQuantity: {s!r}")
    return x

def write(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8",newline="") as h:
        w=csv.DictWriter(h,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("pilot_surface",type=Path)
    ap.add_argument("pilot_token_manifest",type=Path)
    ap.add_argument("pitfall_position_recovery",type=Path)
    ap.add_argument("--contract",type=Path,default=DEFAULT_CONTRACT)
    ap.add_argument("--eligibility-output",type=Path,required=True)
    ap.add_argument("--presence-output",type=Path,required=True)
    ap.add_argument("--transition-output",type=Path,required=True)
    ap.add_argument("--result",type=Path,required=True)
    a=ap.parse_args()
    try:
        c=json.loads(a.contract.read_text())
        if c["schema"]!="structural.bala_pilot_estimability_contract.v1_137":raise Stop("contract schema drift")
        if sha(a.pilot_surface)!=c["pilot_input"]["pilot_surface_sha256"]:raise Stop("pilot surface SHA drift")
        if sha(a.pilot_token_manifest)!=c["pilot_input"]["pilot_token_manifest_sha256"]:raise Stop("pilot token manifest SHA drift")
        if sha(a.pitfall_position_recovery)!=c["surveyed_zero_surface"]["pitfall_position_recovery_sha256"]:raise Stop("pitfall recovery SHA drift")
        expected=load_manifest(a.pilot_token_manifest)
        if len(expected)!=c["pilot_input"]["pilot_distinct_taxa"]:raise Stop("pilot token count drift")
        event_map,islands=load_event_map(a.pitfall_position_recovery)

        idx=c["pilot_decoded_fields"];nfields=32
        raw=a.pilot_surface.read_bytes();lines=raw.splitlines()
        if len(lines)<2:raise Stop("pilot surface empty")
        data=lines[1:]
        if len(data)!=c["pilot_input"]["pilot_occurrence_rows"]:raise Stop("pilot row count drift")

        tax=defaultdict(lambda:defaultdict(list))
        observed=defaultdict(set)
        row_counts=Counter();core_positive=Counter()
        decoded_quantity=decoded_coreid=decoded_eventid=decoded_taxonomy=0
        eventid_coreid_mismatch=0
        for rn,line in enumerate(data,1):
            fields=line.split(b"\t")
            if len(fields)!=nfields:raise Stop(f"pilot field-count drift row {rn}")
            token=dec(fields[idx["identificationRemarks"]])
            if token not in expected:raise Stop("pilot token outside frozen manifest")
            row_counts[token]+=1
            coreid=dec(fields[idx["coreid"]]);decoded_coreid+=1
            quantity=qnum(dec(fields[idx["organismQuantity"]]));decoded_quantity+=1
            eventid=dec(fields[idx["eventID"]]);decoded_eventid+=1
            sci=dec(fields[idx["scientificName"]]);order=dec(fields[idx["order"]]);family=dec(fields[idx["family"]]);rank=dec(fields[idx["taxonRank"]]);decoded_taxonomy+=4
            tax[token]["scientificName"].append(sci);tax[token]["order"].append(order);tax[token]["family"].append(family);tax[token]["taxonRank"].append(rank)
            if eventid and coreid and eventid!=coreid:eventid_coreid_mismatch+=1
            if quantity>0 and coreid in event_map:
                phase,island=event_map[coreid]
                observed[token].add((island,phase));core_positive[token]+=1

        if row_counts!=Counter(expected):raise Stop("pilot row counts do not reproduce token manifest")

        eligibility=[];eligible=[]
        for token in sorted(expected):
            ok,reason,sci,order,family,rank=eligible_taxon(tax[token])
            eligibility.append({
              "MF_token":token,"eligible":str(ok).lower(),"reason":reason,
              "scientificName":";".join(sci),"order":";".join(order),"family":";".join(family),"taxonRank":";".join(rank),
              "occurrence_rows":row_counts[token],"eligible_core_positive_rows":core_positive[token]
            })
            if ok:eligible.append(token)

        presence=[];summaries=[]
        for token in eligible:
            byphase={}
            for ph in ("BALA1","BALA2","BALA3"):
                ss={isl for isl in islands if (isl,ph) in observed[token]};byphase[ph]=ss
                for isl in islands:
                    presence.append({"MF_token":token,"island":isl,"phase":ph,"present":int(isl in ss)})
            p0,p1,p2=byphase["BALA1"],byphase["BALA2"],byphase["BALA3"]
            lost=p0-p1
            contractions=p1-p2
            persist=p1&p2
            multisource=len(p0)>=2
            anyloss=multisource and len(lost)>=1 and len(p1)>=1
            one=multisource and len(lost)==1 and len(p1)>=1
            summaries.append({
              "MF_token":token,
              "t0_occupied_islands":len(p0),"t1_occupied_islands":len(p1),"t2_occupied_islands":len(p2),
              "t0_to_t1_lost_sources":len(lost),"t1_survivor_targets":len(p1),
              "t1_to_t2_contractions":len(contractions),"t1_to_t2_persistences":len(persist),
              "at_least_two_t0_sources":str(multisource).lower(),
              "any_source_loss_with_t1_survivor":str(anyloss).lower(),
              "exactly_one_source_loss":str(one).lower(),
              "within_taxon_both_t2_outcomes":str(one and len(contractions)>0 and len(persist)>0).lower()
            })

        one=[r for r in summaries if r["exactly_one_source_loss"]=="true"]
        gate=c["advance_gate"]
        metrics={
          "taxonomically_eligible_pilot_taxa":len(eligible),
          "taxa_with_at_least_two_t0_sources":sum(r["at_least_two_t0_sources"]=="true" for r in summaries),
          "taxa_with_any_t0_to_t1_source_loss_and_t1_survivor":sum(r["any_source_loss_with_t1_survivor"]=="true" for r in summaries),
          "exactly_one_source_loss_taxa":len(one),
          "exactly_one_loss_target_rows":sum(int(r["t1_survivor_targets"]) for r in one),
          "t2_contractions_across_exactly_one_loss_targets":sum(int(r["t1_to_t2_contractions"]) for r in one),
          "t2_persistences_across_exactly_one_loss_targets":sum(int(r["t1_to_t2_persistences"]) for r in one),
          "taxon_clusters_with_at_least_one_contraction":sum(int(r["t1_to_t2_contractions"])>0 for r in one),
          "taxon_clusters_with_at_least_one_persistence":sum(int(r["t1_to_t2_persistences"])>0 for r in one),
          "taxa_with_within_taxon_both_t2_outcomes":sum(r["within_taxon_both_t2_outcomes"]=="true" for r in one)
        }
        checks={
          "taxonomically_eligible_pilot_taxa":metrics["taxonomically_eligible_pilot_taxa"]>=gate["minimum_taxonomically_eligible_pilot_taxa"],
          "taxa_with_at_least_two_t0_sources":metrics["taxa_with_at_least_two_t0_sources"]>=gate["minimum_taxa_with_at_least_two_t0_sources"],
          "taxa_with_any_t0_to_t1_source_loss_and_t1_survivor":metrics["taxa_with_any_t0_to_t1_source_loss_and_t1_survivor"]>=gate["minimum_taxa_with_any_t0_to_t1_source_loss_and_t1_survivor"],
          "exactly_one_source_loss_taxa":metrics["exactly_one_source_loss_taxa"]>=gate["minimum_exactly_one_source_loss_taxa"],
          "exactly_one_loss_target_rows":metrics["exactly_one_loss_target_rows"]>=gate["minimum_exactly_one_loss_target_rows"],
          "t2_contractions":metrics["t2_contractions_across_exactly_one_loss_targets"]>=gate["minimum_t2_contractions_across_exactly_one_loss_targets"],
          "t2_persistences":metrics["t2_persistences_across_exactly_one_loss_targets"]>=gate["minimum_t2_persistences_across_exactly_one_loss_targets"],
          "clusters_with_contraction":metrics["taxon_clusters_with_at_least_one_contraction"]>=gate["minimum_taxon_clusters_with_at_least_one_contraction"],
          "clusters_with_persistence":metrics["taxon_clusters_with_at_least_one_persistence"]>=gate["minimum_taxon_clusters_with_at_least_one_persistence"],
          "within_taxon_both":metrics["taxa_with_within_taxon_both_t2_outcomes"]>=gate["minimum_taxa_with_within_taxon_both_t2_outcomes"]
        }
        passed=all(checks.values())

        write(a.eligibility_output,eligibility,["MF_token","eligible","reason","scientificName","order","family","taxonRank","occurrence_rows","eligible_core_positive_rows"])
        write(a.presence_output,presence,["MF_token","island","phase","present"])
        write(a.transition_output,summaries,["MF_token","t0_occupied_islands","t1_occupied_islands","t2_occupied_islands","t0_to_t1_lost_sources","t1_survivor_targets","t1_to_t2_contractions","t1_to_t2_persistences","at_least_two_t0_sources","any_source_loss_with_t1_survivor","exactly_one_source_loss","within_taxon_both_t2_outcomes"])
        result={
          "schema":"structural.bala_pilot_estimability_result.v1_137",
          "status":"BALA_PILOT_ESTIMABILITY_GATE_PASSED" if passed else "BALA_PILOT_ESTIMABILITY_GATE_STOPPED",
          "pilot_taxa_routed":len(expected),"pilot_occurrence_rows_decoded":len(data),
          "pilot_taxonomically_eligible_taxa":len(eligible),
          "decoded_coreid_values":decoded_coreid,"decoded_organismQuantity_values":decoded_quantity,
          "decoded_eventID_values":decoded_eventid,"decoded_taxonomy_values":decoded_taxonomy,
          "eventID_coreid_mismatch_rows":eventid_coreid_mismatch,
          "metrics":metrics,"gate_checks":checks,"advance_authorized":passed,
          "eligibility_sha256":sha(a.eligibility_output),"presence_sha256":sha(a.presence_output),"transition_sha256":sha(a.transition_output),
          "source_leverage_values_computed":0,"candidate_minus_reference_effects_computed":0,
          "confirmatory_rows_parsed":0,"confirmatory_token_identities_opened":0,"confirmatory_occurrence_values_opened":0,
          "counts_as_empirical_support_or_non_support":False
        };code=0
    except (OSError,KeyError,ValueError,TypeError,json.JSONDecodeError,decimal.InvalidOperation,Stop) as e:
        result={"schema":"structural.bala_pilot_estimability_result.v1_137","status":"IMPLEMENTATION_STOP","reason":str(e),
          "source_leverage_values_computed":0,"candidate_minus_reference_effects_computed":0,
          "confirmatory_rows_parsed":0,"confirmatory_occurrence_values_opened":0,"advance_authorized":False,
          "counts_as_empirical_support_or_non_support":False};code=2
    a.result.parent.mkdir(parents=True,exist_ok=True);a.result.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True));return code

if __name__=="__main__":raise SystemExit(main())
