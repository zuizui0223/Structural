// Prospective EMEND design core; source adapter and identity audit required. Synthetic checks only.
function components(vectors) {
  if(vectors.length<2) throw Error("at least two site-change vectors required");
  const p=vectors[0].length,n=vectors.length;
  if(p===0||vectors.some(x=>x.length!==p||x.some(v=>!Number.isFinite(v))))throw Error("invalid vector");
  const dot=(a,b)=>a.reduce((s,v,j)=>s+v*b[j],0);
  let T=0,pair=0;
  for(let i=0;i<n;i++){T+=dot(vectors[i],vectors[i]);for(let j=0;j<i;j++)pair+=dot(vectors[i],vectors[j]);}
  T/=n;const U=2*pair/(n*(n-1));
  return {n,T,U,M:(T+(n-1)*U)/n};
}
function emendDesignCore(rows) {
  // Author-method labels canonicalized only by a separately verified source adapter.
  // Input rows: verified physical compartment, block, cover type, treatment, year,
  // study-wide binary incidence vector. No raw source loader.
  const types=["DDOM","DDOMU","MX","CDOM"],treatments=["R0","R10","R20","R50","R75","CT"],years=[1999,2000];
  if(rows.length!==144)throw Error("complete 72x2 frame required");
  const index=new Map(),comp=new Map(),blocks=new Map(),p=rows[0].incidence.length;
  for(const r of rows){
    if(!types.includes(r.cover)||!treatments.includes(r.treatment)||!years.includes(r.year)||typeof r.compartment!=="string"||!r.compartment.trim()||typeof r.block!=="string"||!r.block.trim())throw Error("invalid source identity");
    if(!Array.isArray(r.incidence)||r.incidence.length!==p||r.incidence.some(v=>v!==0&&v!==1))throw Error("incidence axis invalid");
    const richness=r.incidence.reduce((s,v)=>s+v,0);if(richness===0)throw Error("empty community requires explicit prior protocol; STOP");
    const group=JSON.stringify([r.cover,r.treatment,r.block]),key=JSON.stringify([r.cover,r.treatment,r.block,r.year]),canon=JSON.stringify([r.cover,r.treatment,r.block]);
    if(index.has(key))throw Error("duplicate block treatment year");
    if(comp.has(r.compartment)&&comp.get(r.compartment)!==canon)throw Error("compartment identity conflict");
    comp.set(r.compartment,canon);
    if(!blocks.has(r.cover))blocks.set(r.cover,new Set());
    blocks.get(r.cover).add(r.block);
    index.set(key,{compartment:r.compartment,v:r.incidence.map(v=>v/Math.sqrt(richness))});
  }
  if(comp.size!==72||types.some(c=>blocks.get(c)?.size!==3))throw Error("block or compartment support mismatch");
  const byCover=types.map(cover=>{
    const result={cover,byTreatment:{}};
    for(const treatment of treatments){
      const delta=Array.from(blocks.get(cover)).sort().map(block=>{
        const a=index.get(JSON.stringify([cover,treatment,block,1999])),b=index.get(JSON.stringify([cover,treatment,block,2000]));
        if(!a||!b||a.compartment!==b.compartment)throw Error("annual compartment crosswalk conflict");
        return b.v.map((v,j)=>v-a.v[j]);
      });
      result.byTreatment[treatment]=components(delta);
    }
    const a=result.byTreatment.R0,b=result.byTreatment.CT;
    result.R0minusCT={T:a.T-b.T,U:a.U-b.U};
    return result;
  });
  const primary=Object.fromEntries(["T","U"].map(k=>[k,byCover.reduce((s,r)=>s+r.R0minusCT[k],0)/4]));
  return {byCover,primaryR0minusCT:primary,jointDirection:primary.T>0&&primary.U<0,ecologicalPopulationPValue:null};
}
function test() {
  const a=components([[1,0],[1,0],[1,0]]),b=components([[-1,0],[-1,0],[-1,0]]),pooled=components([[1,0],[1,0],[1,0],[-1,0],[-1,0],[-1,0]]);
  if(a.U!==1||b.U!==1||Math.abs(pooled.U+0.2)>1e-12)throw Error("stratification fixture failed");
  const rows=[];
  for(const cover of ["DDOM","DDOMU","MX","CDOM"])for(const treatment of ["R0","R10","R20","R50","R75","CT"])for(let k=0;k<3;k++)for(const year of [1999,2000]){
    let incidence=[1,0,0,0];
    if(year===2000&&treatment==="R0"){incidence=[0,0,0,0];incidence[k+1]=1;}
    rows.push({cover,treatment,block:"b"+k,compartment:cover+"-"+treatment+"-"+k,year,incidence});
  }
  const q=emendDesignCore(rows);
  if(q.primaryR0minusCT.T!==2||q.primaryR0minusCT.U!==1||q.jointDirection)throw Error("design known truth failed");
  let reject=false;try{emendDesignCore(rows.slice(1))}catch(e){reject=true}if(!reject)throw Error("incomplete frame accepted");
  return {within_type_U:[a.U,b.U],pooled_U:pooled.U,design_fixture:q.primaryR0minusCT,biological_rows_read:0};
}
export {components,emendDesignCore,test};
if(typeof process!=="undefined"&&process.argv.includes("--test"))console.log(JSON.stringify(test(),null,2));
