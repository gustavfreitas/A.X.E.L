from __future__ import annotations

import pytest

from app.utils.preflight import check_ollama


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "integration: requer Ollama rodando localmente"
    )


@pytest.fixture(autouse=True)
def _skip_if_ollama_unavailable(request: pytest.FixtureRequest) -> None:
    if "integration" not in {m.name for m in request.node.iter_markers()}:
        return
    result = check_ollama()
    if not result.ok:
        pytest.skip(f"Ollama indisponível: {result.message}")
