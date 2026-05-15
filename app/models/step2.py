"""Pydantic 요청/응답 모델 - step2 엔드포인트."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── /rfp/analyze ─────────────────────────────────────────────────────────────

class RfpAnalyzeRequest(BaseModel):
    rfp_text: str | None = Field(
        default=None,
        description="RFP 전문 텍스트. rfp_file_path와 둘 중 하나는 필수.",
        examples=["프로젝트명: AI 기반 제안서 자동화 시스템\n발주기관: 한국정보화진흥원"],
    )
    rfp_file_path: str | None = Field(
        default=None,
        description="로컬 RFP .txt 파일 경로. rfp_text와 둘 중 하나는 필수.",
        examples=["/local_data/rfp/sample_rfp.txt"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rfp_text": (
                        "프로젝트명: AI 기반 제안서 자동화 시스템\n"
                        "발주기관: 한국정보화진흥원\n"
                        "예산: 3억원\n"
                        "사업 목적: RFP 자동 분석 및 제안서 초안 생성"
                    )
                }
            ]
        }
    }


class RfpRequirements(BaseModel):
    project_name: str | None = None
    organization: str | None = None
    budget_range: str | None = None
    purpose_background: str | None = None
    evaluation_criteria: list[str] = Field(default_factory=list)
    core_requirements: list[str] = Field(default_factory=list)
    authoring_guidelines: list[str] = Field(default_factory=list)
    schedule_constraints: list[str] = Field(default_factory=list)
    must_have_constraints: list[str] = Field(default_factory=list)


class RfpAnalyzeResponse(BaseModel):
    rfp_requirements: RfpRequirements
    missing_fields: list[str] = Field(
        default_factory=list,
        description="추출되지 않은 필수 필드 목록",
    )


# ── /proposals/search ────────────────────────────────────────────────────────

class ProposalSearchRequest(BaseModel):
    query: str = Field(
        description="유사 제안서 검색 질의",
        examples=["AI 기반 데이터 분석 플랫폼"],
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="반환할 최대 결과 수",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [{"query": "AI 기반 데이터 분석 플랫폼", "top_k": 5}]
        }
    }


class ProposalSearchResult(BaseModel):
    document_name: str
    chunk_id: str
    preview: str
    score: float = Field(description="0.0~1.0 코사인 유사도 기반 점수")


class ProposalSearchResponse(BaseModel):
    query: str
    results: list[ProposalSearchResult]
    note: str = Field(
        default="임베딩 기반 검색 (paraphrase-multilingual-MiniLM-L12-v2).",
        description="검색 방식 안내",
    )


# ── /proposals/index/rebuild ─────────────────────────────────────────────────

class IndexRebuildRequest(BaseModel):
    chunks_root: str | None = Field(
        default=None,
        description="Step1 청크 루트 디렉터리 경로. 미지정 시 local_data/step1/chunks 사용.",
        examples=["local_data/step1/chunks"],
    )
    reset: bool = Field(
        default=True,
        description="기존 컬렉션 삭제 후 재생성 여부.",
    )

    model_config = {
        "json_schema_extra": {"examples": [{"reset": True}]}
    }


class IndexRebuildResponse(BaseModel):
    indexed_count: int = Field(description="인덱싱된 청크 수")
    index_path: str = Field(description="Chroma 인덱스 저장 경로")
    model: str = Field(description="사용된 임베딩 모델명")


# ── 공통 에러 ────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Any | None = None
