import test from "node:test";
import assert from "node:assert/strict";
import {pairP} from "../scripts/wolfe_day_pairs_v1_215.mjs";
test("paired exact two-sided null",()=>{
 assert.equal(pairP(0,0),1);
 assert.equal(pairP(1,1),1);
 assert.equal(pairP(2,2),0.5);
 assert.equal(pairP(4,4),0.125);
});
test("impossible pair statistics rejected",()=>{
 assert.throws(()=>pairP(2,3),/Invalid pair statistic/);
});
