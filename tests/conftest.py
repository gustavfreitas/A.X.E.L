from __future__ import annotations

import json

import pytest

from app.core.llm import LLMProvider
from app.utils.preflight import check_ollama


class FakeProvider(LLMProvider):
    """LLM simulado: devolve respostas pré-definidas, na ordem das chamadas.

    Permite testar o pipeline inteiro (intent -> prompt -> resposta -> checagem
    de vazamento) sem Ollama, em milissegundos e de forma determinística.
    """

    def __init__(self, *replies: str) -> None:
        self.replies = list(replies)
        self.prompts: list[str] = []

    def complete(self, prompt: str, *, temperature: float = 0.2) -> str:
        self.prompts.append(prompt)
        if not self.replies:
            raise AssertionError("FakeProvider ficou sem respostas configuradas.")
        return self.replies.pop(0)


def intent_json(
    intent: str,
    confidence: str = "high",
    requires_clarification: bool = False,
    missing_info: list[str] | None = None,
) -> str:
    return json.dumps(
        {
            "intent": intent,
            "confidence": confidence,
            "requires_clarification": requires_clarification,
            "missing_info": missing_info or [],
        }
    )


@pytest.fixture
def fake_provider():
    return FakeProvider


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: requer Ollama rodando localmente")


@pytest.fixture(autouse=True)
def _skip_if_ollama_unavailable(request: pytest.FixtureRequest) -> None:
    if "integration" not in {m.name for m in request.node.iter_markers()}:
        return
    result = check_ollama()
    if not result.ok:
        pytest.skip(f"Ollama indisponível: {result.message}")
