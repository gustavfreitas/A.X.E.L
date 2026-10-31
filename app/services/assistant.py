from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from app.core import prompts
from app.core.llm import LLMProvider
from app.core.memory import SessionMemory
from app.services import intent as intent_service
from app.services import response as response_service
from app.utils import security
from app.utils.logger import get_logger

logger = get_logger(__name__)

Event = dict[str, Any]


class Assistant:
    """Pipeline: entrada -> intent -> prompt assembly -> LLM -> resposta.

    Cada etapa é um módulo isolado — facilita testar e trocar peças
    (ex.: trocar o classificador de intent por um modelo menor/mais rápido
    sem tocar no resto).
    """

    def __init__(
        self, provider: LLMProvider, memory: SessionMemory | None = None
    ) -> None:
        self.provider = provider
        self.memory = memory or SessionMemory()

    def handle(self, user_input: str) -> str:
        """Versão simples (CLI): devolve só a resposta final."""
        text = ""
        for event in self.handle_stream(user_input):
            if event["type"] == "done":
                text = event["text"]
        return text

    def handle_stream(self, user_input: str) -> Iterator[Event]:
        """Mesmo pipeline, emitindo eventos conforme avança (usado pela web).

        Eventos: `status` (etapa atual), `intent`, `token` (pedaço de texto) e
        `done` (texto final, que é a versão autoritativa: já passou pela
        checagem de vazamento e é o que vai para o histórico).
        """
        security.validate_input(user_input)

        yield {"type": "status", "stage": "classifying"}
        result = intent_service.classify(user_input, self.provider)
        yield {"type": "intent", "intent": result.intent}

        if result.intent == "OUT_OF_SCOPE":
            message = response_service.build_out_of_scope_message()
            self.memory.add(user_input, result.intent, message)
            yield {"type": "done", "text": message, "intent": result.intent}
            return

        if result.requires_clarification:
            message = response_service.build_clarification_message(result)
            self.memory.add(user_input, result.intent, message)
            yield {"type": "done", "text": message, "intent": result.intent}
            return

        full_prompt = prompts.build_full_prompt(
            user_input=user_input,
            intent=result.intent,
            history=self.memory.as_context(),
        )

        yield {"type": "status", "stage": "generating"}
        answer = ""
        for piece in self.provider.stream(full_prompt, temperature=0.2):
            answer += piece
            # Checa a resposta acumulada a cada pedaço: se um trecho interno
            # aparecer, a geração é interrompida na hora. Pode escapar um
            # pedacinho antes do canário completo casar; a versão final
            # (`done`) é sempre a segura.
            if security.check_output_leakage(answer):
                break
            yield {"type": "token", "text": piece}

        leaked = security.check_output_leakage(answer)
        if leaked:
            logger.warning(
                "Vazamento de prompt interno detectado na resposta (%d trecho(s)). "
                "Substituindo por mensagem segura.",
                len(leaked),
            )
            answer = security.SAFE_REFUSAL_MESSAGE

        self.memory.add(user_input, result.intent, answer)
        yield {"type": "done", "text": answer, "intent": result.intent}
