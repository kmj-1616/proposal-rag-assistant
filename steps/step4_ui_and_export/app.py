"""Streamlit UI - RFP 입력 → 분석 → 초안 생성 → Word 다운로드 흐름."""
from __future__ import annotations

import json
from io import BytesIO

import requests
import streamlit as st

API_BASE = "http://localhost:8000/api/v1"
REQUEST_TIMEOUT = 600  # 초안 생성은 LLM 호출로 시간이 걸릴 수 있음


# ── 페이지 설정 ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="제안서 자동 생성 시스템",
    page_icon="📄",
    layout="wide",
)

st.title("📄 제안서 자동 생성 시스템")
st.caption("RFP 입력 → 요구사항 분석 → 섹션별 초안 생성 → Word 다운로드")

# ── 헬스체크 ──────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def check_health() -> dict:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.json()
    except Exception:
        return {"status": "error", "index_ready": False}


with st.sidebar:
    st.subheader("서버 상태")
    health = check_health()
    if health.get("status") == "ok":
        st.success("API 서버 연결됨")
        if health.get("index_ready"):
            st.info("검색 인덱스 준비됨")
        else:
            st.warning("검색 인덱스 없음 — 컨텍스트 없이 생성됩니다")
    else:
        st.error("API 서버에 연결할 수 없습니다\n`uvicorn app.main:app --port 8000`을 실행하세요")

    st.divider()
    st.subheader("생성 설정")
    context_top_k = st.slider(
        "섹션별 참고 청크 수",
        min_value=1,
        max_value=10,
        value=3,
        help="유사 제안서 청크를 몇 개까지 프롬프트에 주입할지 설정합니다. 인덱스가 없으면 0으로 동작합니다.",
    )
    st.caption("LLM 모델은 서버 `.env`의 `LLM_MODEL` 설정을 따릅니다.")

# ── 세션 상태 초기화 ──────────────────────────────────────────────────────────

for key in ("rfp_requirements", "draft_result"):
    if key not in st.session_state:
        st.session_state[key] = None

# ── 1단계: RFP 입력 ───────────────────────────────────────────────────────────

st.header("1단계: RFP 입력")

rfp_text = st.text_area(
    "RFP 전문 텍스트를 붙여넣으세요",
    height=200,
    placeholder=(
        "프로젝트명: AI 기반 업무 자동화 시스템\n"
        "발주기관: 한국정보화진흥원\n"
        "예산: 5억원\n"
        "사업 목적: 반복 업무 자동화로 행정 효율화\n"
        "평가기준: 기술력 40점, 사업이해도 30점, 수행조직 30점\n"
        "핵심 요구사항: RPA 도입, 문서 처리 자동화, 대시보드 구축"
    ),
)

