from __future__ import annotations

from functools import lru_cache
from importlib import resources

_PACKAGE = "app.prompts"


@lru_cache(maxsize=None)
def _load(filename: str) -> str:
    """Carrega via importlib.resources, não caminho relativo em disco.

    Decisão de arquitetura: um caminho tipo Path(__file__).parents[N]/"prompts"
    só funciona rodando direto do clone do repositório. Quebra silenciosamente
    quando o pacote é instalado via pip (os .txt não ficam onde o caminho
    relativo espera). importlib.resources funciona nos dois casos porque
    resolve a partir da estrutura do pacote Python, não do sistema de
    arquivos do projeto.
    """
    return resources.files(_PACKAGE).joinpath(filename).read_text(encoding="utf-8")


def system_prompt() -> str:
    return _load("system_prompt.txt")


def security_prompt() -> str:
    return _load("security_prompt.txt")


def intent_prompt(user_input: str) -> str:
    return _load("intent_prompt.txt").replace("{user_input}", user_input)


def response_prompt(intent: str, history: str) -> str:
    return (
        _load("response_prompt.txt")
        .replace("{intent}", intent)
        .replace("{history}", history or "(sem histórico relevante)")
    )


def build_full_prompt(*, user_input: str, intent: str, history: str) -> str:
    """Monta o prompt final concatenando as camadas na ordem correta:
    identidade/comportamento -> segurança -> instrução de formatação -> input.
    """
    return "\n\n---\n\n".join(
        [
            system_prompt(),
            security_prompt(),
            response_prompt(intent=intent, history=history),
            f"MENSAGEM DO USUÁRIO:\n{user_input}",
        ]
    )
