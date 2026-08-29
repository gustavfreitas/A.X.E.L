from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


@lru_cache(maxsize=None)
def _load(filename: str) -> str:
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


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
