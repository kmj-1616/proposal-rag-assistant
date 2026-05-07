# step1 Implementation Notes

## Scope

- Selected proposal copy
- Text extraction from local proposal files
- Chunk generation for retrieval

## Public Changes

- Added step-based scripts under `steps/step1_data_prep/scripts/`
- Replaced hardcoded legacy paths with:
  - project-relative defaults
  - environment-variable overrides

## Local Validation Checklist

- [ ] `proposal_candidates.csv` prepared in local path
- [ ] selected source files copied to raw folder
- [ ] text extraction completed without failures
- [ ] chunk files generated under local step1 directory
