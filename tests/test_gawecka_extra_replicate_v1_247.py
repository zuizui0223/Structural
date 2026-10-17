"""Replay synthetic 60+extra2 schema and never make replicate-6 data vanish."""
import csv,io,sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from gawecka_extra_replicate_v1_247 import groups_of_raw,EXTRA,EXPECTED_ALL_ROWS,evaluate
from gawecka_star_first_detection_v1_246 import COMMUNITIES,SOURCE_LAYOUT

def example():
    headers=["initials","date","time","community","landscape","replica"]+[
        f"patch{p}_{s}" for p in range(1,6) for s in ("BRBR","LIER")]
    lines=[",".join(headers)]
    for community in COMMUNITIES:
        for layout in ("5","1C","1P","4C","4P"):
            reps=range(1,7) if (community=="BRBR_LIER_DIRA" and layout in ("1C","1P")) else range(1,6)
            for rep in reps:
                if layout=="5":sources={1,2,3,4,5}
                else:sources=set(SOURCE_LAYOUT[layout])
                for k,day in enumerate((7,10,13,16,19,22,25,28,29)):
                    values=["A",f"{day:02d}/02/2024","14:30:00",community,layout,str(rep)]
                    for p in range(1,6):
                        count=10 if p in sources else 0
                        if layout=="1P" and rep==6 and k==1 and p==3:count=1
                        if layout=="1P" and rep==6 and k==2 and p==1:count=2
                        values.extend([str(count),"" if community=="BRBR" else "1"])
                    lines.append(",".join(values))
    return ("\n".join(lines)+"\n").encode()

def test_original_source_62_reconcile():
    raw=example()
    h,rows,groups,control=groups_of_raw(raw)
    assert len(rows)==693
    assert len(groups)==62
    assert control==135
    assert EXTRA<=set(groups)

def test_both_denominators_persist_and_extra_observed():
    result=evaluate(example())
    assert result["paper_described_60_landscapes"]["n_independent_focal_1P_landscapes"]==15
    assert result["all_62_original_source_landscape_sensitivity"]["one_source_peripheral_landscapes"]==16
    assert result["all_62_original_source_landscape_sensitivity"]["1P_first_centre_vs_distal_category_counts"]["far_detected_BEFORE_centre_first_positive"]==1
    assert result["paper_described_60_landscapes"]["total_initially_empty_patches"]==150

def test_source_design_cannot_silently_promote_other_rep7():
    raw=example().decode()
    raw=raw.replace("BRBR_LIER_DIRA,1P,6","BRBR_LIER_DIRA,1P,7")
    with pytest.raises(ValueError,match="replicate-six"):
        groups_of_raw(raw.encode())
