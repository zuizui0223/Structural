// Author-design and constructed scalar example only. No biological data access.
function designAudit(){
  const years=[2013,2014,2015,2016,2017,2018,2019,2021,2022,2023,2024],hosts=["beech","fir","spruce"];
  const x=hosts.flatMap(host=>years.map(year=>({host,year,age:year-2013+(host==="spruce"?0:1)})));
  const rank=rows=>{const a=rows.map(r=>r.slice());let n=0;for(let j=0;j<a[0].length;j++){let p=n;for(let i=n;i<a.length;i++)if(Math.abs(a[i][j])>Math.abs(a[p][j]))p=i;if(Math.abs(a[p][j])<1e-8)continue;[a[n],a[p]]=[a[p],a[n]];const v=a[n][j];for(let k=j;k<a[0].length;k++)a[n][k]/=v;for(let i=0;i<a.length;i++)if(i!==n){const w=a[i][j];for(let k=j;k<a[0].length;k++)a[i][k]-=w*a[n][k];}n++;if(n===a.length)break;}return n;};
  const d=x.map(r=>[1,+(r.host==="fir"),+(r.host==="spruce"),r.year-2013,r.age]);
  const tr=x.filter(r=>x.some(s=>s.host===r.host&&s.year===r.year-1));
  let withPrior=0,outside=0;
  for(const r of tr){const a=tr.filter(s=>s.host===r.host&&s.year<r.year);if(a.length){withPrior++;if(r.age>Math.max(...a.map(s=>s.age)))outside++;}}
  // Scalar known-truth construction, not a model of beetle species.
  // The structural equation has no lag: z(p,t)= common(t) + static(p).
  // Compare same-calendar-year other-plot mean and a lagged residual.
  // No held-out plot target is used for either mean.
  const mean=a=>a.reduce((s,v)=>s+v,0)/a.length;
  const example=heterogeneous=>{
    const offsets=heterogeneous?[-3,-1,1,3]:[0,0,0,0];
    let base=[],aug=[];
    for(let held=0;held<4;held++){
      const train=offsets.filter((_,i)=>i!==held);
      const mPrev=10+mean(train),mNow=15+mean(train);
      const prev=10+offsets[held],target=15+offsets[held];
      base.push((target-mNow)**2);
      aug.push((target-(mNow+prev-mPrev))**2);
    }
    return {reference_mse:mean(base),lag_residual_mse:mean(aug),causal_lag_coefficient:0};
  };
  const a={nominal_host_year_cells:x.length,design_columns:d[0].length,design_rank:rank(d),nominal_adjacent_host_year_cells:tr.length,cells_with_earlier_same_host_transition:withPrior,cells_outside_training_age_support:outside,common_time_only_example:example(false),stable_unmeasured_plot_example:example(true),original_biology_read:0};
  if(a.design_rank!==4||withPrior!==24||outside!==24||a.common_time_only_example.reference_mse!==0||a.stable_unmeasured_plot_example.lag_residual_mse>1e-20||a.stable_unmeasured_plot_example.reference_mse<=0)throw Error("DESIGN_KNOWN_TRUTH_FAIL");
  return a;
}
export {designAudit};
if(typeof process!=="undefined"&&process.argv.includes("--test")) console.log(JSON.stringify(designAudit(),null,2));
