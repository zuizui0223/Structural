#!/usr/bin/env node
/** Posthoc conditional-label permutation sensitivity, frozen published Wolfe source.
 *  18 independent 4-vs-4 strata. BigInt exact hypergeometric convolution.
 *  No claims of verified physical random assignment or preregistered p-values.
 */
import fs from "node:fs";
import crypto from "node:crypto";
const EXPECTED_SHA="e78003d425b646b390ae02e36c007892c1c70926";
const UNKNOWN_ID="6HoLM1";
const levels=["none","low","high"];
const strataSpecs=[];
for(const n of [4,6])for(const m of levels)for(const c of levels)strataSpecs.push({n,m,c});
function choose(n,k){if(k<0||k>n)return 0n;let r=1n;for(let j=1;j<=k;j++)r=r*BigInt(n-j+1)/BigInt(j);return r}
export function nullDistribution(ks,signs=null){
  let dist=new Map([[0,1n]]);
  for(let i=0;i<ks.length;i++){
    const K=ks[i];const sg=signs?signs[i]:1;
    if(!Number.isInteger(K)||K<0||K>8||![1,-1].includes(sg))throw Error("Invalid null design");
    let nxt=new Map();
    for(let j=Math.max(0,K-4);j<=Math.min(4,K);j++){
      const weight=choose(K,j)*choose(8-K,4-j),delta=sg*(2*j-K);
      for(const [t,v] of dist){
        const z=t+delta;nxt.set(z,(nxt.get(z)||0n)+weight*v);
      }
    }
    dist=nxt;
  }
  const denominator=70n**BigInt(ks.length);
  if([...dist.values()].reduce((a,b)=>a+b,0n)!==denominator)throw Error("Permutation total mismatch");
  return {dist,denominator};
}
export function pTail(obj,observed,twoSided){
  let count=0n;for(const [v,w] of obj.dist){
    if(twoSided?Math.abs(v)>=Math.abs(observed):v>=observed)count+=w;
  }
  return Number(count*100000000000000n/obj.denominator)/1e14;
}
export function analyze(raw){
  if(raw.length!==12096)throw Error("Unexpected Wolfe source size");
  const digest=crypto.createHash("sha1").update(Buffer.concat([
    Buffer.from("blob "+raw.length+"\0"),raw
  ])).digest("hex");
  if(digest!==EXPECTED_SHA)throw Error("Wolfe Git blob mismatch");
  const [header,...lines]=raw.toString("utf8").trimEnd().replace(/\r/g,"").split("\n");
  const cols=header.split(",");
  const needed=["","microcosm","replicate","patch_number","heterogeneity","matrix_dispersal",
    "corridor_dispersal","stentor_coeruleus","didinium_nasutum","dileptus_anser"];
  if(!needed.every(s=>cols.includes(s))||lines.length!==176)throw Error("Source schema or row count mismatch");
  const groups=new Map(),ids=new Set();let excluded=0;
  for(const line of lines){
    const v=line.split(",");
    if(v.length!==cols.length)throw Error("Unexpected CSV row format");
    const r=Object.fromEntries(cols.map((c,i)=>[c,v[i]]));
    const id=r.microcosm+"|"+r.replicate;
    if(ids.has(id))throw Error("Duplicate independent experiment");
    ids.add(id);
    if(r[""]===UNKNOWN_ID){
      if(r.microcosm!=="6HoLM"||r.replicate!=="1"||r.patch_number!=="6"||
         r.heterogeneity!=="homogeneous"||r.matrix_dispersal!=="none"||r.corridor_dispersal!=="none"){
        throw Error("Response-opaque identification exception changed");
      }
      excluded++;continue;
    }
    const n=Number(r.patch_number),h=r.heterogeneity,m=r.matrix_dispersal,c=r.corridor_dispersal;
    if(![4,6].includes(n) || !["homogeneous","heterogeneous"].includes(h))continue;
    if(!levels.includes(m)||!levels.includes(c))throw Error("Unknown experimental treatment");
    const x=["stentor_coeruleus","didinium_nasutum","dileptus_anser"].map(z=>Number(r[z]));
    if(x.some(z=>!Number.isFinite(z)||z<0))throw Error("Invalid focal density");
    const y=Number(x[0]>0 && (x[1]>0 || x[2]>0));
    const key=[n,h,m,c].join("|");
    if(!groups.has(key))groups.set(key,[]);
    groups.get(key).push(y);
  }
  if(excluded!==1||groups.size!==36)throw Error("Wrong exclusion or factorial");
  let pending=[],strata=[];
  for(const s of strataSpecs){
    const a=groups.get([s.n,"heterogeneous",s.m,s.c].join("|"));
    const b=groups.get([s.n,"homogeneous",s.m,s.c].join("|"));
    if(!a||!b||a.length<3||a.length>4||b.length<3||b.length>4)throw Error("Bad arm");
    let idx=strata.length;
    for(let k=a.length;k<4;k++)pending.push({index:idx,arm:"a"});
    for(let k=b.length;k<4;k++)pending.push({index:idx,arm:"b"});
    strata.push({...s,a,b});
  }
  if(pending.length!==5)throw Error("Expected exactly five unknown outcomes");
  let tested=[];
  for(let mask=0;mask<(1<<pending.length);mask++){
    const complete=strata.map(s=>({...s,aa:s.a.slice(),bb:s.b.slice()}));
    for(let j=0;j<pending.length;j++){
      const {index,arm}=pending[j];
      complete[index][arm==="a"?"aa":"bb"].push((mask>>j)&1);
    }
    if(complete.some(s=>s.aa.length!==4||s.bb.length!==4))throw Error("Incomplete imputation");
    const ks=[],sg=[],diff=[];
    for(const s of complete){
      const sa=s.aa.reduce((a,b)=>a+b,0),sb=s.bb.reduce((a,b)=>a+b,0);
      ks.push(sa+sb);sg.push(s.n===6?1:-1);diff.push(sa-sb);
    }
    const overall=diff.reduce((a,b)=>a+b,0);
    const interaction=diff.reduce((a,b,i)=>a+b*sg[i],0);
    const null0=nullDistribution(ks),null1=nullDistribution(ks,sg);
    tested.push({
      imputation_mask:mask,
      overall_contrast:overall/72,
      four_patch_contrast:diff.slice(0,9).reduce((a,b)=>a+b,0)/36,
      six_patch_contrast:diff.slice(9).reduce((a,b)=>a+b,0)/36,
      six_minus_four_contrast:interaction/36,
      p_two_sided_overall:pTail(null0,overall,true),
      p_two_sided_six_minus_four:pTail(null1,interaction,true),
      p_one_sided_overall:pTail(null0,overall,false),
      p_one_sided_six_minus_four:pTail(null1,interaction,false)
    });
  }
  const keys=["overall_contrast","four_patch_contrast","six_patch_contrast","six_minus_four_contrast",
    "p_two_sided_overall","p_two_sided_six_minus_four","p_one_sided_overall","p_one_sided_six_minus_four"];
  const ranges=Object.fromEntries(keys.map(k=>[k,[Math.min(...tested.map(z=>z[k])),Math.max(...tested.map(z=>z[k]))]]));
  return {
    schema:"structural.wolfe_assignment_permutation_sensitivity_result.v1_214",
    evidence_class:"PUBLISHED_OUTCOME_CONTEXT_EXPOSED_POSTHOC_HYPOTHETICAL_EXCHANGEABILITY",
    source_blob:digest,
    retained_source_rows:175,
    analyzed_4_and_6_patch_outcome_rows:139,
    ambiguous_row_excluded:UNKNOWN_ID,
    imputed_missing_binary_events:5,
    imputation_configurations:tested.length,
    independent_treatment_strata:18,
    p_value_interpretation:"Hypothetical exchangeability tail areas, NOT verified design-randomization p-values; 32-case missingness sensitivity and no multiplicity correction",
    exact_null_permutation_denominator:"70^18",
    ranges,
    original_mammal_topology_validated:false,
    no_retroactive_confirmatory_promotion:true,
    results_by_imputation:tested
  };
}
if(process.argv[1] && process.argv[1].split("/").pop()==="wolfe_assignment_permutation_v1_214.mjs"){
  if(process.argv.length!==4)throw Error("Specify exact immutable CSV and safe result filename");
  const out=analyze(fs.readFileSync(process.argv[2]));
  fs.mkdirSync((await import("node:path")).dirname(process.argv[3]),{recursive:true});
  fs.writeFileSync(process.argv[3],JSON.stringify(out,null,2)+"\n");
  const {results_by_imputation,...summary}=out;
  process.stdout.write(JSON.stringify(summary)+"\n");
}
