"""Provider do Ollama com a camada HTTP simulada."""

from __future__ import annotations

from dataclasses import replace

import pytest
import requests

from app.core import llm


class _Resposta:
    def __init__(self, dados: dict) -> None:
        self._dados = dados

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._dados


def test_ollama_envia_modelo_prompt_e_temperatura(monkeypatch):
    capturado = {}

    def falso_post(url, json, timeout):
        capturado.update(url=url, json=json, timeout=timeout)
        return _Resposta({"response": "  ok  "})

    monkeypatch.setattr(llm.requests, "post", falso_post)
    provider = llm.OllamaProvider(host="http://h:1/", model="m")

    assert provider.complete("oi", temperature=0.0) == "ok"
    assert capturado["url"] == "http://h:1/api/generate"
    assert capturado["json"]["model"] == "m"
    assert capturado["json"]["stream"] is False
    assert capturado["json"]["options"] == {"temperature": 0.0}


def test_ollama_indisponivel_vira_runtime_error_acionavel(monkeypatch):
    def falha(*args, **kwargs):
        raise requests.ConnectionError("recusada")

    monkeypatch.setattr(llm.requests, "post", falha)
    with pytest.raises(RuntimeError, match="ollama serve"):
        llm.OllamaProvider(host="http://h", model="m").complete("oi")


def test_get_provider_devolve_ollama_por_padrao():
    assert isinstance(llm.get_provider(), llm.OllamaProvider)


def test_get_provider_recusa_provider_desconhecido(monkeypatch):
    monkeypatch.setattr(llm, "settings", replace(llm.settings, llm_provider="x"))
    with pytest.raises(ValueError, match="não suportado"):
        llm.get_provider()
