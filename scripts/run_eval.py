"""
Fase 05 — Avaliação do AXEL.

Roda tests/test_cases.json contra o classificador de intenção real, calcula
accuracy e grava um relatório em docs/evaluation.md. Feito como script
separado (não só pytest) porque o objetivo aqui não é "passar/falhar" —
é medir e registrar accuracy ao longo do tempo, à medida que os prompts
forem iterados.

Uso:
    python -m scripts.run_eval
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.core.llm import get_provider
from app.services import intent as intent_service
from app.utils.preflight import check_ollama

ROOT = Path(__file__).resolve().parents[1]
TEST_CASES_PATH = ROOT / "tests" / "test_cases.json"
REPORT_PATH = ROOT / "docs" / "evaluation.md"


def run() -> None:
    preflight = check_ollama()
    if not preflight.ok:
        print(f"Não é possível avaliar: {preflight.message}")
        return

    provider = get_provider()
    cases = json.loads(TEST_CASES_PATH.read_text(encoding="utf-8"))

    rows = []
    correct = 0
    for case in cases:
        result = intent_service.classify(case["input"], provider)
        passed = result.intent == case["expected_intent"]
        if "expected_requires_clarification" in case:
            passed = passed and (
                result.requires_clarification
                == case["expected_requires_clarification"]
            )
        correct += int(passed)
        rows.append(
            {
                "input": case["input"],
                "expected": case["expected_intent"],
                "got": result.intent,
                "confidence": result.confidence,
                "passed": passed,
            }
        )
        status = "OK" if passed else "FALHOU"
        print(f"[{status}] esperado={case['expected_intent']:<18} obtido={result.intent:<18} | {case['input'][:60]}")

    accuracy = correct / len(cases) if cases else 0.0
    print(f"\nAccuracy: {correct}/{len(cases)} ({accuracy:.0%})")

    _write_report(rows, accuracy)
    print(f"Relatório salvo em {REPORT_PATH.relative_to(ROOT)}")


def _write_report(rows: list[dict], accuracy: float) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# A.X.E.L. — Relatório de Avaliação (Fase 05)",
        "",
        f"Gerado em: {timestamp}",
        f"Accuracy de intent: **{accuracy:.0%}** ({sum(r['passed'] for r in rows)}/{len(rows)})",
        "",
        "| Status | Esperado | Obtido | Confiança | Input |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        status = "✅" if row["passed"] else "❌"
        input_short = row["input"].replace("|", "\\|")[:80]
        lines.append(
            f"| {status} | {row['expected']} | {row['got']} | {row['confidence']} | {input_short} |"
        )

    failures = [r for r in rows if not r["passed"]]
    if failures:
        lines += ["", "## Casos que falharam (analisar antes de iterar o prompt)", ""]
        for row in failures:
            lines.append(f"- **Input**: {row['input']}")
            lines.append(f"  - Esperado: `{row['expected']}` | Obtido: `{row['got']}`")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    run()
