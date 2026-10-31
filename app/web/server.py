"""Interface web local do A.X.E.L. (estilo chat).

Roda só na sua máquina (127.0.0.1): o navegador conversa com este servidor, que
usa exatamente o mesmo pipeline da CLI (`Assistant`) e o Ollama local.
"""

from __future__ import annotations

import json
import threading
import webbrowser
from collections.abc import Iterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import settings
from app.core.llm import LLMProvider, get_provider
from app.core.memory import get_memory
from app.services.assistant import Assistant
from app.utils.logger import get_logger
from app.utils.preflight import check_ollama
from app.utils.security import InputValidationError

logger = get_logger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


class ChatRequest(BaseModel):
    message: str


def _linha(evento: dict) -> str:
    return json.dumps(evento, ensure_ascii=False) + "\n"


def create_app(
    assistant: Assistant | None = None, provider: LLMProvider | None = None
) -> FastAPI:
    """Cria o app. Em produção usa Ollama; nos testes recebe um Assistant falso."""
    app = FastAPI(title="A.X.E.L.", docs_url=None, redoc_url=None)
    state = {"assistant": assistant}
    # Uma conversa por vez: é um app local de uma pessoa só.
    lock = threading.Lock()

    def get_assistant() -> Assistant:
        if state["assistant"] is None:
            state["assistant"] = Assistant(
                provider or get_provider(), memory=get_memory()
            )
        return state["assistant"]

    # CSS e JS da interface (componentizados em static/css e static/js)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health")
    def health() -> dict:
        resultado = check_ollama()
        return {
            "ok": resultado.ok,
            "message": resultado.message,
            "model": settings.ollama_model,
        }

    @app.get("/api/history")
    def history() -> list[dict]:
        return [
            {"user": t.user, "intent": t.intent, "response": t.response}
            for t in get_assistant().memory.history()
        ]

    @app.post("/api/clear")
    def clear() -> dict:
        get_assistant().memory.clear()
        return {"ok": True}

    @app.post("/api/chat")
    def chat(req: ChatRequest) -> StreamingResponse:
        def gerar() -> Iterator[str]:
            if not lock.acquire(blocking=False):
                yield _linha(
                    {
                        "type": "error",
                        "message": "Já existe uma resposta em andamento. Aguarde.",
                    }
                )
                return
            try:
                for evento in get_assistant().handle_stream(req.message):
                    yield _linha(evento)
            except InputValidationError as exc:
                yield _linha({"type": "error", "message": str(exc)})
            except RuntimeError as exc:
                yield _linha({"type": "error", "message": str(exc)})
            except Exception:  # noqa: BLE001 - não vaza detalhes internos ao navegador
                logger.exception("Erro inesperado no /api/chat")
                yield _linha(
                    {"type": "error", "message": "Erro interno. Veja o terminal."}
                )
            finally:
                lock.release()

        return StreamingResponse(gerar(), media_type="application/x-ndjson")

    return app


def main() -> None:
    import uvicorn

    host, port = "127.0.0.1", 8000
    resultado = check_ollama()
    if not resultado.ok:
        print(f"Aviso: {resultado.message}")
    url = f"http://{host}:{port}"
    print(f"A.X.E.L. web em {url}  (Ctrl+C para encerrar)")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    uvicorn.run(create_app(), host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
