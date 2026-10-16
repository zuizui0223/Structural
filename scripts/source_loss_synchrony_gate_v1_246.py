#!/usr/bin/env python3
"""Exact known-truth counterexample: one source loss, opposite persistence opportunity.

This is a SYNTHETIC IDENTIFIABILITY GATE, not empirical Fox or butterfly data.
The outcome is ONE-STEP probability that at least one surviving source
successfully establishes at a target given independent per-source success q.
No population persistence time, colony rescue, source disappearance risk,
or causal field effect is inferred.
"""
import argparse,itertools,json,math
from fractions import Fraction as F
from pathlib import Path

Q_GRID=(F(1,4),F(1,2),F(3,4),F(4,5),F(9,10),F(1,1))

def cases():
    before={bits:F(1,8) for bits in itertools.product((0,1),repeat=3)}
    neutral={bits:F(1,4) for bits in itertools.product((0,1),repeat=2)}
    # Exactly one donor alive in every post-loss asynchrony state
    anti={(0,1):F(1,2),(1,0):F(1,2)}
    # Exactly two alive together or none alive
    synced={(0,0):F(1,2),(1,1):F(1,2)}
    return {"three_independent_pre":before,
            "two_independent_post":neutral,
            "two_anticorrelated_post":anti,
            "two_perfectly_synchronized_post":synced}

def joint_validate(dist,expected_length):
    if not dist or any(len(k)!=expected_length for k in dist):
        raise ValueError("Mixed source statuses")
    if any(not isinstance(p,F) or p<0 for p in dist.values()):
        raise ValueError("Probability must be exact nonnegative rational")
    if sum(dist.values())!=1:
        raise ValueError("Joint source states must have unit probability")
    marginals=[sum(p*state[i] for state,p in dist.items())
               for i in range(expected_length)]
    if marginals!=[F(1,2)]*expected_length:
        raise ValueError("All nominal source marginals must be exactly 1/2")
    return marginals

def at_least_one_establishment(joint,q):
    if not isinstance(q,F) or not (0<=q<=1):
        raise ValueError("Establishment rate q must be an exact rational in [0,1]")
    total=F(0)
    for state,weight in joint.items():
        n_alive=sum(state)
        total+=weight*(1-(1-q)**n_alive)
    return total

def no_live_donors(joint):
    return sum(weight for state,weight in joint.items() if not any(state))

def exact_sample(q):
    d=cases()
    for name,x in d.items():joint_validate(x,3 if name.startswith("three") else 2)
    before=at_least_one_establishment(d["three_independent_pre"],q)
    depleted=at_least_one_establishment(d["two_independent_post"],q)
    after_anti=at_least_one_establishment(d["two_anticorrelated_post"],q)
    after_sync=at_least_one_establishment(d["two_perfectly_synchronized_post"],q)
    direct=depleted-before
    desync=after_anti-depleted
    sync=after_sync-depleted
    if (before!=1-(1-q/2)**3 or
        depleted!=1-(1-q/2)**2 or
        after_anti!=q or after_sync!=q-q*q/2 or
        direct!= -q*(2-q)**2/8 or
        desync!=q*q/4 or sync!= -q*q/4):
        raise AssertionError("The independent exact finite-state algebra did not reconcile")
    def rational(x):return f"{x.numerator}/{x.denominator}"
    return {
      "q_exact":rational(q),"q_float":float(q),
      "preloss_source_count":3,"postloss_source_count":2,
      "all_marginal_viability_probabilities":0.5,
      "preloss_P_establishment":float(before),
      "postloss_independent_P_establishment":float(depleted),
      "postloss_anticorrelated_P_establishment":float(after_anti),
      "postloss_synchronized_P_establishment":float(after_sync),
      "direct_donor_depletion_component":float(direct),
      "post_depletion_asynchrony_component":float(desync),
      "post_depletion_synchrony_component":float(sync),
      "net_anticorrelated_minus_preloss":float(after_anti-before),
      "net_synchronized_minus_preloss":float(after_sync-before),
      "exact_fraction_components":{
        "pre":rational(before),"depleted":rational(depleted),
        "anti":rational(after_anti),"sync":rational(after_sync),
        "depletion":rational(direct),"desync":rational(desync),"synchronizing":rational(sync)
      }
    }

def run():
    d=cases()
    output=[exact_sample(q) for q in Q_GRID]
    for key,x in d.items():joint_validate(x,3 if key.startswith("three") else 2)
    none={name:float(no_live_donors(x)) for name,x in d.items()}
    if none!={"three_independent_pre":0.125,
             "two_independent_post":0.25,
             "two_anticorrelated_post":0.0,
             "two_perfectly_synchronized_post":0.5}:
        raise AssertionError("Joint failure values differ from exact truth")
    threshold=3-math.sqrt(5)
    if not (0.75<threshold<0.8):raise AssertionError("Invalid q crossover")
    def analytic(q):return -q/2+3*q*q/4-q*q*q/8
    if abs(analytic(threshold))>1e-12 or analytic(0.9)<=0 or analytic(0.5)>=0:
        raise AssertionError("Wrong exact synthetic crossover")
    return {
      "schema":"structural.source_loss_synchrony_sign_competition.known_truth.v1_246",
      "status":"SYNTHETIC_EXACT_MATH_ONLY_NOT_ECOLOGICAL_EFFECT_SIZE",
      "biological_data_accessed":False,
      "initial_donors":3,"removed_donors":1,"surviving_donors":2,
      "each_source_marginal_viability_pre_and_post":0.5,
      "no_live_donor_probability":none,
      "synthetic_q_grid_exact_fraction":["1/4","1/2","3/4","4/5","9/10","1"],
      "known_truth_results":output,
      "analytical_crossover_q":"3-sqrt(5)",
      "crossover_q_float":threshold,
      "preloss_formula":"1-(1-q/2)^3",
      "postloss_independent_formula":"1-(1-q/2)^2",
      "postloss_anticorrelated_formula":"q",
      "postloss_synchronized_formula":"q-q^2/2",
      "depletion_component_formula":"-q*(2-q)^2/8",
      "change_to_anticorrelated_dependence_formula":"q^2/4",
      "change_to_synchronized_dependence_formula":"-q^2/4",
      "net_anti_loss_vs_pre_formula":"-q/2+3*q^2/4-q^3/8",
      "Fox_2017_empirical_spatial_hydra_not_reestimated":True,
      "Matter_Roland_2009_empirical_butterfly_increase_sync_not_reestimated":True,
      "not_expected_metapopulation_persistence_or_extinction_time":True,
      "not_a_calibrated_field_recolonization_operator":True,
      "no_new_confirmatory_systems_admitted":True,
      "original_mammal_heldout_unopened":True,
      "eBird_used":False,"GEB_scientific_HOLD":True
    }

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result=run()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
if __name__=="__main__":main()
