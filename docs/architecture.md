# A.X.E.L. — Arquitetura

## Fluxo de dados

```
Usuário (linguagem natural, CLI)
        │
        ▼
services/intent.py ──────► core/llm.py (LLMProvider.complete)
   classifica a intenção        │
        │                       │
        ▼                       │
  requires_clarification?       │
     sim → resposta direta      │
     não │                      │
        ▼                       │
services/assistant.py           │
  monta prompt final ───────────┘
  (core/prompts.py: system + security + response + input + histórico)
        │
        ▼
core/llm.py (LLMProvider.complete) — chamada real ao modelo
        │
        ▼
core/memory.py — grava o turno na sessão
        │
        ▼
app/main.py — formata e imprime no CLI (rich)
```

## Por que provider-agnostic (`core/llm.py`)

Decisão deliberada: nenhum módulo de `services/` ou `app/main.py` sabe que o
backend é Ollama. Todos dependem da interface `LLMProvider` (método
`complete`). Isso significa:

- Trocar Ollama por uma API paga (Anthropic, OpenAI, Gemini) em produção é
  implementar uma nova classe em `core/llm.py` e mudar uma variável de
  ambiente (`AXEL_LLM_PROVIDER`) — zero mudança no resto do código.
- Os testes de intent (`tests/test_intent.py`) rodam contra qualquer provider
  configurado, sem acoplamento ao Ollama especificamente.

Trade-off assumido: por rodar localmente via Ollama, a v1 depende da
qualidade do modelo local escolhido. Isso é aceitável para o escopo definido
(debug/otimização em Python/SQL de escopo único), mas seria um ponto a
revisar antes de qualquer uso em produção com problemas mais complexos.

## Por que duas chamadas de LLM (intent + resposta) em vez de uma só

Poderia-se pedir tudo em uma única chamada ("classifique e responda"). A
decisão de separar em duas chamadas foi deliberada:

1. **Controle de fluxo**: se `requires_clarification=true`, o AXEL nunca
   chega a gerar um diagnóstico especulativo — a ramificação acontece em
   código Python, não depende do modelo "se comportar bem" dentro de um
   prompt único.
2. **Avaliação isolada**: dá pra medir accuracy da classificação de intenção
   separadamente da qualidade da resposta final (Fase 05 do plano).
3. **Custo controlado com temperature=0.0** na classificação (determinístico)
   vs `temperature=0.2` na resposta (alguma flexibilidade natural).

Trade-off: duas chamadas = mais latência que uma só. Aceitável na v1 porque
roda local (sem custo de API) e o ganho em controle/testabilidade compensa.

## Camadas de prompt (`prompts/`)

Cada arquivo `.txt` é uma responsabilidade isolada, concatenada em
`core/prompts.py::build_full_prompt` na ordem: identidade/comportamento →
segurança → formatação → input do usuário. Isso permite editar/testar cada
camada isoladamente (ex.: reforçar `security_prompt.txt` sem tocar no resto).

## Ferramentas de desenvolvimento (fora do produto)

- **Ollama**: runtime local do LLM usado pelo `OllamaProvider`. Faz parte do
  produto (é a dependência de execução), não só da fase de dev.
- **Antigravity (Google)**: IDE agent-first usada para acelerar a
  implementação deste esqueleto (scaffolding, testes, iteração). Não é uma
  dependência do AXEL em runtime — é uma ferramenta de processo de
  engenharia, registrada aqui para transparência sobre como o projeto foi
  construído, sem misturar isso com a arquitetura do produto em si.

## Pontos de extensão previstos (v2+)

- `services/intent.py`: novas intents exigem só adicionar ao `VALID_INTENTS`
  e ajustar `prompts/intent_prompt.txt`.
- `core/memory.py`: trocar `deque` em memória por persistência (SQLite/Redis)
  sem mudar a interface pública (`add`, `as_context`).
- `core/llm.py`: adicionar `AnthropicProvider`/`GeminiProvider` para produção.
