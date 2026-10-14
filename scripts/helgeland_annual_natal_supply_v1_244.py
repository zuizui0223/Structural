#!/usr/bin/env python3
"""v1.244 (RETROSPECTIVE): dynamic natal marked-cohort supply for destination forecasts.

No island extinction, offspring rescue, source viability, or new confirmation.
Old author 2026 CMR Git blobs fixed, original v1.231 direction matrix SHA fixed.
All historical probabilities learn 1994-2013 only; 2014 excluded; score
2015-2021 known-at-birth source marked nestlings -> t+1 observed emigrant targets.
"""
import argparse,csv,hashlib,io,json,math
from collections import defaultdict,Counter
from pathlib import Path
from helgeland_directional_route_portability_v1_240 import matrix_by_era
from helgeland_habitat_pair_portability_v1_241 import (
    historical_background,historical_habitat_coef,predict)

SHA_PRESENCE="c998367c55d0d88ec17e6d1dc2931a97c46aff55"
SHA_POPULATION="c31823caff36dcd07ae30d657f8507a44ab4f7b0"
SHA_V231_FREEZE="955d58e958b2f241cda726706bec0260fea79dd5"
ISLANDS=(20,22,23,24,26,27,28,33,34,35,38)
ROUTES=("P0","H","R2","C2")
HISTORY_YEARS=tuple(range(1994,2014))
FUTURE_YEARS=tuple(range(2015,2022))
PRIMARY_ROUTE="R2"
TAU=10

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\x00"+raw).hexdigest()

def number(x):
    try:return int(str(x).strip().strip('"'))
    except (ValueError,TypeError):return None

def read_rows(raw,fields):
    reader=csv.DictReader(io.StringIO(raw.decode("utf-8-sig"),newline=""),delimiter=";")
    if not set(fields).issubset(reader.fieldnames or []):
        raise ValueError("Source did not preserve declared annual study fields")
    for r in reader:
        if None in r:raise ValueError("Source extra malformed row")
        yield r

def annual_data(raw_pres,raw_pop):
    if blob(raw_pres)!=SHA_PRESENCE or blob(raw_pop)!=SHA_POPULATION:
        raise ValueError("Author 2026 Git blob identity drift")
    ids={number(r["Island"]) for r in read_rows(raw_pop,("Island","Year","N_corr"))}
    ids.discard(None);ids.discard(0)
    if ids!=set(ISLANDS):
        raise ValueError("Eleven island IDs do not match original population model")
    births=defaultdict(set)
    adults=defaultdict(set)
    count=0
    for r in read_rows(raw_pres,("ID","Year","Island","stage")):
        count+=1
        id=str(r["ID"] or "").strip().strip('"')
        yr=number(r["Year"]);island=number(r["Island"])
        stage=str(r["stage"] or "").strip().strip('"').casefold()
        if not id or id.casefold() in ("na","nan","null"):
            continue
        if yr is None or island not in ids:
            continue
        if stage=="nest":births[id].add((yr,island))
        elif stage in ("capt","obs"):adults[(id,yr)].add(island)
    if count!=73593:
        raise ValueError("Study observation record count drift")
    annual_marks=defaultdict(Counter)
    annual_migrants=defaultdict(Counter)
    qc=Counter()
    for id,record in births.items():
        if len(record)!=1:
            qc["ambiguous_natal_ID"]+=1
            continue
        yr,source=next(iter(record))
        if yr not in HISTORY_YEARS and yr!=2014 and yr not in FUTURE_YEARS:
            continue
        annual_marks[yr][source]+=1
        destinations=adults.get((id,yr+1),set())
        if len(destinations)==1:
            j=next(iter(destinations))
            if j!=source:
                annual_migrants[yr][(source,j)]+=1
            else:
                qc["observed_natal_resident_nextyear"]+=1
        elif not destinations:
            qc["unknown_nextyear_adult_resighting"]+=1
        else:
            qc["ambiguous_nextyear_destinations"]+=1
    def sum_era(years,collection):
        return sum(sum(collection[y].values()) for y in years)
    expected=[
       (HISTORY_YEARS,9868,259),
       ((2014,),664,28),
       (FUTURE_YEARS,4484,173)]
    for years,m,e in expected:
        if sum_era(years,annual_marks)!=m or sum_era(years,annual_migrants)!=e:
            raise ValueError("Exact annual partition fails v1.231 source-locked anchors")
    return annual_marks,annual_migrants,dict(qc)

def predict_receiving(ids,route,marked,yields):
    """Distribution of destination among *documented next-year migrants*."""
    weights={}
    for target in ids:
        v=sum(marked.get(i,0)*yields[i]*route[i][target]
              for i in ids if i!=target)
        weights[target]=v
    total=sum(weights.values())
    if not math.isfinite(total) or total<=0:
        raise ValueError("No source volume to predict registered destination")
    result={j:w/total for j,w in weights.items()}
    if not math.isclose(sum(result.values()),1,abs_tol=1e-12):
        raise ValueError("Predicted destination probabilities do not sum to 1")
    return result

