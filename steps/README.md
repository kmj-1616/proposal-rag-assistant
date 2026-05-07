# Step-Based Workflow

- `step1_data_prep`: local raw proposal ingestion, text extraction, chunking
- `step2_retrieval_and_rfp_parse`: retrieval index + RFP structured parsing
- `step3_generation_pipeline`: section-level proposal draft generation
- `step4_ui_and_export`: user interface and document export
- `step5_integration_and_demo`: final integration, evaluation, demo prep

All runtime data is local-only and must be stored under `local_data/` (ignored by git).
