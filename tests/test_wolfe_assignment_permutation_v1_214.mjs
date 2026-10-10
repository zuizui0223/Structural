import test from "node:test";
import assert from "node:assert/strict";
import {nullDistribution,pTail} from "../scripts/wolfe_assignment_permutation_v1_214.mjs";
test("hypergeometric sharp null has exact 70 assignments for each 4-vs-4 stratum",()=>{
 const d=nullDistribution([1]);
 assert.equal(d.denominator,70n);
 assert.equal(d.dist.get(-1),35n);
 assert.equal(d.dist.get(+1),35n);
 assert.equal(pTail(d,1,true),1);
 assert.equal(pTail(d,1,false),0.5);
});
test("multiple strata have exact weighted convolution with sign changes",()=>{
 const d=nullDistribution([1,1],[1,-1]);
 assert.equal(d.denominator,4900n);
 assert.equal(d.dist.get(-2),1225n);
 assert.equal(d.dist.get(0),2450n);
 assert.equal(d.dist.get(+2),1225n);
 assert.equal(pTail(d,2,true),0.5);
});
test("none or all successes yield point-null and no tails invented",()=>{
 const d=nullDistribution([0,8]);
 assert.equal(d.dist.size,1);
 assert.equal(d.dist.get(0),4900n);
 assert.equal(pTail(d,0,true),1);
});
