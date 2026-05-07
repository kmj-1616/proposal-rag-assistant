"""step2 스키마 검증 유틸리티."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _type_ok(value: Any, expected: str | list[str]) -> bool:
    expected_types = expected if isinstance(expected, list) else [expected]
    for t in expected_types:
        if t == "null" and value is None:
            return True
        if t == "string" and isinstance(value, str):
            return True
        if t == "array" and isinstance(value, list):
            return True
        if t == "object" and isinstance(value, dict):
            return True
    return False


def validate_payload(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    properties: dict[str, Any] = schema.get("properties", {})
    required: list[str] = schema.get("required", [])
    allow_extra = schema.get("additionalProperties", True)

    for field in required:
        if field not in payload:
            errors.append(f"missing required field: {field}")

    if not allow_extra:
        extra_keys = sorted(set(payload.keys()) - set(properties.keys()))
        for key in extra_keys:
            errors.append(f"unexpected field: {key}")

    for key, value in payload.items():
        spec = properties.get(key)
        if not spec:
            continue
        if not _type_ok(value, spec.get("type", "object")):
            errors.append(f"type mismatch: {key}")
            continue
        if isinstance(value, list):
            item_type = spec.get("items", {}).get("type")
            if item_type:
                for idx, item in enumerate(value):
                    if not _type_ok(item, item_type):
                        errors.append(f"item type mismatch: {key}[{idx}]")
    return errors

