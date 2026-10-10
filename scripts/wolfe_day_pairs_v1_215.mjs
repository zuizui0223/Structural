#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
const BLOB="e78003d425b646b390ae02e36c007892c1c70926";
const LEVEL=["none","low","high"];
function comb(n,k){if(k<0||k>n)return 0n;let v=1n;for(let j=1;j<=k;j++)v=v*BigInt(n-j+1)/BigInt(j);return v}
export function pairP(D,T){
 if(!Number.isInteger(D)||D<0||D>72||!Number.isInteger(T)||Math.abs(T)>D)throw Error("Invalid pair statistic");
 let num=0n;for(let j=0;j<=D;j++)if(Math.abs(2*j-D)>=Math.abs(T))num+=comb(D,j);
 return Number(num*100000000000000n/(2n**BigInt(D)))/1e14;
}
export function compute(raw){
 if(raw.length!==12096)throw Error("Bad source length");
 const hash=crypto.createHash("sha1").update(Buffer.concat([Buffer.from("blob "+raw.length+"\0"),raw])).digest("hex");
 if(hash!==BLOB)throw Error("Source SHA mismatch");
 const [header,...lines]=raw.toString("utf8").trimEnd().replace(/\r/g,"").split("\n");
 const names=header.split(","),rows=new Map(),ident=new Set();let excluded=0;
 if(lines.length!==176)throw Error("Unexpected response universe");
 for(const l of lines){
  const v=l.split(",");if(v.length!==names.length)throw Error("Unexpected CSV encoding");
  const r=Object.fromEntries(names.map((n,i)=>[n,v[i]]));
  const id=r.microcosm+"|"+r.replicate;if(ident.has(id))throw Error("Duplicate experimental replicate");ident.add(id);
  if(r[""]==="6HoLM1"){
   if(r.microcosm!=="6HoLM"||r.replicate!=="1"||r.patch_number!=="6"||
      r.heterogeneity!=="homogeneous"||r.matrix_dispersal!=="none"||r.corridor_dispersal!=="none")throw Error("Ambiguous ID changed");
   excluded++;continue;
  }
  if(r.patch_number==="1")continue;
  const n=Number(r.patch_number),m=r.matrix_dispersal,c=r.corridor_dispersal,rep=Number(r.replicate),h=r.heterogeneity;
  if(![4,6].includes(n)||!LEVEL.includes(m)||!LEVEL.includes(c)||![1,2,3,4].includes(rep)||
     !["heterogeneous","homogeneous"].includes(h))throw Error("Experimental factor mismatch");
  const x=["stentor_coeruleus","didinium_nasutum","dileptus_anser"].map(k=>Number(r[k]));
  if(x.some(z=>!Number.isFinite(z)||z<0))throw Error("Invalid focal density");
  const y=Number(x[0]>0&&(x[1]>0||x[2]>0)),k=[n,m,c,rep,h].join("|");
  if(rows.has(k))throw Error("Duplicate blocked unit");
  rows.set(k,y);
 }
 if(excluded!==1||rows.size!==139)throw Error("Selected outcomes not exactly 139");
 let pairs=[],missing=[];
 for(const n of [4,6])for(const m of LEVEL)for(const c of LEVEL)for(const rep of [1,2,3,4]){
  const a=[n,m,c,rep,"heterogeneous"].join("|"),b=[n,m,c,rep,"homogeneous"].join("|"),idx=pairs.length;
  const A=rows.get(a),B=rows.get(b);
  if(A===undefined)missing.push({i:idx,arm:"A",key:a});
  if(B===undefined)missing.push({i:idx,arm:"B",key:b});
  pairs.push({n,A,B});
 }
 const frozenMissing=["4|high|high|4|homogeneous","6|none|high|4|heterogeneous",
 "6|low|none|1|homogeneous","6|high|none|3|homogeneous","6|high|high|1|homogeneous"].sort();
 if(pairs.length!==72||missing.length!==5||
    JSON.stringify(missing.map(z=>z.key).sort())!==JSON.stringify(frozenMissing))throw Error("Missingness source mismatch");
 let cases=[];
 for(let mask=0;mask<32;mask++){
  let filled=pairs.map(z=>({...z}));
  for(let i=0;i<5;i++)filled[missing[i].i][missing[i].arm]=(mask>>i)&1;
  let D=0,T=0,J=0;
  for(const z of filled){
   if(![0,1].includes(z.A)||![0,1].includes(z.B))throw Error("Pair not completed");
   const d=z.A-z.B;if(d!==0)D++;T+=d;J+=(z.n===6?d:-d);
  }
  cases.push({mask,discordant_pairs:D,overall:T/72,interaction_six_minus_four:J/36,
   two_sided_pairwise_null_overall:pairP(D,T),
   two_sided_pairwise_null_interaction:pairP(D,J)});
 }
 const keys=["discordant_pairs","overall","interaction_six_minus_four",
  "two_sided_pairwise_null_overall","two_sided_pairwise_null_interaction"];
 return {schema:"structural.wolfe_weekday_paired_sensitivity_result.v1_215",
   interpretation:"Hypothetical exchangeability of labels WITHIN replicate weekdays; actual random allocation not established",
   source_blob:hash,source_rows_retained:175,selected_rows:139,pairs:72,
   missing_binary:5,imputations:32,valid_randomization_p_values:false,
   ranges:Object.fromEntries(keys.map(k=>[k,[Math.min(...cases.map(z=>z[k])),Math.max(...cases.map(z=>z[k]))]])),cases};
}
if(process.argv[1] && path.basename(process.argv[1])==="wolfe_day_pairs_v1_215.mjs"){
 if(process.argv.length!==4)throw Error("Input and receipt required");
 const result=compute(fs.readFileSync(process.argv[2]));
 fs.mkdirSync(path.dirname(process.argv[3]),{recursive:true});
 fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2)+"\n");
 const {cases,...short}=result;
 process.stdout.write(JSON.stringify(short)+"\n");
}
