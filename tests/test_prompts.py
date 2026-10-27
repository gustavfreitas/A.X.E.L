"""Montagem dos prompts: placeholders resolvidos e camadas na ordem certa."""

from __future__ import annotations

from app.core import prompts


def test_intent_prompt_injeta_a_mensagem_do_usuario():
    texto = prompts.intent_prompt("minha query está lenta")
    assert "minha query está lenta" in texto
    assert "{user_input}" not in texto


def test_response_prompt_resolve_intent_e_historico():
    texto = prompts.response_prompt(intent="CODE_DEBUG", history="Usuário: oi")
    assert "CODE_DEBUG" in texto
    assert "Usuário: oi" in texto
    assert "{intent}" not in texto and "{history}" not in texto


def test_response_prompt_sem_historico_usa_texto_padrao():
    texto = prompts.response_prompt(intent="CODE_DEBUG", history="")
    assert "sem histórico relevante" in texto


def test_prompt_completo_tem_as_camadas_na_ordem():
    texto = prompts.build_full_prompt(
        user_input="PERGUNTA-UNICA", intent="CODE_DEBUG", history=""
    )
    posicoes = [
        texto.index(prompts.system_prompt()[:40]),
        texto.index(prompts.security_prompt()[:40]),
        texto.index("MENSAGEM DO USUÁRIO"),
        texto.index("PERGUNTA-UNICA"),
    ]
    assert posicoes == sorted(posicoes)


def test_todos_os_arquivos_de_prompt_existem_e_nao_estao_vazios():
    for carregar in (prompts.system_prompt, prompts.security_prompt):
        assert carregar().strip()
