// Post-hoc aggregate-only descriptive sensitivity. Brazil E/F habitat mapping unverified.
// Q=U/T is invariant to common scalar multiplication but NOT mean cosine similarity.
// Parallel vectors of unequal lengths can have Q<1; no pure directional mechanism claim.
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
function relativeCoherence(x){if(!Number.isInteger(x.n)||x.n<2||!Number.isFinite(x.T)||!Number.isFinite(x.M)||x.T<=0||x.M<0||x.M>x.T+1e-10)throw Error("Invalid aggregate or undefined relative coherence");const q=(x.n*x.M-x.T)/((x.n-1)*x.T);if(q< -1/(x.n-1)-1e-10||q>1+1e-10)throw Error("Algebraic bound violated");return q;}
function summarize(data){const out={};for(const [region,d] of Object.entries(data)){const rows=d.years.map(y=>{const modified=relativeCoherence(y.modified),reference=relativeCoherence(y.reference);return {year:y.year,modified,reference,deltaQ:modified-reference};});out[region]={rows,meanQmodified:rows.reduce((s,x)=>s+x.modified,0)/rows.length,meanQreference:rows.reduce((s,x)=>s+x.reference,0)/rows.length,meanDeltaQ:rows.reduce((s,x)=>s+x.deltaQ,0)/rows.length,negative:rows.filter(x=>x.deltaQ<0).length};}return out;}
function test(){const close=(x,y)=>Math.abs(x-y)<1e-12;if(!close(relativeCoherence({n:2,T:1,M:1}),1)||!close(relativeCoherence({n:2,T:1,M:0}),-1))throw Error("known truth");const x={n:2,T:5,M:4},scaled={n:2,T:45,M:36};if(!close(relativeCoherence(x),relativeCoherence(scaled)))throw Error("scale invariance");if(!close(relativeCoherence(x),0.6))throw Error("parallel unequal lengths fixture");let stop=false;try{relativeCoherence({n:2,T:0,M:0})}catch{stop=true}if(!stop)throw Error("zero motion accepted");}
export {relativeCoherence,summarize,test};
test();console.log(JSON.stringify(summarize(frozen),null,2));
