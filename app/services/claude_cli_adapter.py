"""LLM 어댑터 - OpenAI 호환 엔드포인트 범용 클라이언트.

환경변수 (.env):
  LLM_API_KEY   : API 키 (Ollama는 임의 문자열 가능, 예: 'ollama')
  LLM_BASE_URL  : API 베이스 URL (기본: http://localhost:11434/v1  ← Ollama)
  LLM_MODEL     : 사용할 모델명  (기본: qwen2.5:7b)

Ollama 사용 시:
  LLM_API_KEY=ollama
  LLM_BASE_URL=http://localhost:11434/v1
  LLM_MODEL=qwen2.5:7b   # ollama pull qwen2.5:7b 선행 필요

OpenAI 사용 시:
  LLM_API_KEY=sk-...
  LLM_BASE_URL=https://api.openai.com/v1
  LLM_MODEL=gpt-4o
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

ADAPTER_ID = "openai-compatible-llm"

_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")
_API_KEY = os.getenv("LLM_API_KEY", "ollama")

DEFAULT_TIMEOUT = 120


class ClaudeAdapterError(RuntimeError):
    """LLM 어댑터 기반 예외."""
    error_code: str = "LLM_ERROR"

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class ClaudeNotInstalledError(ClaudeAdapterError):
    error_code = "LLM_NOT_CONFIGURED"


class ClaudeNotLoggedInError(ClaudeAdapterError):
    error_code = "LLM_AUTH_FAILED"


class ClaudeTimeoutError(ClaudeAdapterError):
    error_code = "LLM_TIMEOUT"


class ClaudeCallError(ClaudeAdapterError):
    error_code = "LLM_CALL_FAILED"


def call_claude(prompt: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """OpenAI 호환 LLM 엔드포인트를 호출하고 생성 결과를 반환한다.

    Ollama, OpenAI 등 LLM_BASE_URL이 가리키는 엔드포인트에 요청을 보낸다.

    Args:
        prompt: 생성 프롬프트 전문.
        timeout: 최대 대기 시간(초).

    Returns:
        모델의 생성 텍스트.

    Raises:
        ClaudeNotInstalledError: LLM_API_KEY가 설정되지 않았을 때.
        ClaudeNotLoggedInError: 인증 실패(401/403) 시.
        ClaudeTimeoutError: 타임아웃 시.
        ClaudeCallError: 그 외 API 오류 시.
    """
    if not _API_KEY:
        raise ClaudeNotInstalledError(
            "LLM_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.",
            {"hint": "프로젝트 루트 .env에 LLM_API_KEY=ollama (Ollama) 또는 sk-...(OpenAI) 를 추가하세요."},
        )

    try:
        from openai import OpenAI, APITimeoutError, AuthenticationError, APIError

        client = OpenAI(
            api_key=_API_KEY,
            base_url=_BASE_URL,
            timeout=timeout,
        )

        response = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 IT 사업 제안서 전문 작성자입니다. "
                        "사용자가 요청한 섹션 본문을 격식체 한국어로 즉시 작성합니다. "
                        "인사말, 질문, 확인 요청 없이 본문만 출력합니다."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )

        content = response.choices[0].message.content or ""
        if not content.strip():
            raise ClaudeCallError(
                "모델이 빈 응답을 반환했습니다.",
                {"model": _MODEL, "base_url": _BASE_URL},
            )
        return content.strip()

    except AuthenticationError as exc:
        raise ClaudeNotLoggedInError(
            f"LLM API 인증에 실패했습니다. LLM_API_KEY를 확인하세요: {exc}",
            {"base_url": _BASE_URL},
        )
    except APITimeoutError:
        raise ClaudeTimeoutError(
            f"LLM API가 {timeout}초 내에 응답하지 않았습니다. (모델: {_MODEL})",
            {"timeout_seconds": timeout, "model": _MODEL},
        )
    except ClaudeAdapterError:
        raise
    except Exception as exc:
        raise ClaudeCallError(
            f"LLM API 호출 중 오류가 발생했습니다: {exc}",
            {"model": _MODEL, "base_url": _BASE_URL},
        )
