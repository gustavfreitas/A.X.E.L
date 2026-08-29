"""
Verificação de pré-requisitos antes de usar o AXEL.

Existe porque, na prática (Fase 04), o erro mais comum não é bug no AXEL —
é o Ollama simplesmente não estar rodando. Em vez de deixar isso estourar
como ConnectionError cru em qualquer lugar do código, centralizamos o
diagnóstico aqui e retornamos uma mensagem acionável.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from app.config import settings


@dataclass
class PreflightResult:
    ok: bool
    message: str


def check_ollama() -> PreflightResult:
    base = settings.ollama_host.rstrip("/")

    try:
        response = requests.get(f"{base}/api/tags", timeout=5)
        response.raise_for_status()
    except requests.ConnectionError:
        return PreflightResult(
            ok=False,
            message=(
                f"Não consegui conectar em {base}. O servidor do Ollama não "
                "parece estar rodando. Rode `ollama serve` num terminal e "
                "tente de novo."
            ),
        )
    except requests.RequestException as exc:
        return PreflightResult(
            ok=False,
            message=f"Ollama respondeu com erro inesperado em {base}: {exc}",
        )

    models = [m.get("name", "") for m in response.json().get("models", [])]
    model_base = settings.ollama_model.split(":")[0]
    if not any(model_base in name for name in models):
        return PreflightResult(
            ok=False,
            message=(
                f"O Ollama está rodando, mas o modelo '{settings.ollama_model}' "
                f"não foi encontrado (modelos instalados: {models or 'nenhum'}). "
                f"Rode `ollama pull {settings.ollama_model}`."
            ),
        )

    return PreflightResult(ok=True, message="Ollama e modelo disponíveis.")
