"""step2 파서 + 스키마 검증 일괄 실행."""
from __future__ import annotations

import json
from pathlib import Path

from parser import parse_rfp_text
from schema_validator import load_schema, validate_payload


def main() -> int:
    base = Path(__file__).resolve().parent
    schema_path = base / "schemas" / "rfp_requirements.schema.json"
    cases_dir = base / "test_cases"
    out_dir = base / "validation_results"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not schema_path.is_file():
        raise SystemExit(f"Schema not found: {schema_path}")
    if not cases_dir.is_dir():
        raise SystemExit(f"Case directory not found: {cases_dir}")

    schema = load_schema(schema_path)
    case_files = sorted(cases_dir.glob("*.txt"))
    if not case_files:
        raise SystemExit(f"No case files found: {cases_dir}")

    has_error = False
    for case_file in case_files:
        text = case_file.read_text(encoding="utf-8", errors="replace")
        parsed = parse_rfp_text(text)
        errors = validate_payload(parsed, schema)

        report = {
            "case": case_file.name,
            "valid": len(errors) == 0,
            "errors": errors,
            "parsed": parsed,
            "missing_fields": [k for k, v in parsed.items() if v is None or (isinstance(v, list) and not v)],
        }
        report_path = out_dir / f"{case_file.stem}.report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        status = "PASS" if not errors else "FAIL"
        print(f"[{status}] {case_file.name} -> {report_path.name}")
        if errors:
            has_error = True
            for err in errors:
                print(f"  - {err}")

    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
