from __future__ import annotations

from app.services.intent import IntentResult


def build_clarification_message(result: IntentResult) -> str:
    if result.missing_info:
        items = "\n".join(f"  - {item}" for item in result.missing_info)
        return "Preciso de mais detalhes antes de diagnosticar:\n" + items
    return "Pode detalhar melhor o problema (código, erro ou comportamento observado)?"


def build_out_of_scope_message() -> str:
    return (
        "Esse assunto está fora do meu escopo atual. Sou especializado em debug "
        "e otimização de código Python e queries SQL."
    )
