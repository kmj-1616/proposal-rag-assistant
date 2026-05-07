# Data Security Policy (Public Repository)

## Scope

This repository is public. Real proposal documents and real RFP files must never be committed.

## Never Commit

- Raw source documents:
  - Any files under `제안서 모음`, `RFP`, `원본_제안서`
- Derived artifacts from source documents:
  - Any files under `추출_결과`, `청크_출력`
  - Any extraction/chunking summary JSON files
- Office and PDF payloads (`.pptx`, `.pdf`, `.docx`, etc.)

## Allowed in Public Repo

- Source code
- Architecture/design docs
- Implementation notes per step
- Templates/schemas that do not contain real customer data

## Safe Workflow Before Each Commit

1. Run `git status` and inspect staged files.
2. Ensure no paths include:
   - `제안서`, `RFP`, `원본_제안서`, `추출_결과`, `청크_출력`
3. Ensure no office/PDF binaries are staged.
4. Commit only code and sanitized documentation.

## Incident Response

If sensitive data is committed by mistake:

1. Stop pushing immediately.
2. Rotate/replace exposed files in local environment.
3. Rewrite repository history (e.g. `git filter-repo` or BFG).
4. Force-push cleaned history only after verification.
