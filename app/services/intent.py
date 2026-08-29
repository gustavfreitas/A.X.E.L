from __future__ import annotations

import json
from dataclasses import dataclass

from app.core import prompts
from app.core.llm import LLMProvider
from app.utils.logger import get_logger

logger = get_logger(__name__)

VALID_INTENTS = {
    "CODE_DEBUG",
    "CODE_OPTIMIZATION",
    "SQL_OPTIMIZATION",
    "ERROR_ANALYSIS",
    "EXPLANATION",
    "GENERAL_QUERY",
    "OUT_OF_SCOPE",
}


@dataclass
class IntentResult:
    intent: str
    confidence: str
    requires_clarification: bool
    missing_info: list[str]


def _extract_json(raw: str) -> str:
    """Modelos pequenos às vezes ignoram a instrução 'sem markdown' e envolvem
    a resposta em ```json ... ```. Em vez de depender só do prompt pra evitar
    isso, tratamos no código, que é determinístico.
    """
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def classify(user_input: str, provider: LLMProvider) -> IntentResult:
    raw = provider.complete(prompts.intent_prompt(user_input), temperature=0.0)
    try:
        data = json.loads(_extract_json(raw))
        intent = data.get("intent", "GENERAL_QUERY")
        if intent not in VALID_INTENTS:
            intent = "GENERAL_QUERY"
        return IntentResult(
            intent=intent,
            confidence=data.get("confidence", "low"),
            requires_clarification=bool(data.get("requires_clarification", False)),
            missing_info=data.get("missing_info", []) or [],
        )
    except (json.JSONDecodeError, AttributeError) as exc:
        # Falha de parsing não pode virar exceção não tratada em produção:
        # cai para o caminho mais seguro (pedir esclarecimento).
        logger.warning("Falha ao parsear resposta de intent: %s | raw=%r", exc, raw)
        return IntentResult(
            intent="GENERAL_QUERY",
            confidence="low",
            requires_clarification=True,
            missing_info=["reformule sua pergunta com mais detalhes"],
        )
