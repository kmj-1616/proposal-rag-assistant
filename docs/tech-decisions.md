# Tech Decisions

## Decision Summary

- Language: Python
- Document extraction: `python-pptx`, `PyMuPDF`, `pdfplumber`
- Retrieval backend (planned): ChromaDB
- Embedding model (planned): to be finalized in step2 benchmark
- Generation model interface (planned): pluggable LLM client
- UI (planned): Streamlit first, optional Gradio alternative
- Export (planned): `python-docx` as minimum, `python-pptx` optional

## Why This Stack

- Python ecosystem already matches extraction/export needs.
- ChromaDB gives fast local iteration for retrieval prototyping.
- Streamlit minimizes UI boilerplate and accelerates demo readiness.
- Word export first reduces implementation risk while preserving delivery value.

## Trade-offs

- Local-first setup improves privacy but requires explicit environment setup.
- Excluding all office/PDF files from git reduces leakage risk but limits reproducible sample bundles.
- Step-wise module split improves clarity but requires stricter interface contracts between steps.

## Revisit Points

- Embedding model quality vs latency after step2 retrieval tests
- Section generation prompt strategy after step3 quality review
- UI framework swap only if Streamlit fails required interactions
