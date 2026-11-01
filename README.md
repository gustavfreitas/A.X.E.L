# A.X.E.L.

[![CI](https://github.com/gustavfreitas/A.X.E.L/actions/workflows/ci.yml/badge.svg)](https://github.com/gustavfreitas/A.X.E.L/actions/workflows/ci.yml)

**Automated X-electronic Engineering Link**

Assistente técnico via CLI, especializado em debug e otimização de código
Python e queries SQL. Interpreta descrições em linguagem natural, classifica
a intenção do pedido e responde com diagnóstico estruturado — sem inventar
causas quando falta contexto.

![Demonstração do A.X.E.L.: pergunta sobre SQL lento respondida em tempo real na interface web](docs/demo.gif)

*Interface web respondendo em streaming, com o modelo `qwen2.5:1.5b` rodando localmente. O modelo é pequeno: as respostas são genéricas e a qualidade do diagnóstico depende dele.*

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

Python 3.11+, Ollama, `requests`, `rich`, FastAPI + uvicorn (interface web), `pytest`, `ruff`, GitHub Actions.

## Security

- `.env` nunca versionado (`.gitignore`); `.env.example` documenta as
  variáveis necessárias sem expor valores.
- System prompt nunca é exposto, mesmo sob pedido direto ou tentativa de
  prompt injection — regra ativa em `security_prompt.txt`.
- Sem execução de código arbitrário fornecido pelo usuário.

## Evaluation

Há três camadas de verificação, com propósitos diferentes:

| Camada | O que verifica | Precisa de Ollama? | Onde roda |
|---|---|---|---|
| Testes unitários (65+) | Pipeline, parsing do classificador, memória, montagem de prompts, defesa de vazamento, provider HTTP. Usam um LLM simulado. | Não | CI a cada push (Python 3.11, 3.12 e 3.13) |
| Avaliação de intenção | Se o classificador rotula corretamente 16 pedidos reais | Sim | Local: `python -m scripts.run_eval` |
| Avaliação de segurança | Se 10 tentativas de extrair o prompt vazam algo no pipeline completo | Sim | Local: `python -m scripts.run_security_eval` |

### Resultados

- **Classificação de intenção: 88% (14/16)**, relatório de 2026-08-29 em [`docs/evaluation.md`](docs/evaluation.md). Com 16 casos, o intervalo de confiança de 95% vai de cerca de 64% a 97%: o número serve para acompanhar mudanças de prompt, não para afirmar uma taxa de acerto geral.
- **Os dois erros** foram `"tá dando erro aqui, pode ajudar?"` (esperado `GENERAL_QUERY`, obtido `ERROR_ANALYSIS`) e um `KeyError` com a chave "que já existe" (esperado `CODE_DEBUG`, obtido `ERROR_ANALYSIS`). Em ambos o modelo pequeno se apoiou na palavra "erro"/`KeyError`; o primeiro também é discutível como rótulo.
- **Segurança: 10/10 sem vazamento** do prompt interno ([`docs/security_evaluation.md`](docs/security_evaluation.md)).

### O que esses números **não** dizem

- A avaliação de intenção mede **só a classificação do pedido** (por exemplo, "isso é otimização de SQL"). **Não mede se o diagnóstico gerado é correto ou útil.** Não existe hoje uma avaliação da qualidade das respostas.
- O dataset é pequeno e escrito pelo próprio autor, então ele não é uma amostra independente de pedidos reais.
- A detecção de vazamento compara **trechos literais** dos prompts internos com a resposta. Um vazamento traduzido ou parafraseado passa por ela (há um teste que documenta esse limite). Por isso a defesa também depende do prompt de segurança e da classificação de intenção, e o resultado 10/10 em 10 tentativas não é uma garantia contra prompt injection.
- Os resultados dependem do modelo local (`qwen2.5:1.5b` por padrão), que é pequeno; com outro modelo os números mudam.

### Como rodar

```bash
pip install -r requirements-dev.txt

pytest                         # testes unitários (não precisam de Ollama)
ruff check . && ruff format --check .

# precisam do Ollama rodando:
pytest -m integration          # classificador contra o dataset, pass/fail por caso
python -m scripts.run_eval     # relatório com accuracy, IC 95% e quebra por intenção
python -m scripts.run_security_eval
```

Se algo falhar com erro de conexão, o problema quase sempre é o Ollama não estar rodando: confira `ollama serve` antes de investigar o código. **Este projeto não usa Docker nem Postgres**; a única dependência externa é o processo do Ollama.

## Installation

Pré-requisito: [Ollama](https://ollama.com) instalado e rodando na sua máquina (ver `docs/architecture.md`, seção "Por que não há deploy tradicional", para o raciocínio por trás dessa decisão).

```bash
# 1. Baixar o modelo e subir o Ollama
ollama pull qwen2.5:1.5b
# se sua máquina tiver pouca RAM (≤4GB) e mesmo assim faltar memória,
# use qwen2.5:0.5b (ainda mais leve) e ajuste OLLAMA_MODEL no .env
ollama serve

# 2. Baixar o código e criar o ambiente (Python 3.11+)
git clone https://github.com/gustavfreitas/A.X.E.L.git
cd A.X.E.L
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .

# 3. Configurar variáveis
cp .env.example .env
```

O pacote ainda **não está publicado no PyPI**; a instalação é a partir do código-fonte. Com `pip install -e .` o comando `axel` fica disponível no terminal (equivale a `python -m app.main`).

## Usage

### Interface web (estilo chat)

```bash
pip install -e ".[web]"   # ou: pip install -r requirements.txt
python -m app.web.server  # ou, com o pacote instalado: axel-web
```

Abre no navegador em `http://127.0.0.1:8000`: tema escuro com vidro (glassmorphism), painel centralizado de altura fixa (só a conversa rola), resposta em tempo real (streaming), blocos de código com botão "Copiar", sugestões rápidas e botão "Nova conversa". O símbolo do projeto (`static/img/axel-logo.png`) funciona como indicador de atividade: pulsa devagar em repouso e mais rápido, com brilho ciano, enquanto o modelo responde. O front-end é separado em módulos: `app/web/static/css/` (tokens, base, layout, ícone, componentes) e `app/web/static/js/` (markdown, api, ui, main). Usa o mesmo pipeline da CLI e o mesmo Ollama local; o servidor só escuta em `127.0.0.1`, então não fica exposto na rede. É um app de uma pessoa só: uma conversa por vez.

A checagem de vazamento do prompt roda sobre o texto acumulado a cada pedaço: se um trecho interno aparece, a geração é interrompida e a resposta final é substituída pela mensagem segura. Como a checagem é por trecho literal, pode escapar um pedaço curto antes do trecho completo casar.

### Linha de comando

```bash
python -m app.main
```

```
você > minha query SQL está demorando 20s para 50 mil registros
AXEL: DIAGNÓSTICO
...
```

Comandos disponíveis no CLI: `sair` (encerra), `/historico` (lista os turnos
da sessão atual), `/limpar` (apaga o histórico).

**Memória entre execuções (opcional)**: por padrão o histórico é só em RAM
e some ao fechar o CLI. Para persistir entre execuções (útil se você fecha e
reabre o terminal no mesmo problema), configure no `.env`:

```
AXEL_MEMORY_BACKEND=sqlite
```

Isso grava as mensagens num arquivo `axel_history.db` local (nunca vai pro
Git — está no `.gitignore`, mesma lógica do `.env`). É opt-in de propósito:
persistir significa guardar trechos de código em texto puro em disco.

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