def compute(raw_pres,raw_pop,frozen_v231):
    marks,migrants,quality=annual_data(raw_pres,raw_pop)
    ids,matrix=matrix_by_era(frozen_v231)
    if tuple(ids)!=ISLANDS:
        raise ValueError("Frozen v1.231 islands drift")
    for era,years in (("historical",HISTORY_YEARS),("bridge",(2014,)),("later",FUTURE_YEARS)):
        for i in ids:
            for j in ids:
                if i==j:continue
                n=sum(migrants[t][(i,j)] for t in years)
                if n!=matrix[era][(i,j)]:
                    raise ValueError("Annual source-direction cells differ from pre-frozen v1.231")
    P0=historical_background(ids,matrix["historical"])
    beta,_=historical_habitat_coef(ids,matrix["historical"],P0)
    if beta!=1.85:
        raise ValueError("Previously source-locked habitat training coefficient drift")
    original_predictors=predict(ids,matrix["historical"],P0,beta,TAU)
    routes={name:{i:original_predictors[i][name] for i in ids} for name in ROUTES}
    historic_marked={i:sum(marks[t][i] for t in HISTORY_YEARS) for i in ids}
    historic_emigrant={i:sum(migrants[t][(i,j)] for t in HISTORY_YEARS for j in ids if j!=i)
                       for i in ids}
    yields={i:(historic_emigrant[i]+0.5)/(historic_marked[i]+1) for i in ids}
    static_marked={i:historic_marked[i]/len(HISTORY_YEARS) for i in ids}
    predictions={route:predict_receiving(ids,model,static_marked,yields)
                 for route,model in routes.items()}
    yearly=[]
    total_logloss={r:{"static":0.0,"dynamic":0.0} for r in ROUTES}
    total_events=0
    for year in FUTURE_YEARS:
        N=sum(migrants[year].values())
        total_events+=N
        current={i:marks[year][i] for i in ids}
        dynamic={r:predict_receiving(ids,model,current,yields)
                 for r,model in routes.items()}
        observations={j:sum(migrants[year][(i,j)] for i in ids if i!=j) for j in ids}
        yearly_loss={}
        for r in ROUTES:
            losses={"static":0.0,"dynamic":0.0}
            for j,count in observations.items():
                if count==0:continue
                for mode,probs in (("static",predictions[r]),("dynamic",dynamic[r])):
                    probability=probs[j]
                    if probability<=0:
                        raise ValueError("A true later migrant got zero predicted probability")
                    losses[mode]-=count*math.log(probability)
            yearly_loss[r]={key:(value/N if N else None) for key,value in losses.items()}
            yearly_loss[r]["dynamic_minus_static"]=(
                (losses["dynamic"]-losses["static"])/N if N else None)
            for mode in ("static","dynamic"):
                total_logloss[r][mode]+=losses[mode]
        yearly.append({
           "birth_year":year,"known_at_birth_natal_marked_total":sum(current.values()),
           "known_at_birth_natal_marked_by_island":{str(i):current[i] for i in ids},
           "test_documented_nextyear_immigrants":N,
           "test_documented_immigrants_by_recipient":{str(j):observations[j] for j in ids},
           "all_routes":yearly_loss
        })
    if total_events!=173:
        raise ValueError("Registered future migrant anchor changed")
    all_routes={}
    for route,scores in total_logloss.items():
        avg={key:scores[key]/total_events for key in ("static","dynamic")}
        all_routes[route]={"test_static_logloss":avg["static"],
                           "test_dynamic_logloss":avg["dynamic"],
                           "dynamic_minus_static":avg["dynamic"]-avg["static"]}
    return {
       "schema":"structural.helgeland_annual_natal_source_supply_v1_244",
       "status":"POSTPUBLICATION_TEMPORALLY_HELDOUT_MARKED_NATAL_SOURCE_VOLUME_PREDICTION",
       "training_historical_marked_total":sum(historic_marked.values()),
       "training_historical_movers":sum(historic_emigrant.values()),
       "test_future_marked_total":sum(sum(marks[y].values()) for y in FUTURE_YEARS),
       "test_future_documented_movers":total_events,
       "2014_boundary_marked_and_movers_excluded":[sum(marks[2014].values()),sum(migrants[2014].values())],
       "training_historical_only_farm_coefficient":beta,
       "historical_emigration_yields_of_marked_cohorts":{str(i):yields[i] for i in ids},
       "historical_annual_mean_marked_by_natal_island":{str(i):static_marked[i] for i in ids},
       "main_route":"R2 undirected pair smoothed with known habitat baseline, tau=10",
       "main_primary_dynamic_minus_static":all_routes[PRIMARY_ROUTE]["dynamic_minus_static"],
       "all_predeclared_route_sensitivities":all_routes,
       "all_seven_test_birth_years":yearly,
       "source_quality":quality,
       "future_resighting_destinations_only_test_labels":True,
       "source_nest_marking_effort_is_not_true_biological_production":True,
       "original_CMR_Ncorr_not_used_due_to_full_record_fit":True,
       "no_distance_or_source_population_viability_adjustment":True,
       "no_island_extinction_colonization_or_causal_rescue_inferred":True,
       "single_published_archipelago_and_postpublication_records":True,
       "new_confirmatory_evidence":False,
       "original_GEB_mammal_heldout_unopened":True,
       "GEB_scientific_HOLD":True,"eBird_used":False
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("author",type=Path)
    parser.add_argument("frozen_v231",type=Path)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    raw=args.frozen_v231.read_bytes()
    if blob(raw)!=SHA_V231_FREEZE:
        raise ValueError("Original v1.231 source Git blob mismatch")
    root=args.author/"Data"
    res=compute((root/"presence_data_1994_2022.txt").read_bytes(),
                (root/"estimated_pop_sizes_nestling_to_adult_model_with_lurøy_onøy.txt").read_bytes(),
                json.loads(raw))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(res,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "schema":res["schema"],"status":res["status"],
        "yearly_source_supply_additional_info_R2":res["main_primary_dynamic_minus_static"],
        "all_routes":res["all_predeclared_route_sensitivities"],
        "yearly":[{"birth_year":x["birth_year"],
                   "n_test_immigrants":x["test_documented_nextyear_immigrants"],
                   "R2_delta":x["all_routes"]["R2"]["dynamic_minus_static"]}
                  for x in res["all_seven_test_birth_years"]]
    },sort_keys=True))
if __name__=="__main__":
    main()
