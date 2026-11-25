// Prospective Pilis block conditional comparison; no raw source loader.
function metrics(ds){
  const n=ds.length,p=ds[0]?.length;
  if(n<2||!p||ds.some(v=>v.length!==p||v.some(x=>!Number.isFinite(x))))throw Error("invalid change vectors");
  const dot=(a,b)=>a.reduce((s,x,j)=>s+x*b[j],0);
  const T=ds.reduce((s,v)=>s+dot(v,v),0)/n;
  let s=0;for(let i=0;i<n;i++)for(let j=0;j<i;j++)s+=dot(ds[i],ds[j]);
  const U=2*s/(n*(n-1));return {T,U,M:(T+(n-1)*U)/n};
}
function pairedContrasts(pairs,allowRandomization=false){
  if(!Array.isArray(pairs)||pairs.length!==6||new Set(pairs.map(x=>x.block)).size!==6)throw Error("six distinct verified blocks required");
  const p=pairs[0].cc?.length;
  if(!p||pairs.some(x=>typeof x.block!=="string"||!x.block.trim()||!Array.isArray(x.cc)||!Array.isArray(x.control)||x.cc.length!==p||x.control.length!==p||[...x.cc,...x.control].some(v=>!Number.isFinite(v))))throw Error("invalid block vector");
  function calc(mask){
    const a=[],b=[];
    for(let i=0;i<6;i++){const x=pairs[i];if(mask&(1<<i)){a.push(x.control);b.push(x.cc);}else{a.push(x.cc);b.push(x.control);}}
    const cc=metrics(a),control=metrics(b);return {cc,control,deltaT:cc.T-control.T,deltaU:cc.U-control.U};
  }
  const observed=calc(0);
  const outcome={...observed,jointDirection:observed.deltaT>0&&observed.deltaU<0,randomization:null};
  // This Boolean is a caller assertion, not a verification of the experimental design.
  // Only enable after source-author assignment and conditional exchangeability,
  // fixed units, and an interference-compatible sharp null have been verified.
  if(allowRandomization===true){
    const perm=Array.from({length:64},(_,i)=>calc(i)),eps=1e-12;
    for(let i=0;i<64;i++){const j=63^i;if(Math.abs(perm[i].deltaT+perm[j].deltaT)>eps||Math.abs(perm[i].deltaU+perm[j].deltaU)>eps)throw Error("complement symmetry failure");}
    const pT=perm.filter(x=>x.deltaT>=observed.deltaT-eps).length/64;
    const pU=perm.filter(x=>x.deltaU<=observed.deltaU+eps).length/64;
    outcome.randomization={assignments:64,pT,pU,maxDirectionalSharpNullP:Math.max(pT,pU),jointDirectionalRejectionAt05:outcome.jointDirection&&Math.max(pT,pU)<=.05,interpretation:"conditional sharp-null test only; not a weak-null test of population average signs"};
  }
  return outcome;
}
function knownTruth(){
  const pairs=Array.from({length:6},(_,i)=>({block:`b${i}`,cc:i<3?[-1,1]:[1,-1],control:[1-1/Math.sqrt(2),-1/Math.sqrt(2)]}));
  const a=pairedContrasts(pairs),b=pairedContrasts(pairs,true);
  if(a.randomization!==null||!a.jointDirection||Math.abs(a.cc.T-2)>1e-12||Math.abs(a.cc.U+.4)>1e-12||b.randomization.assignments!==64)throw Error("known truth failed");
  const identical=pairs.map(x=>({...x,cc:x.control.slice()}));
  const c=pairedContrasts(identical,true);
  if(c.randomization.pT!==1||c.randomization.pU!==1||c.jointDirection)throw Error("sharp-null ties failed");
  let stopped=false;try{pairedContrasts(pairs.slice(1))}catch(e){stopped=true}if(!stopped)throw Error("incomplete frame accepted");
  return {syntheticAlternative:b,syntheticIdentical:c,originalBiologicalRowsRead:0};
}
export {metrics,pairedContrasts,knownTruth};
if(typeof process!=="undefined"&&process.argv.includes("--test"))console.log(JSON.stringify(knownTruth(),null,2));
