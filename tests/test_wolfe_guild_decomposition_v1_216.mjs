import test from "node:test";
import assert from "node:assert/strict";
import {cellProbs,summarize} from "../scripts/wolfe_joint_guild_decomposition_v1_216.mjs";

test("joint = product of marginals + within-cell association exactly",()=>{
 const x=cellProbs([[1,1],[1,0],[0,1],[0,0]]);
 assert.equal(x.J,0.25);
 assert.equal(x.independence_product,0.25);
 assert.equal(x.association,0);
 const y=cellProbs([[1,1],[1,1],[0,0],[0,0]]);
 assert.equal(y.J,0.5);
 assert.equal(y.independence_product,0.25);
 assert.equal(y.association,0.25);
});
test("bounded source response flags and summary",()=>{
 assert.throws(()=>cellProbs([[1,2]]),/Binary guild flags/);
 const strata=[{n:4,heterogeneous:[[1,1],[1,1],[0,0],[0,0]],
  homogeneous:[[1,0],[0,1],[1,0],[0,1]]},
  {n:6,heterogeneous:[[1,1],[1,1],[1,1],[1,1]],
   homogeneous:[[0,0],[0,0],[0,0],[0,0]]}];
 const z=summarize(strata);
 assert.equal(z.patches4.joint,0.5);
 assert.equal(z.patches6.joint,1);
 assert.equal(z.overall.joint,0.75);
});