if st.button("RFP 분석", type="primary", disabled=not rfp_text.strip()):
    with st.spinner("RFP를 분석하는 중..."):
        try:
            resp = requests.post(
                f"{API_BASE}/rfp/analyze",
                json={"rfp_text": rfp_text},
                timeout=30,
            )
            if resp.status_code == 200:
                st.session_state.rfp_requirements = resp.json().get("rfp_requirements")
                st.session_state.draft_result = None
                st.success("RFP 분석 완료")
            else:
                st.error(f"분석 실패: {resp.status_code} — {resp.text}")
        except requests.exceptions.ConnectionError:
            st.error("API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        except requests.exceptions.Timeout:
            st.error("요청 시간이 초과됐습니다.")

# ── 2단계: 분석 결과 확인 ─────────────────────────────────────────────────────

if st.session_state.rfp_requirements:
    st.header("2단계: 분석 결과 확인")

    reqs = st.session_state.rfp_requirements

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**프로젝트명**: {reqs.get('project_name') or '—'}")
        st.markdown(f"**발주기관**: {reqs.get('organization') or '—'}")
        st.markdown(f"**예산**: {reqs.get('budget_range') or '—'}")
    with col2:
        st.markdown(f"**사업 목적**: {reqs.get('purpose_background') or '—'}")

    criteria = reqs.get("evaluation_criteria") or []
    if criteria:
        st.markdown("**평가 기준**")
        for c in criteria:
            st.markdown(f"- {c}")

    core = reqs.get("core_requirements") or []
    if core:
        st.markdown("**핵심 요구사항**")
        for r in core:
            st.markdown(f"- {r}")

    with st.expander("전체 파싱 결과 (JSON)"):
        st.json(reqs)

    # ── 3단계: 초안 생성 ──────────────────────────────────────────────────────

    st.header("3단계: 제안서 초안 생성")

    if st.button("초안 생성 시작", type="primary"):
        with st.spinner(
            "LLM으로 섹션별 초안을 생성하는 중입니다. 모델 크기와 메모리 여유에 따라 수 분이 소요될 수 있습니다..."
        ):
            try:
                resp = requests.post(
                    f"{API_BASE}/drafts/generate",
                    json={
                        "rfp_requirements": reqs,
                        "context_top_k": context_top_k,
                    },
                    timeout=REQUEST_TIMEOUT,
                )
                if resp.status_code == 200:
                    st.session_state.draft_result = resp.json()
                    st.success(
                        f"초안 생성 완료 — {st.session_state.draft_result['total_sections']}개 섹션"
                    )
                elif resp.status_code == 503:
                    detail = resp.json().get("detail", {})
                    error_code = detail.get("error_code", "UNKNOWN")
                    message = detail.get("message", resp.text)
                    st.error(
                        f"LLM 서비스 오류 ({error_code})\n\n{message}\n\n"
                        "**Ollama 체크리스트**\n"
                        "1. `ollama serve` 실행 여부 확인\n"
                        "2. `ollama pull qwen2.5:0.5b` 모델 다운로드 여부 확인\n"
                        "3. 가용 RAM이 모델 요구량 이상인지 확인"
                    )
                else:
                    st.error(f"생성 실패: {resp.status_code} — {resp.text}")
            except requests.exceptions.ConnectionError:
                st.error("API 서버에 연결할 수 없습니다.")
            except requests.exceptions.Timeout:
                st.error(
                    "생성 요청 시간이 초과됐습니다.\n\n"
                    "경량 모델(예: `qwen2.5:0.5b`)을 사용하거나 다른 앱을 종료해 RAM을 확보하세요."
                )

# ── 4단계: 결과 확인 및 다운로드 ─────────────────────────────────────────────

if st.session_state.draft_result:
    result = st.session_state.draft_result
    st.header("4단계: 생성 결과 확인 및 다운로드")

    meta = result.get("generation_meta", {})
    st.caption(
        f"생성 일시: {meta.get('generated_at', '—')} | "
        f"어댑터: {meta.get('adapter', '—')} | "
        f"목차 출처: {meta.get('toc_source', '—')}"
    )

    for section in result.get("sections", []):
        with st.expander(
            f"[{section['priority']}] {section['title']} "
            f"(참고 청크: {section['context_chunks_used']}개)",
            expanded=section["priority"] == 1,
        ):
            st.markdown(section["content"])

    st.divider()
    st.subheader("Word 파일 다운로드")

    if st.button("Word(.docx) 생성"):
        with st.spinner("Word 파일을 만드는 중..."):
            try:
                resp = requests.post(
                    f"{API_BASE}/exports/word",
                    json={
                        "project_name": result.get("project_name"),
                        "sections": result.get("sections", []),
                    },
                    timeout=30,
                )
                if resp.status_code == 200:
                    project = result.get("project_name") or "proposal_draft"
                    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in project)
                    filename = f"{safe.strip().replace(' ', '_')[:50]}.docx"
                    st.download_button(
                        label="📥 Word 파일 다운로드",
                        data=BytesIO(resp.content),
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                else:
                    st.error(f"파일 생성 실패: {resp.status_code} — {resp.text}")
            except requests.exceptions.ConnectionError:
                st.error("API 서버에 연결할 수 없습니다.")
            except requests.exceptions.Timeout:
                st.error("파일 생성 요청 시간이 초과됐습니다.")
