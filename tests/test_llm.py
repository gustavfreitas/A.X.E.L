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


def test_timeout_tem_mensagem_propria_e_nao_diz_que_o_ollama_esta_parado(monkeypatch):
    def demora(*args, **kwargs):
        raise requests.Timeout("lento")

    monkeypatch.setattr(llm.requests, "post", demora)
    with pytest.raises(RuntimeError, match="AXEL_TIMEOUT_SECONDS") as info:
        llm.OllamaProvider(host="http://h", model="m").complete("oi")
    assert "ollama serve" not in str(info.value)


def test_stream_junta_pedacos_e_respeita_done(monkeypatch):
    linhas = [
        b'{"response": "Ol", "done": false}',
        b"",
        b'{"response": "\xc3\xa1", "done": false}',
        b'{"response": "", "done": true}',
        b'{"response": "NAO DEVE APARECER", "done": false}',
    ]

    class Resp:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def raise_for_status(self):
            pass

        def iter_lines(self):
            return iter(linhas)

    def falso_post(url, json, stream, timeout):
        assert stream is True and json["stream"] is True
        return Resp()

    monkeypatch.setattr(llm.requests, "post", falso_post)
    provider = llm.OllamaProvider(host="http://h", model="m")
    assert "".join(provider.stream("oi")) == "Olá"


def test_stream_timeout_tem_mensagem_propria(monkeypatch):
    def falha(*args, **kwargs):
        raise requests.Timeout("lento")

    monkeypatch.setattr(llm.requests, "post", falha)
    with pytest.raises(RuntimeError, match="AXEL_TIMEOUT_SECONDS"):
        list(llm.OllamaProvider(host="http://h", model="m").stream("oi"))


def test_provider_padrao_faz_stream_com_a_resposta_completa():
    class Fixo(llm.LLMProvider):
        def complete(self, prompt, *, temperature=0.2):
            return "inteira"

    assert list(Fixo().stream("x")) == ["inteira"]
