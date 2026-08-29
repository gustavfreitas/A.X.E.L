"""
Teste de integração — requer Ollama rodando localmente com o modelo baixado.
Não é mockado de propósito: o objetivo aqui é medir accuracy real do
classificador de intenção contra o dataset de avaliação (Fase 05 do plano).

Rodar com: pytest tests/test_intent.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.llm import get_provider
from app.services import intent as intent_service

TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"


def load_cases() -> list[dict]:
    return json.loads(TEST_CASES_PATH.read_text(encoding="utf-8"))


@pytest.mark.integration
@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["input"][:40])
def test_intent_classification(case: dict) -> None:
    provider = get_provider()
    result = intent_service.classify(case["input"], provider)

    assert result.intent == case["expected_intent"], (
        f"esperado={case['expected_intent']} obtido={result.intent} "
        f"input={case['input']!r}"
    )

    if "expected_requires_clarification" in case:
        assert result.requires_clarification == case["expected_requires_clarification"]
