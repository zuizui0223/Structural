#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json
from pathlib import Path

PATH=Path("research/murundu_relative_topology/pre_response_protocol_v0_1.json")
EXPECTED="83b6a2539acc7983bb75648eb6c53a913917d5ea50dffdaefceceb3ac8fb6512"

x=json.loads(PATH.read_text(encoding="utf-8"))
assert x["schema"]=="structural.murundu_relative_topology_protocol.v0_1"
assert x["status"]=="FROZEN_BEFORE_DRYAD_RESPONSE_ACCESS"
assert x["selection_provenance"]["response_values_accessed"] is False
assert x["response_firewall"]["workbook_opened"] is False
assert x["response_firewall"]["response_columns_opened"] is False
assert x["response_firewall"]["primary_response_column"]=="Richness.Trees"
assert x["spatial_unit"]["replication_unit"]=="1-ha plot"
assert x["spatial_unit"]["plot_count_declared"]==11
assert x["geometry_gate"]["uses_response"] is False
assert "Height_Mur is not required" in x["geometry_gate"]["row_eligibility"]["source_nodes"]
assert x["geometry_gate"]["study_pass"]["minimum_geometry_qualified_plots"]==8
assert x["H1_primary"]["prediction"]=="positive"
assert x["H1_primary"]["bootstrap"]["replicates"]==10000
assert x["H1_primary"]["bootstrap"]["seed"]==20260925
assert x["secondary_nonrescuing"]["herb_or_termite_reanalysis"]["authorized"] is False
assert "independent replication of the frozen Structural C-R3 claim" in x["claim_boundary"]["not_allowed"]

unsigned=dict(x)
observed=unsigned.pop("protocol_fingerprint_unsigned")
payload=json.dumps(unsigned,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
digest=hashlib.sha256(payload).hexdigest()
assert observed==EXPECTED==digest, (observed,EXPECTED,digest)
print(json.dumps({
  "schema":"structural.murundu_relative_topology_pre_response_validation.v0_1",
  "status":"PRE_RESPONSE_PROTOCOL_LOCK_VALID",
  "protocol_fingerprint":digest,
  "response_values_accessed":False,
  "response_open_authorized":False,
},indent=2,sort_keys=True))
