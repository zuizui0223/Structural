// Structural: method-only canonical panel/age routing and synthetic validation.
// Original source column names, anonymized replicate identity and reference panel semantics
// must be verified using the public author codebook BEFORE any real call.
// No fetch, no source reader, no ecological p-values. Do not run against guessed IDs.
// SPDX-License-Identifier: MIT
function prepareRoutes(trt, ref) {
  const fail = m => {throw new Error(m)};
  const exact = (r, names) => Object.keys(r).sort().join("|")===names.slice().sort().join("|");
  const valid = x => typeof x==="string" && x.trim()===x && x.length>0;
  const key = a => JSON.stringify(a);
  const scope = r => key([r.dataset,r.forest,r.guild]);
  const rr=new Map(), hh=new Map();
  for(const r of ref){
    if(!exact(r,["dataset","forest","guild","panel","a","b"])||!Object.values(r).every(valid)||r.a===r.b)fail("INVALID_RR_ROUTING");
    const s=key([scope(r),r.panel]), p=key([r.a,r.b].sort());
    if(!rr.has(s))rr.set(s,new Set());
    if(rr.get(s).has(p))fail("DUPLICATE_UNORDERED_RR_PAIR");
    rr.get(s).add(p);
  }
  for(const r of trt){
    if(!exact(r,["dataset","forest","guild","panel","harvest","reference","age"])||!["dataset","forest","guild","panel","harvest","reference"].every(k=>valid(r[k]))||typeof r.age!=="number"||!Number.isFinite(r.age)||r.age<0)fail("INVALID_TR_ROUTING");
    const s=scope(r), h=key([s,r.harvest]);
    if(!hh.has(h))hh.set(h,{dataset:r.dataset,forest:r.forest,guild:r.guild,panel:r.panel,harvest:r.harvest,age:r.age,refs:new Set()});
    const x=hh.get(h);
    if(x.age!==r.age||x.panel!==r.panel)fail("HARVEST_ID_AGE_OR_PANEL_CONFLICT");
    if(x.refs.has(r.reference))fail("DUPLICATE_TR_PAIR");
    x.refs.add(r.reference);
  }
  const groups=new Map();
  let excludedNoRR=0;
  for(const h of hh.values()){
    const refs=[...h.refs].sort(), p=key([scope(h),h.panel]), pairs=[];
    for(let a=0;a<refs.length;a++)for(let b=a+1;b<refs.length;b++)pairs.push(key([refs[a],refs[b]]));
    if(refs.length<2||!rr.has(p)||!pairs.every(x=>rr.get(p).has(x))){excludedNoRR++;continue;}
    const g=key([scope(h),h.panel,refs]);
    if(!groups.has(g))groups.set(g,{dataset:h.dataset,forest:h.forest,guild:h.guild,panel:h.panel,refs,pairs,harvests:[]});
    groups.get(g).harvests.push({harvest:h.harvest,age:h.age});
  }
  const eligible=[],excludedAgeSupport=[];
  for(const g of groups.values()){
    const n=new Map();for(const h of g.harvests)n.set(h.age,(n.get(h.age)||0)+1);
    if(n.size<2||[...n.values()].some(x=>x<2)){excludedAgeSupport.push(g);continue;}
    eligible.push(g);
  }
  const summaries=new Map();
  for(const g of eligible){const k=key([g.forest,g.guild]);if(!summaries.has(k))summaries.set(k,new Set());summaries.get(k).add(g.dataset);}
  return {eligible,report:{routing_only:true,harvest_units:hh.size,eligible_panels:eligible.length,eligible_harvest_units:eligible.reduce((a,g)=>a+g.harvests.length,0),excluded_harvest_no_complete_rr:excludedNoRR,excluded_panels_age_support:excludedAgeSupport.length,eligible_datasets_by_forest_guild:[...summaries].map(([k,v])=>({stratum:JSON.parse(k),datasets:v.size})),original_outcomes_scored:0}};
}
function evaluateRoutes(routes,trtSimilarity,rrSimilarity){
  const key=a=>JSON.stringify(a);
  const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
  const get=(m,k)=>{const x=m.get(k);if(typeof x!=="number"||!Number.isFinite(x)||x<0||x>1)throw Error("MISSING_OR_INVALID_SIMILARITY");return x};
  const slope=(a,b)=>{const x=mean(a),y=mean(b),den=a.reduce((s,v)=>s+(v-x)**2,0);return den===0?null:a.reduce((s,v,i)=>s+(v-x)*(b[i]-y),0)/den};
  const byStratum=new Map();
  for(const g of routes.eligible){
    const s=[g.dataset,g.forest,g.guild,g.panel];
    const baseline=mean(g.pairs.map(p=>get(rrSimilarity,key([...s,...JSON.parse(p)]))));
    const ages=g.harvests.map(h=>h.age);
    const deficits=g.harvests.map(h=>baseline-mean(g.refs.map(r=>get(trtSimilarity,key([...s,h.harvest,r])))));
    const k=key([g.forest,g.guild]);
    if(!byStratum.has(k))byStratum.set(k,new Map());
    const datasets=byStratum.get(k);
    if(!datasets.has(g.dataset))datasets.set(g.dataset,[]);
    datasets.get(g.dataset).push({slope:slope(ages,deficits)*10,age:mean(ages),deficit:mean(deficits)});
  }
  return [...byStratum].map(([k,ds])=>{
    const d=[...ds.values()].map(a=>({within:mean(a.map(z=>z.slope)),age:mean(a.map(z=>z.age)),deficit:mean(a.map(z=>z.deficit))}));
    const b=slope(d.map(z=>z.age),d.map(z=>z.deficit));
    return {stratum:JSON.parse(k),datasets:d.length,within_deficit_slope_per_decade:mean(d.map(z=>z.within)),between_deficit_slope_per_decade:b===null?null:b*10,within_dataset_slopes:d.map(z=>z.within),inference:"descriptive; anonymized higher-study dependence unresolved"};
  });
}
function knownTruth(){
  const trt=[],ref=[],tv=new Map(),rv=new Map(),key=a=>JSON.stringify(a);
  const add=(dataset,age0,deficit0,slope,panel="fixed",nAges=2)=>{
    const forest="conifer",guild="saproxylic",s=[dataset,forest,guild,panel];
    ref.push({dataset,forest,guild,panel,a:"r1",b:"r2"});
    rv.set(key([...s,"r1","r2"]),0.8);
    for(let i=0;i<nAges;i++)for(let j=0;j<2;j++){
      const age=age0+i*10,harvest=`${panel}-${i}-${j}`,d=deficit0+slope*i;
      for(const reference of ["r1","r2"]){trt.push({dataset,forest,guild,panel,harvest,reference,age});tv.set(key([...s,harvest,reference]),0.8-d);}
    }
  };
  add("early",0,0.5,0.05);add("late",30,0.15,0.05);
  add("unsupported",10,0.3,0,"p1",1);add("unsupported",20,0.3,0,"p2",1);
  const routes=prepareRoutes(trt,ref),res=evaluateRoutes(routes,tv,rv)[0];
  if(routes.report.eligible_panels!==2||routes.report.eligible_harvest_units!==8||routes.report.excluded_panels_age_support!==2||Math.abs(res.within_deficit_slope_per_decade-0.05)>1e-12||Math.abs(res.between_deficit_slope_per_decade+0.35/3)>1e-12)throw Error("KNOWN_TRUTH_FAILED");
  let caught=0;for(const [t,r] of [[trt.concat(trt[0]),ref],[trt,ref.concat({...ref[0],a:"r2",b:"r1"})],[trt.map((z,i)=>i===0?{...z,similarity:0.4}:z),ref]]){try{prepareRoutes(t,r)}catch(e){caught++}}
  if(caught!==3)throw Error("FIREWALL_FAILED");
  const missing=new Map(tv);missing.delete(missing.keys().next().value);let missingStop=false;try{evaluateRoutes(routes,missing,rv)}catch(e){missingStop=true}if(!missingStop)throw Error("OUTCOME_DOMAIN_FAILED");
  return {status:"SYNTHETIC_ONLY_PASS",routing:routes.report,result:res,duplicate_or_extra_field_rejections:caught,missing_similarity_rejected:missingStop};
}
export {prepareRoutes,evaluateRoutes,knownTruth};
if (typeof process !== "undefined" && process.argv.includes("--test")) console.log(JSON.stringify(knownTruth(),null,2));
