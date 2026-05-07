# step1_data_prep

## Purpose

Prepare reusable learning text units from local proposal files.

## Scripts

- `scripts/copy_selected_to_raw.py`
- `scripts/extract_texts.py`
- `scripts/chunk_texts.py`

## Local Data Contract (not committed)

- `local_data/proposal_collection/` : local source proposal documents
- `local_data/step1/proposal_candidates.csv` : local selection metadata
- `local_data/step1/raw_proposals/` : selected proposal documents
- `local_data/step1/extracted_texts/` : extracted plain text
- `local_data/step1/chunks/` : chunk outputs for retrieval
