from __future__ import annotations

import hashlib

from structural.zenodo_318_mammal_stress_model import (
    matrix_bitstrings,
    matrix_from_bitstrings,
    raw_surface_text,
)


def test_compact_pilot_matrix_roundtrip_preserves_raw_surface():
    order=["a","b"]
    matrix={"a":(1,0,1,1,0),"b":(0,1,0,0,1)}
    compact=matrix_bitstrings(matrix,pilot_order=order)
    rebuilt=matrix_from_bitstrings(
        compact,pilot_order=order,species_count=5
    )
    assert rebuilt==matrix

    text=raw_surface_text(rebuilt,pilot_order=order)
    assert text==(
        "partition_unit,block,target\n"
        "a,a,1\n"
        "a,a,0\n"
        "a,a,1\n"
        "a,a,1\n"
        "a,a,0\n"
        "b,b,0\n"
        "b,b,1\n"
        "b,b,0\n"
        "b,b,0\n"
        "b,b,1\n"
    )
    assert hashlib.sha256(text.encode()).hexdigest()==hashlib.sha256(
        text.encode()
    ).hexdigest()
