"""
Camada de abstração de LLM.

Decisão de arquitetura: o AXEL nunca chama Ollama diretamente do resto da
aplicação. Tudo passa pela interface LLMProvider, para que trocar de backend
(ex.: Ollama local -> API paga em produção) não exija tocar em services/.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

import requests

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, *, temperature: float = 0.2) -> str:
        """Retorna a resposta de texto bruta do modelo para o prompt dado."""
        raise NotImplementedError

    def stream(self, prompt: str, *, temperature: float = 0.2) -> Iterator[str]:
        """Devolve a resposta em pedaços, conforme o modelo gera.

        Implementação padrão: um único pedaço com a resposta completa. Providers
        que suportam streaming de verdade (como o Ollama) sobrescrevem.
        """
        yield self.complete(prompt, temperature=temperature)


class OllamaProvider(LLMProvider):
    def __init__(self, host: str | None = None, model: str | None = None) -> None:
        self.host = (host or settings.ollama_host).rstrip("/")
        self.model = model or settings.ollama_model

    def complete(self, prompt: str, *, temperature: float = 0.2) -> str:
        url = f"{self.host}/api/generate"
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        try:
            response = requests.post(
                url, json=payload, timeout=settings.request_timeout_seconds
            )
            response.raise_for_status()
        except requests.Timeout as exc:
            logger.error("Timeout ao chamar Ollama em %s: %s", url, exc)
            raise RuntimeError(
                "O Ollama demorou mais que "
                f"{settings.request_timeout_seconds}s para responder (ele está "
                "rodando, mas o modelo é lento nesta máquina). Aumente "
                "AXEL_TIMEOUT_SECONDS no .env (ex.: 180) e tente de novo."
            ) from exc
        except requests.RequestException as exc:
            logger.error("Falha ao chamar Ollama em %s: %s", url, exc)
            raise RuntimeError(
                "Não foi possível falar com o Ollama. Verifique se ele está "
                "rodando (`ollama serve`) e se o modelo foi baixado "
                f"(`ollama pull {self.model}`)."
            ) from exc

        data = response.json()
        return data.get("response", "").strip()

    def stream(self, prompt: str, *, temperature: float = 0.2) -> Iterator[str]:
        url = f"{self.host}/api/generate"
        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": True,
            "options": {"temperature": temperature},
        }
        try:
            # O timeout de leitura vale para a espera entre pedaços, não para a
            # resposta inteira: respostas longas não estouram o limite.
            with requests.post(
                url,
                json=payload,
                stream=True,
                timeout=settings.request_timeout_seconds,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("response"):
                        yield data["response"]
                    if data.get("done"):
                        break
        except requests.Timeout as exc:
            logger.error("Timeout no streaming do Ollama em %s: %s", url, exc)
            raise RuntimeError(
                f"O Ollama ficou mais de {settings.request_timeout_seconds}s sem "
                "responder. Aumente AXEL_TIMEOUT_SECONDS no .env e tente de novo."
            ) from exc
        except requests.RequestException as exc:
            logger.error("Falha no streaming do Ollama em %s: %s", url, exc)
            raise RuntimeError(
                "Não foi possível falar com o Ollama. Verifique se ele está "
                "rodando (`ollama serve`) e se o modelo foi baixado "
                f"(`ollama pull {self.model}`)."
            ) from exc


def get_provider() -> LLMProvider:
    """Factory: escolhe o provider com base em settings.llm_provider.

    Hoje só existe Ollama implementado — o ponto de extensão fica aqui, não
    espalhado pelo código (ex.: adicionar AnthropicProvider no futuro).
    """
    if settings.llm_provider == "ollama":
        return OllamaProvider()
    raise ValueError(f"LLM provider não suportado: {settings.llm_provider}")
