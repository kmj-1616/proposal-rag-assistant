"""Pydantic 요청 모델 - step4 exports 엔드포인트."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ExportSection(BaseModel):
    title: str = Field(description="섹션 제목")
    content: str = Field(description="섹션 본문 텍스트")
    priority: int | None = Field(default=None, description="생성 우선순위 (선택)")


class PptExportRequest(BaseModel):
    project_name: str | None = Field(
        default=None,
        description="표지 제목으로 사용할 프로젝트명. 없으면 '제안서 초안' 사용.",
        examples=["AI 기반 업무 자동화 시스템"],
    )
    sections: list[ExportSection] = Field(
        description="섹션 목록. POST /api/v1/drafts/generate 응답의 sections 값을 그대로 사용 가능.",
        min_length=1,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_name": "AI 기반 업무 자동화 시스템",
                    "sections": [
                        {
                            "title": "사업 이해도 및 수행 전략",
                            "content": "본 사업은 반복 업무 자동화를 통해 행정 효율을 높이는 것을 목표로 합니다.",
                            "priority": 1,
                        },
                        {
                            "title": "기술 요구사항 대응방안",
                            "content": "RPA 및 AI 기반 문서 처리 자동화 솔루션을 적용합니다.",
                            "priority": 2,
                        },
                    ],
                }
            ]
        }
    }


class WordExportRequest(BaseModel):
    project_name: str | None = Field(
        default=None,
        description="문서 제목으로 사용할 프로젝트명. 없으면 '제안서 초안' 사용.",
        examples=["AI 기반 업무 자동화 시스템"],
    )
    sections: list[ExportSection] = Field(
        description="섹션 목록. POST /api/v1/drafts/generate 응답의 sections 값을 그대로 사용 가능.",
        min_length=1,
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "project_name": "AI 기반 업무 자동화 시스템",
                    "sections": [
                        {
                            "title": "사업 이해도 및 수행 전략",
                            "content": "본 사업은 반복 업무 자동화를 통해 행정 효율을 높이는 것을 목표로 합니다.",
                            "priority": 1,
                        },
                        {
                            "title": "기술 요구사항 대응방안",
                            "content": "RPA 및 AI 기반 문서 처리 자동화 솔루션을 적용합니다.",
                            "priority": 2,
                        },
                    ],
                }
            ]
        }
    }
