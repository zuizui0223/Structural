"""No original biological data accessed by known-truth tests."""
import sys
from datetime import datetime,timedelta
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from gawecka_star_first_detection_v1_246 import (
    distance,first_detected,center_and_far_category,nonnegative_int_or_missing,
    SOURCE_LAYOUT,COMMUNITIES,analyze)

def events(vals):
    t=datetime(2024,2,7)
    return [(t+timedelta(days=i*3),{1:z,2:10,3:0,4:0,5:0})
            for i,z in enumerate(vals)]

def test_star_distances_not_euclidean_guess():
    assert distance(2,3)==2
    assert distance(2,1)==1
    assert distance(1,5)==1
    assert distance(4,5)==2
    assert SOURCE_LAYOUT["1P"]==(2,)

def test_middle_detection_window_and_censoring():
    r=first_detected(events([0,0,5,7]),1)
    assert r["last_recorded_zero_day"]==3
    assert r["first_positive_day"]==6
    assert not r["right_censored"]
    right=first_detected(events([0,0,0,0]),1)
    assert right["right_censored"] and right["first_positive_day"] is None

def test_far_preceding_first_recorded_center_detection():
    c={"first_positive_day":9}
    far=[{"first_positive_day":6},{"first_positive_day":None},{"first_positive_day":12}]
    assert center_and_far_category(c,far)=="far_detected_BEFORE_centre_first_positive"
    assert center_and_far_category({"first_positive_day":None},far)=="far_detected_centre_never_detected"
    assert center_and_far_category({"first_positive_day":6},far)=="first_centre_and_far_same_visit"

def test_observation_missing_not_zero():
    assert nonnegative_int_or_missing("") is None
    assert nonnegative_int_or_missing("NA") is None
    assert nonnegative_int_or_missing("0")==0
    assert nonnegative_int_or_missing("10")==10
    with pytest.raises(ValueError):nonnegative_int_or_missing("-2")
    with pytest.raises(ValueError):nonnegative_int_or_missing("4.2")

def test_synthetic_60_landscapes_all_layouts_and_levels():
    headers=["initials","date","time","community","landscape","replica"]+[
        f"patch{p}_{s}" for p in range(1,6) for s in ("BRBR","LIER")]
    rows=[",".join(headers)]
    for community in COMMUNITIES:
        for layout,source in SOURCE_LAYOUT.items():
            for replica in range(1,6):
                for k,day in enumerate((7,10,13)):
                    count={p:(10 if p in source else 0) for p in range(1,6)}
                    if layout=="1P" and k==1:
                        count[3]=2 # Two links away, center is still 0.
                    if layout=="1P" and k==2:count[1]=1
                    vals=["A",f"{day:02d}/02/2024","14:30:00",
                          community,layout,str(replica)]
                    for patch in range(1,6):
                        vals.extend([str(count[patch]),"" if community=="BRBR" else "1"])
                    rows.append(",".join(vals))
    result=analyze(("\n".join(rows)+"\n").encode())
    assert result["total_independent_spatial_treatment_landscapes"]==60
    assert result["one_peripheral_source_independent_landscapes"]==15
    assert result["original_empty_patch_series_total"]==150
    assert result["focal_classification_counts"]=={
         "far_detected_BEFORE_centre_first_positive":15}
