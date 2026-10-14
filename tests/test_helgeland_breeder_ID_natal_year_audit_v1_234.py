"""Synthetic consistency audit only, no empirical breeding values."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from helgeland_breeder_ID_natal_year_audit_v1_234 import SHA
def test_frozen_source_blobs():
    assert SHA["presence"]=="c998367c55d0d88ec17e6d1dc2931a97c46aff55"
    assert SHA["producer"]=="e6cc1558b740b03b9ca33c3af180e05079bcbba8"
    assert len(SHA)==3
