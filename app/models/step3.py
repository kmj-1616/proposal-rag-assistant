"""Pydantic 요청/응답 모델 - step3 drafts/generate 엔드포인트."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.step2 import RfpRequirements


# ── POST /api/v1/drafts/generate ─────────────────────────────────────────────

class DraftGenerateRequest(BaseModel):
    rfp_text: str | None = Field(
        default=None,
        description=(
            "RFP 전문 텍스트. rfp_file_path 또는 rfp_requirements 중 하나와 같이 사용. "
            "rfp_requirements가 없으면 내부에서 자동 파싱."
        ),
        examples=["프로젝트명: AI 기반 제안서 자동화\n발주기관: 한국정보화진흥원"],
    )
    rfp_file_path: str | None = Field(
        default=None,
        description="로컬 RFP .txt 파일 경로. rfp_text와 중복 불가.",
        examples=["/local_data/rfp/sample_rfp.txt"],
    )
    rfp_requirements: RfpRequirements | None = Field(
        default=None,
        description=(
            "이미 파싱된 RFP 요구사항 객체. "
            "제공 시 rfp_text/rfp_file_path 파싱 단계를 건너뜀. "
            "POST /api/v1/rfp/analyze 응답의 rfp_requirements 값을 그대로 사용 가능."
        ),
    )
    context_top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="섹션별 검색 컨텍스트로 주입할 최대 청크 수.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "rfp_text": (
                        "프로젝트명: AI 기반 업무 자동화 시스템\n"
                        "발주기관: 한국정보화진흥원\n"
                        "예산: 5억원\n"
                        "사업 목적: 반복 업무 자동화로 행정 효율화\n"
                        "평가기준: 기술력 40점, 사업이해도 30점, 수행조직 30점\n"
                        "핵심 요구사항: RPA 도입, 문서 처리 자동화, 대시보드 구축"
                    ),
                    "context_top_k": 3,
                }
            ]
        }
    }


class DraftSection(BaseModel):
    title: str = Field(description="섹션 제목")
    priority: int = Field(description="생성 우선순위 (1이 가장 높음)")
    content: str = Field(description="생성된 섹션 초안 텍스트")
    context_chunks_used: int = Field(
        description="해당 섹션 생성에 사용된 검색 컨텍스트 청크 수"
    )


class GenerationMeta(BaseModel):
    generated_at: str = Field(description="생성 일시 (ISO 8601)")
    adapter: str = Field(description="사용된 생성 어댑터 식별자")
    context_top_k: int = Field(description="요청된 섹션별 컨텍스트 청크 수")
    toc_source: str = Field(
        description="목차 출처: 'rfp_guidelines' 또는 'default'"
    )


class DraftGenerateResponse(BaseModel):
    project_name: str | None = Field(
        default=None,
        description="RFP에서 추출된 프로젝트명",
    )
    sections: list[DraftSection] = Field(description="섹션별 생성 초안 목록")
    total_sections: int = Field(description="생성된 섹션 수")
    generation_meta: GenerationMeta = Field(description="생성 메타정보")
