import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_provider: str = os.getenv("AXEL_LLM_PROVIDER", "ollama")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")
    max_history_turns: int = int(os.getenv("AXEL_MAX_HISTORY_TURNS", "6"))
    max_history_chars: int = int(os.getenv("AXEL_MAX_HISTORY_CHARS", "3000"))
    memory_backend: str = os.getenv("AXEL_MEMORY_BACKEND", "ram")
    history_db_path: str = os.getenv("AXEL_HISTORY_DB_PATH", "axel_history.db")
    log_level: str = os.getenv("AXEL_LOG_LEVEL", "INFO")
    request_timeout_seconds: int = int(os.getenv("AXEL_TIMEOUT_SECONDS", "60"))


settings = Settings()
