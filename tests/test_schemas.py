"""Tests for schema discovery and loading."""

import pytest
from ating_engine.schemas.loader import (
    build_schema_registry,
    get_schema_path,
    list_schemas,
    load_schema,
)


def test_list_schemas_contains_all_core_contracts():
    schemas = list_schemas("v1")
    expected = {"agent", "event", "input", "operation", "state"}
    assert expected.issubset(set(schemas))


def test_load_all_schemas_valid_structure():
    schemas = list_schemas("v1")
    for s_name in schemas:
        schema_data = load_schema(s_name, "v1")
        assert "$schema" in schema_data
        assert "$id" in schema_data
        assert "title" in schema_data
        assert "version" in schema_data
        assert schema_data["type"] == "object"


def test_load_nonexistent_schema_raises_error():
    with pytest.raises(FileNotFoundError):
        load_schema("nonexistent_schema_xyz", "v1")


def test_build_schema_registry_loads_resources():
    registry = build_schema_registry("v1")
    assert registry is not None
