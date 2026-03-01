"""Tests for load_stubs."""

import json
from pathlib import Path

import pytest

from wiremock_mock import load_stubs


def test_load_stubs_from_json_file(tmp_path: Path) -> None:
    """load_stubs reads a JSON file with mappings."""
    stubs_file = tmp_path / "stubs.json"
    stubs_file.write_text(
        '{"mappings": [{"request": {"method": "GET", "urlPath": "/v1/pages"}, '
        '"response": {"status": 200, "jsonBody": {"object": "page"}}}]}',
    )
    result = load_stubs(path=stubs_file)
    assert "mappings" in result
    assert len(result["mappings"]) == 1
    assert result["mappings"][0]["request"]["urlPath"] == "/v1/pages"


def test_load_stubs_invalid_json_raises(tmp_path: Path) -> None:
    """load_stubs raises for invalid JSON."""
    stubs_file = tmp_path / "stubs.json"
    stubs_file.write_text("not json")
    with pytest.raises(json.JSONDecodeError):
        load_stubs(path=stubs_file)


def test_load_stubs_non_object_raises(tmp_path: Path) -> None:
    """load_stubs raises when JSON is not an object."""
    stubs_file = tmp_path / "stubs.json"
    stubs_file.write_text("[1, 2, 3]")
    with pytest.raises(ValueError):
        load_stubs(path=stubs_file)
