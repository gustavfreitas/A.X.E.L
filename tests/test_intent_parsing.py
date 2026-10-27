"""Parsing da resposta do classificador de intenção (sem LLM real)."""

from __future__ import annotations

from app.services import intent as intent_service
from tests.conftest import FakeProvider, intent_json


def test_extract_json_remove_cerca_markdown():
    bruto = '```json\n{"intent": "CODE_DEBUG"}\n```'
    assert intent_service._extract_json(bruto) == '{"intent": "CODE_DEBUG"}'


def test_extract_json_mantem_json_puro():
    assert intent_service._extract_json(' {"a": 1} ') == '{"a": 1}'


def test_classify_le_json_valido():
    provider = FakeProvider(intent_json("SQL_OPTIMIZATION"))
    result = intent_service.classify("query lenta", provider)
    assert result.intent == "SQL_OPTIMIZATION"
    assert result.confidence == "high"
    assert result.requires_clarification is False


def test_classify_aceita_json_dentro_de_cerca_markdown():
    provider = FakeProvider("```json\n" + intent_json("CODE_DEBUG") + "\n```")
    assert intent_service.classify("bug", provider).intent == "CODE_DEBUG"


def test_classify_intent_desconhecida_vira_general_query():
    provider = FakeProvider(intent_json("INVENTADA"))
    assert intent_service.classify("x", provider).intent == "GENERAL_QUERY"


def test_classify_json_quebrado_cai_no_caminho_seguro():
    provider = FakeProvider("isto não é json")
    result = intent_service.classify("x", provider)
    assert result.intent == "GENERAL_QUERY"
    assert result.requires_clarification is True
    assert result.missing_info


def test_classify_missing_info_nulo_vira_lista_vazia():
    provider = FakeProvider('{"intent": "CODE_DEBUG", "missing_info": null}')
    assert intent_service.classify("x", provider).missing_info == []


def test_classify_json_que_nao_e_objeto_nao_derruba():
    provider = FakeProvider("[1, 2, 3]")
    result = intent_service.classify("x", provider)
    assert result.intent == "GENERAL_QUERY"
    assert result.requires_clarification is True


def test_classify_usa_temperatura_zero():
    class Espiao(FakeProvider):
        temperaturas: list[float] = []

        def complete(self, prompt, *, temperature=0.2):
            self.temperaturas.append(temperature)
            return super().complete(prompt, temperature=temperature)

    provider = Espiao(intent_json("EXPLANATION"))
    intent_service.classify("x", provider)
    assert provider.temperaturas == [0.0]
