from __future__ import annotations

from app.core import prompts
from app.core.llm import LLMProvider
from app.core.memory import SessionMemory
from app.services import intent as intent_service
from app.services import response as response_service
from app.utils import security
from app.utils.logger import get_logger

logger = get_logger(__name__)


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
        security.validate_input(user_input)

        result = intent_service.classify(user_input, self.provider)

        if result.intent == "OUT_OF_SCOPE":
            message = response_service.build_out_of_scope_message()
            self.memory.add(user_input, result.intent, message)
            return message

        if result.requires_clarification:
            message = response_service.build_clarification_message(result)
            self.memory.add(user_input, result.intent, message)
            return message

        full_prompt = prompts.build_full_prompt(
            user_input=user_input,
            intent=result.intent,
            history=self.memory.as_context(),
        )
        answer = self.provider.complete(full_prompt, temperature=0.2)

        leaked = security.check_output_leakage(answer)
        if leaked:
            logger.warning(
                "Vazamento de prompt interno detectado na resposta (%d trecho(s)). "
                "Substituindo por mensagem segura.",
                len(leaked),
            )
            answer = security.SAFE_REFUSAL_MESSAGE

        self.memory.add(user_input, result.intent, answer)
        return answer
