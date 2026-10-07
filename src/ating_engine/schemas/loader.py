"""JSON Schema discovery and loading utilities."""

import json
from pathlib import Path
from typing import Dict, List, Optional
from referencing import Registry, Resource

_SCHEMAS_DIR = Path(__file__).resolve().parent


def get_schema_path(schema_name: str, version: str = "v1") -> Path:
    """Get filesystem path for a specific schema file."""
    filename = schema_name if schema_name.endswith(".schema.json") else f"{schema_name}.schema.json"
    path = _SCHEMAS_DIR / version / filename
    if not path.is_file():
        raise FileNotFoundError(f"Schema not found at path: {path}")
    return path


def load_schema(schema_name: str, version: str = "v1") -> Dict:
    """Load and parse JSON Schema definition."""
    path = get_schema_path(schema_name, version)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def list_schemas(version: str = "v1") -> List[str]:
    """List available schema names in the designated version directory."""
    version_dir = _SCHEMAS_DIR / version
    if not version_dir.is_dir():
        return []
    return [
        p.stem.replace(".schema", "")
        for p in sorted(version_dir.glob("*.schema.json"))
    ]


def build_schema_registry(version: str = "v1") -> Registry:
    """Build a referencing.Registry preloaded with all schemas in the version dir.

    Enables local $ref resolution between sibling schemas (e.g. state -> agent).
    """
    version_dir = _SCHEMAS_DIR / version
    resources = []
    for schema_file in version_dir.glob("*.schema.json"):
        with schema_file.open("r", encoding="utf-8") as f:
            data = json.load(f)
            # Register by filename, $id, and relative name
            resource = Resource.from_contents(data)
            resources.append((schema_file.name, resource))
            if "$id" in data:
                resources.append((data["$id"], resource))

    registry = Registry()
    for uri, res in resources:
        registry = registry.with_resource(uri, res)
    return registry
