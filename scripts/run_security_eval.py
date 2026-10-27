"""
Fase 08 — Avaliação de segurança.

Diferença em relação a scripts/run_eval.py: aquele testa só a classificação
de intenção. Este roda o pipeline COMPLETO (Assistant.handle) contra tentativas
de extrair o system prompt, e verifica se a resposta final vazou algo — ou
seja, testa a defesa em profundidade de verdade (prompt + código), não só se
o classificador rotulou certo.

Uso:
    python -m scripts.run_security_eval
"""

from __future__ import annotations

import json
from pathlib import Path

from app.core.llm import get_provider
from app.core.memory import SessionMemory
from app.services.assistant import Assistant
from app.utils import security
from app.utils.preflight import check_ollama

ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "tests" / "security_cases.json"
REPORT_PATH = ROOT / "docs" / "security_evaluation.md"


def run() -> None:
    preflight = check_ollama()
    if not preflight.ok:
        print(f"Não é possível avaliar: {preflight.message}")
        return

    provider = get_provider()
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    rows = []
    for case in cases:
        # Uma instância nova por caso: sem contaminação de histórico entre
        # tentativas de ataque diferentes.
        assistant = Assistant(provider=provider, memory=SessionMemory())
        answer = assistant.handle(case["input"])
        leaked = security.check_output_leakage(answer)
        safe = not leaked

        rows.append(
            {
                "category": case["category"],
                "input": case["input"],
                "answer_preview": answer[:120].replace("\n", " "),
                "safe": safe,
                "leaked_phrases": leaked,
            }
        )
        status = "SEGURO" if safe else "VAZOU"
        print(f"[{status}] {case['category']:<22} | {case['input'][:60]}")
        if leaked:
            print(f"         trecho vazado: {leaked[0][:70]}")

    safe_count = sum(r["safe"] for r in rows)
    print(f"\n{safe_count}/{len(rows)} casos sem vazamento detectado.")

    _write_report(rows, safe_count, len(rows))
    print(f"Relatório salvo em {REPORT_PATH.relative_to(ROOT)}")


def _write_report(rows: list[dict], safe_count: int, total: int) -> None:
    lines = [
        "# A.X.E.L. — Relatório de Avaliação de Segurança (Fase 08)",
        "",
        f"Sem vazamento detectado: **{safe_count}/{total}**",
        "",
        "Testa o pipeline completo (`Assistant.handle`), incluindo a checagem "
        "de vazamento pós-resposta em `app/utils/security.py`, não só a "
        "classificação de intenção.",
        "",
        "| Status | Categoria | Input | Início da resposta |",
        "|---|---|---|---|",
    ]
    for row in rows:
        status = "✅" if row["safe"] else "❌"
        input_short = row["input"].replace("|", "\\|").replace("\n", " ")[:60]
        answer_short = row["answer_preview"].replace("|", "\\|")
        lines.append(
            f"| {status} | {row['category']} | {input_short} | {answer_short} |"
        )

    leaks = [r for r in rows if not r["safe"]]
    if leaks:
        lines += [
            "",
            "## Vazamentos detectados (investigar antes de qualquer deploy)",
            "",
        ]
        for row in leaks:
            lines.append(f"- **{row['category']}**: {row['input'][:80]}")
            lines.append(f"  - Trecho vazado: `{row['leaked_phrases'][0][:100]}`")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
