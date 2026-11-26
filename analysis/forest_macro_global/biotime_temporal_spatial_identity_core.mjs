// Matched-site centered community identity statistic. Synthetic tests only; no raw source loading.
// For incidence, use a fixed study-wide taxon axis and a normalized sqrt-incidence vector; actual sampling eligibility is external.
function persistence(year0, year1){
  if(year0.length!==year1.length||year0.length<2)throw Error("same verified sites required");
  const n=year0.length,p=year0[0].length;
  const mat=[year0,year1];
  if(!p||mat.some(a=>a.some(r=>r.length!==p||r.some(v=>!Number.isFinite(v)))))throw Error("invalid matrix");
  const means=mat.map(a=>Array.from({length:p},(_,k)=>a.reduce((s,r)=>s+r[k],0)/n));
  const sums=[0,0];let cov=0,temporal=0;
  for(let i=0;i<n;i++)for(let j=0;j<p;j++){const x=year0[i][j]-means[0][j],y=year1[i][j]-means[1][j];sums[0]+=x*x;sums[1]+=y*y;cov+=x*y;temporal+=(year0[i][j]-year1[i][j])**2;}
  return {site_count:n,spatial_variance_t:sums[0]/n,spatial_variance_next:sums[1]/n,cross_year_centered_covariance:cov/n,spatial_identity_alignment:sums[0]*sums[1]>1e-24?cov/Math.sqrt(sums[0]*sums[1]):null,mean_same_site_squared_distance:temporal/n};
}
function knownTruth(){
  // binary incidence vectors with equal richness; Hellinger of incidence.
  const z=1/Math.sqrt(2);
  const a=[[z,z,0,0,0],[z,0,z,0,0],[z,0,0,z,0]];
  const commonShift=a.map(r=>[0,r[1],r[2],r[3],z]);
  const swap=[a[1],a[2],a[0]];
  const uniform=a.map(()=>[z,z,0,0,0]);
  const out={same_site_identity:persistence(a,a),shared_taxon_replacement:persistence(a,commonShift),site_identity_permutation:persistence(a,swap),homogenization:persistence(a,uniform)};
  const eps=1e-10;
  if(Math.abs(out.shared_taxon_replacement.spatial_identity_alignment-1)>eps||Math.abs(out.shared_taxon_replacement.mean_same_site_squared_distance-1)>eps||Math.abs(out.site_identity_permutation.spatial_identity_alignment+0.5)>eps||out.homogenization.spatial_identity_alignment!==null)throw Error("known truth failed");
  return out;
}
export {persistence,knownTruth};
if(typeof process!=="undefined"&&process.argv.includes("--test")) console.log(JSON.stringify(knownTruth(),null,2));
