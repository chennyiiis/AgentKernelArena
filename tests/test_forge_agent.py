import json

import pytest

from agents.forge.launch_agent import (
    _forge_max_hours,
    _source_hashes,
    _validate_forge_outcome,
)


def _result(path, **overrides):
    value = {
        "success": True,
        "status": "improved",
        "termination_reason": "budget_exhausted",
    }
    value.update(overrides)
    path.write_text(json.dumps(value))


def test_forge_max_hours_reserves_finalization_window():
    assert _forge_max_hours({"timeout_seconds": 43200}) == 11.5
    assert _forge_max_hours({"timeout_seconds": 3600}) == 0.5


def test_validate_forge_outcome_rejects_nonzero_exit(tmp_path):
    result = tmp_path / "forge_result.json"
    _result(result, success=False, status="agent_failed")
    with pytest.raises(RuntimeError, match=r"exit=1.*agent_failed"):
        _validate_forge_outcome(result_json=result, return_code=1)


def test_validate_forge_outcome_rejects_unchanged_sources(tmp_path):
    result = tmp_path / "forge_result.json"
    source = tmp_path / "kernel.py"
    source.write_text("baseline")
    _result(result, status="no_change")
    before = _source_hashes([source])
    with pytest.raises(RuntimeError, match="no effective source changes"):
        _validate_forge_outcome(
            result_json=result,
            return_code=0,
            before_hashes=before,
            source_files=[source],
        )


def test_validate_forge_outcome_accepts_changed_sources(tmp_path):
    result = tmp_path / "forge_result.json"
    source = tmp_path / "kernel.py"
    source.write_text("baseline")
    before = _source_hashes([source])
    source.write_text("optimized")
    _result(result)
    value = _validate_forge_outcome(
        result_json=result,
        return_code=0,
        before_hashes=before,
        source_files=[source],
    )
    assert value["status"] == "improved"
