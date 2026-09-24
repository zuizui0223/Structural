from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/gift_global_archipelago/run_burned_pilot_v0_1.py"

spec = importlib.util.spec_from_file_location("gift_burned_pilot_v0_1", SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_missing_questionable_flags_are_not_positive_flags():
    assert module.flag_is_explicitly_true(None) is False
    assert module.flag_is_explicitly_true("") is False
    assert module.flag_is_explicitly_true("NA") is False


def test_zero_questionable_flags_are_not_positive_flags():
    assert module.flag_is_explicitly_true(0) is False
    assert module.flag_is_explicitly_true("0") is False
    assert module.flag_is_explicitly_true(0.0) is False


def test_explicit_one_questionable_flags_are_positive():
    assert module.flag_is_explicitly_true(1) is True
    assert module.flag_is_explicitly_true("1") is True
    assert module.flag_is_explicitly_true(1.0) is True
