from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKEN_SCRIPT = ROOT / "scripts/prepare_dryad_token_v0_73.py"
STAGE_A = ROOT / ".github/workflows/boreal-lake-islands-stage-a-v0_78.yml"
STAGE_B = ROOT / ".github/workflows/boreal-lake-islands-stage-b-v0_89.yml"


def load_token_script():
    spec = importlib.util.spec_from_file_location("dryad_token_v073_mask", TOKEN_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_boreal_workflows_use_src_layout_pythonpath():
    for path in (STAGE_A, STAGE_B):
        text = path.read_text(encoding="utf-8")
        assert "PYTHONPATH: ${{ github.workspace }}/src" in text
        assert "PYTHONPATH: ${{ github.workspace }}\n" not in text


def test_dryad_token_is_registered_for_actions_masking_before_export(
    tmp_path, monkeypatch, capsys
):
    module = load_token_script()
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    github_env = tmp_path / "github_env"

    receipt = module.prepare_token(
        client_id="",
        client_secret="",
        fallback_token="MASK_THIS_BEARER",
        github_env=github_env,
    )

    stdout = capsys.readouterr().out
    assert "::add-mask::MASK_THIS_BEARER" in stdout
    assert github_env.read_text(encoding="utf-8") == (
        "DRYAD_TOKEN=MASK_THIS_BEARER\n"
    )
    assert "MASK_THIS_BEARER" not in json.dumps(receipt)
    assert receipt["token_persisted_in_receipt"] is False
