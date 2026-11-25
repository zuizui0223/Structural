// Aggregate-only descriptive decomposition of consumed original receipts. No original occurrence values read.
// Brazil modified/reference keys refer to literal E/F codes, not authenticated habitats.
const frozen={
  "Germany": {
    "sourceRun": 45541446158,
    "years": [
      {
        "year": 2008,
        "modified": {
          "n": 22,
          "T": 1.0735631588642256,
          "M": 0.10507580034038042,
          "A": 0.12692350610069605
        },
        "reference": {
          "n": 22,
          "T": 0.9966145181939485,
          "M": 0.15864165685347886,
          "A": 0.08919363062223172
        }
      },
      {
        "year": 2009,
        "modified": {
          "n": 22,
          "T": 1.0417019704536719,
          "M": 0.07538871253461574,
          "A": 0.15640518067323889
        },
        "reference": {
          "n": 22,
          "T": 0.9151654411680652,
          "M": 0.0952923752435826,
          "A": 0.10462863459037351
        }
      },
      {
        "year": 2010,
        "modified": {
          "n": 22,
          "T": 1.0477547757907177,
          "M": 0.07128140783069978,
          "A": 0.1364937329416903
        },
        "reference": {
          "n": 22,
          "T": 0.9540494522016254,
          "M": 0.10024772781085275,
          "A": 0.12640109629435414
        }
      }
    ]
  },
  "Brazil": {
    "sourceRun": 45585210678,
    "years": [
      {
        "year": 2009,
        "modified": {
          "n": 15,
          "T": 0.8694740922571967,
          "M": 0.10001030746856676,
          "A": 0.37946930381361943
        },
        "reference": {
          "n": 12,
          "T": 0.801072065607968,
          "M": 0.12900683764365609,
          "A": 0.1796808632638019
        },
        "observedExhaustiveM8": {
          "modified": 0.14810179401785603,
          "reference": 0.1595552570965791
        }
      },
      {
        "year": 2010,
        "modified": {
          "n": 15,
          "T": 0.9884952090282625,
          "M": 0.05578724571168031,
          "A": 0.31324218879713667
        },
        "reference": {
          "n": 12,
          "T": 0.7597173815237439,
          "M": 0.11339055903147191,
          "A": 0.23725508179289664
        },
        "observedExhaustiveM8": {
          "modified": 0.11408149341896819,
          "reference": 0.14276905096293918
        }
      },
      {
        "year": 2011,
        "modified": {
          "n": 15,
          "T": 1.1177084474561076,
          "M": 0.1131824078805038,
          "A": 0.18932707974807722
        },
        "reference": {
          "n": 12,
          "T": 0.8171055049649314,
          "M": 0.1123221203253485,
          "A": 0.16000533959466345
        },
        "observedExhaustiveM8": {
          "modified": 0.17596528535397926,
          "reference": 0.14435772871805896
        }
      },
      {
        "year": 2012,
        "modified": {
          "n": 15,
          "T": 0.9072306725390048,
          "M": 0.0784030655465468,
          "A": 0.22121218043519694
        },
        "reference": {
          "n": 12,
          "T": 0.686620508336437,
          "M": 0.08367474561011065,
          "A": 0.25225224091367426
        },
        "observedExhaustiveM8": {
          "modified": 0.1302047909835744,
          "reference": 0.11108137118858089
        }
      }
    ]
  }
};
function coherence(x){if(!Number.isInteger(x.n)||x.n<2||!Number.isFinite(x.T)||!Number.isFinite(x.M)||x.T<0||x.M<0||x.M>x.T+1e-10)throw Error("Invalid aggregate");return (x.n*x.M-x.T)/(x.n-1);}
function subsetCentroid(x,k){if(!Number.isInteger(k)||k<1||k>x.n)throw Error("Invalid subset size");const U=coherence(x);return U+(x.T-U)/k;}
function calculate(data){
 const result={};
 for(const [region,d] of Object.entries(data)){
   const rows=d.years.map(y=>{
     const U=coherence(y.modified)-coherence(y.reference),T=y.modified.T-y.reference.T,A=y.modified.A-y.reference.A;
     if(y.observedExhaustiveM8)for(const group of ["modified","reference"])if(Math.abs(subsetCentroid(y[group],8)-y.observedExhaustiveM8[group])>1e-12)throw Error("Exhaustive subset mismatch");
     return {year:y.year,U,T,A};
   });
   const mean={};for(const k of ["U","T","A"])mean[k]=rows.reduce((s,r)=>s+r[k],0)/rows.length;
   const cap=Math.min(...d.years.flatMap(y=>[y.modified.n,y.reference.n]));
   result[region]={rows,mean,descriptiveCrossover:mean.U<0&&mean.T>0?1-mean.T/mean.U:null,expectedMatchedCountContrast:Array.from({length:cap},(_,i)=>({k:i+1,deltaM:mean.U+(mean.T-mean.U)/(i+1)}))};
 }
 return result;
}
function test(){
 const vectors=[[1,0],[0,1],[-1,0],[0,-1]],x={n:4,T:1,M:0};
 let sum=0,count=0;for(let i=0;i<4;i++)for(let j=i+1;j<4;j++){sum+=vectors[i].reduce((s,v,k)=>s+(v+vectors[j][k])**2/4,0);count++;}
 if(Math.abs(sum/count-subsetCentroid(x,2))>1e-12||Math.abs(subsetCentroid(x,4)-x.M)>1e-12||Math.abs(subsetCentroid(x,1)-x.T)>1e-12)throw Error("Known truth mismatch");
}
export {coherence,subsetCentroid,calculate};
test();console.log(JSON.stringify(calculate(frozen),null,2));
