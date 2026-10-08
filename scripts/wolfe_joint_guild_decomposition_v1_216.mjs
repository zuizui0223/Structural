#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
const BLOB="e78003d425b646b390ae02e36c007892c1c70926";
const LV=["none","low","high"];
export function cellProbs(a){
 if(!Array.isArray(a)||a.length===0)throw Error("No experimental units");
 let G=0,S=0,J=0;
 for(const v of a){
  if(v.length!==2||![0,1].includes(v[0])||![0,1].includes(v[1]))throw Error("Binary guild flags required");
  G+=v[0];S+=v[1];J+=v[0]*v[1];
 }
 const g=G/a.length,s=S/a.length,j=J/a.length;
 return {G:g,S:s,J:j,independence_product:g*s,association:j-g*s};
}
export function summarize(strata){
 const out=strata.map(z=>{
  const a=cellProbs(z.heterogeneous),b=cellProbs(z.homogeneous);
  return {n:z.n,J:a.J-b.J,P:a.independence_product-b.independence_product,
    C:a.association-b.association,G:a.G-b.G,S:a.S-b.S};
 });
 const avg=(a,k)=>a.reduce((s,z)=>s+z[k],0)/a.length;
 const block=n=>{
  const arr=n?out.filter(v=>v.n===n):out;
  if(!arr.length)throw Error("No strata");
  return {joint:avg(arr,"J"),independence_product:avg(arr,"P"),
    association_component:avg(arr,"C"),generalist:avg(arr,"G"),specialist:avg(arr,"S")};
 };
 return {overall:block(),patches4:block(4),patches6:block(6)};
}
export function analyze(raw){
 if(raw.length!==12096)throw Error("Frozen source length mismatch");
 const sha=crypto.createHash("sha1").update(Buffer.concat([
  Buffer.from("blob "+raw.length+"\0"),raw])).digest("hex");
 if(sha!==BLOB)throw Error("Source commit blob mismatch");
 const [hdr,...lines]=raw.toString("utf8").trimEnd().replace(/\r/g,"").split("\n");
 const keys=hdr.split(",");
 const required=["","microcosm","replicate","patch_number","heterogeneity",
  "matrix_dispersal","corridor_dispersal","stentor_coeruleus","didinium_nasutum","dileptus_anser"];
 if(lines.length!==176||!required.every(k=>keys.includes(k)))throw Error("Unexpected source shape");
 const groups=new Map(),ids=new Set();
 let excluded=0,selected=0;
 for(const line of lines){
  const vals=line.split(",");if(vals.length!==keys.length)throw Error("Invalid fixed CSV schema");
  const r=Object.fromEntries(keys.map((k,i)=>[k,vals[i]]));
  const id=r.microcosm+"|"+r.replicate;if(ids.has(id))throw Error("Duplicate independent experimental unit");ids.add(id);
  if(r[""]==="6HoLM1"){
   if(r.microcosm!=="6HoLM"||r.replicate!=="1"||r.patch_number!=="6"||
    r.heterogeneity!=="homogeneous"||r.matrix_dispersal!=="none"||r.corridor_dispersal!=="none")
    throw Error("Ambiguous source metadata changed");
   excluded++;continue; // no biological response parsing for this unit
  }
  const n=Number(r.patch_number);if(n===1)continue;
  if(![4,6].includes(n)||!["homogeneous","heterogeneous"].includes(r.heterogeneity)||
   !LV.includes(r.matrix_dispersal)||!LV.includes(r.corridor_dispersal))throw Error("Unexpected experimental group");
  const ns=["stentor_coeruleus","didinium_nasutum","dileptus_anser"].map(k=>Number(r[k]));
  if(ns.some(x=>!Number.isFinite(x)||x<0))throw Error("Invalid density");
  const G=Number(ns[0]>0),S=Number(ns[1]>0||ns[2]>0);
  const key=[n,r.heterogeneity,r.matrix_dispersal,r.corridor_dispersal].join("|");
  if(!groups.has(key))groups.set(key,[]);
  groups.get(key).push([G,S]);selected++;
 }
 if(excluded!==1||selected!==139||groups.size!==36)throw Error("Unexpected observed trial count");
 let missing=[],strata=[];
 for(const n of [4,6])for(const m of LV)for(const c of LV){
  const a=groups.get([n,"heterogeneous",m,c].join("|"));
  const b=groups.get([n,"homogeneous",m,c].join("|"));
  if(!a||!b||a.length<3||a.length>4||b.length<3||b.length>4)throw Error("Unexpected arm size");
  const idx=strata.length;strata.push({n,heterogeneous:a,homogeneous:b});
  for(let k=a.length;k<4;k++)missing.push({idx,arm:"heterogeneous"});
  for(let k=b.length;k<4;k++)missing.push({idx,arm:"homogeneous"});
 }
 if(strata.length!==18||missing.length!==5)throw Error("Unexpected missingness pattern");
 const observedOnly=summarize(strata);
 const all=[];
 for(let mask=0;mask<1024;mask++){
  const complete=strata.map(z=>({n:z.n,
   heterogeneous:z.heterogeneous.map(v=>v.slice()),
   homogeneous:z.homogeneous.map(v=>v.slice())}));
  for(let j=0;j<5;j++){
   const flag=(mask>>(2*j))&3;
   complete[missing[j].idx][missing[j].arm].push([(flag>>1)&1,flag&1]);
  }
  if(complete.some(z=>z.heterogeneous.length!==4||z.homogeneous.length!==4))throw Error("Incomplete assignment");
  all.push(summarize(complete));
 }
 const keys2=["joint","independence_product","association_component","generalist","specialist"];
 const regions=["overall","patches4","patches6"];
 const ranges=Object.fromEntries(regions.map(region=>[
  region,Object.fromEntries(keys2.map(k=>[k,[
   Math.min(...all.map(v=>v[region][k])),Math.max(...all.map(v=>v[region][k]))
  ]]))
 ]));
 const contrastRanges={};
 for(const k of keys2){
  const diffs=all.map(z=>z.patches6[k]-z.patches4[k]);
  contrastRanges[k]=[Math.min(...diffs),Math.max(...diffs)];
 }
 for(const z of all)for(const part of regions){
  const a=z[part];if(Math.abs(a.joint-a.independence_product-a.association_component)>1e-10)throw Error("Algebraic conservation failed");
 }
 return {schema:"structural.wolfe_joint_guild_decomposition_result.v1_216",
   source_sha:sha,experimental_source_rows_used:175,selected_4_6_patch_rows:139,
   all_missing_guild_state_completions:all.length,observed_only:observedOnly,
   completion_bounds:ranges,six_minus_four_bounds:contrastRanges,
   covariance_component_is_causal_guild_interaction:false,
   effect_is_retrospective_only:true,mammal_graph_biology_validated:false};
}
if(process.argv[1] && path.basename(process.argv[1])==="wolfe_joint_guild_decomposition_v1_216.mjs"){
 if(process.argv.length!==4)throw Error("Provide exact source and result path");
 const x=analyze(fs.readFileSync(process.argv[2]));
 fs.mkdirSync(path.dirname(process.argv[3]),{recursive:true});
 fs.writeFileSync(process.argv[3],JSON.stringify(x,null,2)+"\n");
 process.stdout.write(JSON.stringify(x)+"\n");
}
