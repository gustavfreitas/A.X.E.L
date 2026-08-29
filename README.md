# A.X.E.L.

**Automated X-electronic Engineering Link**

Assistente técnico via CLI, especializado em debug e otimização de código
Python e queries SQL. Interpreta descrições em linguagem natural, classifica
a intenção do pedido e responde com diagnóstico estruturado — sem inventar
causas quando falta contexto.

## Overview

O AXEL nasceu como desafio do bootcamp DIO (Dados, IA Generativa e
Cibersegurança) e evoluiu para uma implementação autoral com foco em
Engenharia de Prompt e arquitetura desacoplada. Detalhes de escopo e decisões
de produto em [`docs/product_brief.md`](docs/product_brief.md); detalhes
técnicos de arquitetura em [`docs/architecture.md`](docs/architecture.md).

## Problem

Transformar descrições informais de bugs, lentidão ou erros em diagnósticos
objetivos e acionáveis — sem exigir que o usuário formule a pergunta de forma
técnica.

## Architecture

Pipeline desacoplado: classificação de intenção → montagem de prompt em
camadas → chamada ao LLM (provider-agnostic, Ollama por padrão) → resposta
estruturada. Ver diagrama completo em `docs/architecture.md`.

## Prompt Engineering

Prompts organizados por responsabilidade em `app/prompts/`: identidade e
comportamento (`system_prompt.txt`), regras de segurança
(`security_prompt.txt`), classificação de intenção (`intent_prompt.txt`) e
formatação de resposta (`response_prompt.txt`).

## Technologies

Python 3.11+, Ollama, `requests`, `rich`, `pytest`.

## Security

- `.env` nunca versionado (`.gitignore`); `.env.example` documenta as
  variáveis necessárias sem expor valores.
- System prompt nunca é exposto, mesmo sob pedido direto ou tentativa de
  prompt injection — regra ativa em `security_prompt.txt`.
- Sem execução de código arbitrário fornecido pelo usuário.

## Evaluation

Dataset de casos de teste em `tests/test_cases.json`, cobrindo classificação
correta de intenção, pedidos ambíguos e tentativa de prompt injection.

Duas formas de rodar:

```bash
# Testes automatizados (pass/fail, integra com CI no futuro)
pytest tests/test_intent.py -v

# Relatório de avaliação com accuracy e histórico (Fase 05)
python -m scripts.run_eval
```

O segundo comando gera `docs/evaluation.md` com a accuracy geral e o detalhe
de cada caso — é o que deve ser reexecutado a cada iteração de prompt para
medir se a mudança melhorou ou piorou os resultados.

Se qualquer um dos dois falhar com erro de conexão, o problema quase sempre
é o Ollama não estar rodando — confira `ollama serve` antes de investigar o
código do AXEL. **Este projeto não usa Docker nem Postgres**; a única
dependência externa é o processo do Ollama.

## Installation

Duas formas de instalar:

**Via pip (recomendado, uma vez publicado):**

```bash
pip install axel-tech-assistant
axel
```

**A partir do código-fonte (desenvolvimento):**

```bash
# 1. Instalar e subir o Ollama
# https://ollama.com
ollama pull qwen2.5:1.5b
# se sua máquina tiver pouca RAM (≤4GB) e mesmo assim faltar memória,
# use qwen2.5:0.5b (ainda mais leve) e ajuste OLLAMA_MODEL no .env
ollama serve

# 2. Ambiente Python
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar variáveis
cp .env.example .env
```

Nos dois casos, o Ollama continua sendo pré-requisito rodando na máquina de
quem usa — ver `docs/architecture.md`, seção "Por que não há deploy
tradicional", para o raciocínio completo por trás dessa decisão.

## Usage

```bash
python -m app.main
```

```
você > minha query SQL está demorando 20s para 50 mil registros
AXEL: DIAGNÓSTICO
...
```

## Deployment

Não definido ainda — depende da stack final avaliada após validação do MVP
local (ver `docs/product_brief.md`, seção Limitações).

## Roadmap

- v1 (atual): CLI, domínio Python/SQL, Ollama local.
- v2: persistência de memória, análise de dados como segundo domínio.
- v3: API REST, provider de produção (API paga) como alternativa ao Ollama.

## Author

Projeto desenvolvido como parte do bootcamp DIO (Bradesco — Dados,
Cibersegurança e IA Generativa), evoluído para implementação autoral.
