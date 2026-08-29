# A.X.E.L. — Log de Iteração de Prompts (Fase 05)

Registro das versões do `intent_prompt.txt` e o efeito de cada mudança na
accuracy medida por `scripts/run_eval.py`, contra `tests/test_cases.json`.
Mantido como evidência do processo de engenharia, não só do resultado final.

## v1 — baseline, só regras em texto

Accuracy: **57% (4/7)**

Falhas: CSV confundido com SQL; "meu código não funciona" classificado como
CODE_DEBUG em vez de pedir esclarecimento; assunto fora de domínio (filme)
classificado como GENERAL_QUERY em vez de OUT_OF_SCOPE.

## v2 — few-shot não balanceado (4 exemplos, cobrindo só 4 das 7 intents)

Accuracy: **43% (3/7)** — piorou.

Os dois casos-alvo (CSV, filme fora de escopo) passaram a acertar. Mas
`ERROR_ANALYSIS` e `EXPLANATION` — que não tinham exemplo no prompt —
regrediram para `CODE_DEBUG`/`CODE_OPTIMIZATION`. Também apareceu um caso de
resposta envolta em ` ```json ` apesar da instrução dizer "sem markdown",
quebrando o parser e mascarando o resultado real daquele caso.

**Aprendizado**: few-shot em modelo pequeno não é estritamente aditivo — um
exemplo não só ensina o padrão dele, ele também *puxa* a distribuição de
saída na direção das classes demonstradas, às custas das classes sem
exemplo. Corrigir só os casos que falharam, sem balancear as demais classes,
troca um tipo de erro por outro.

## v3 — few-shot balanceado (1 exemplo por intenção, 7 no total) + parsing
robusto no código (remove crases de markdown antes de tentar `json.loads`)

Duas mudanças na mesma iteração, deliberadamente: o parsing é uma correção
de robustez independente do modelo (deveria ter sido feito desde o início,
já que "seguir instrução negativa de formatação" é um dos pontos mais
inconsistentes em modelos pequenos). O rebalanceamento dos exemplos é a
correção de fato do prompt.

Resultado: **86% (6/7)** — subiu de 57% (v1) para 86%. Os dois casos-alvo
originais (CSV, filme fora de escopo) continuaram corretos, e nenhuma das
classes sem exemplo direto na v2 regrediu — confirma que o rebalanceamento
foi a correção certa, não um acaso.

**Caso que persiste**: "meu código não funciona" continua caindo em
`CODE_DEBUG` em vez de `GENERAL_QUERY`, mesmo com um exemplo quase idêntico
no prompt (`{"intent": "GENERAL_QUERY", ...}`). Isso é notável — é o único
caso com exemplo direto que ainda falha.

## Nota metodológica

Com um dataset de só 7 casos, cada acerto/erro individual vale ~14 pontos
percentuais de accuracy. Isso é o suficiente para orientar a direção do
ajuste (como aconteceu aqui), mas não é robusto o bastante para afirmar
"86% de accuracy" como número definitivo do sistema — o dataset precisa
crescer (Fase 06/Sprint seguinte) antes de qualquer citação desse número em
portfólio como métrica final.

## v4 — correção da causa raiz do caso persistente + dataset ampliado

**Causa raiz do caso persistente**: a própria definição de `CODE_DEBUG` na lista
de intents continha a frase "algo não funciona" — ou seja, o prompt ensinava o
modelo a associar diretamente "não funciona" a `CODE_DEBUG`, contradizendo o
exemplo few-shot que dizia o oposto para essa mesma frase. O modelo estava
seguindo a definição da classe, não o exemplo (mais peso pra definição do que
pro exemplo, aparentemente). Corrigido reescrevendo a definição de `CODE_DEBUG`
para exigir detalhe concreto, e adicionando regra de contraste explícita entre
"não funciona" vago (→ GENERAL_QUERY) e "não funciona" com detalhe (→ CODE_DEBUG).

**Dataset ampliado** de 7 para 16 casos, 2+ por classe, incluindo variações que
não são cópia quase literal dos exemplos few-shot (para medir generalização
real, não decoreba) e uma segunda variação de prompt injection (jailbreak via
"esqueça que você é o AXEL...").

Resultado: **88% (14/16)**. Subiu de 57% → 86% → 88% ao longo das iterações,
sem nenhuma regressão nas classes já corrigidas — evidência de que os ajustes
foram cirúrgicos, não "sorte" de reordenar o problema.

**Casos que restaram**: os dois erros são a mesma confusão — `ERROR_ANALYSIS`
puxado por menção a "erro"/nome de exceção (`KeyError`), mesmo sem um
traceback de verdade colado. Análise: isso não é mais um bug de prompt, é uma
sobreposição real na taxonomia entre `CODE_DEBUG` e `ERROR_ANALYSIS` — as
duas intenções levam ao mesmo formato de resposta estruturada em
`response_prompt.txt`, então o custo prático dessa confusão para o usuário
final é baixo. Decisão registrada: **não perseguir esse ajuste específico**,
para não repetir o padrão da v2 (corrigir um caso e desbalancear outro em
troca). 88% com um modelo de 1.5B parâmetros, sob restrição de ~4GB de RAM,
é um resultado defensável e documentado — inclusive o processo de chegar
até aqui é, por si, o argumento mais forte de portfólio desta fase.

Se algum caso específico continuar instável, a próxima alavanca não é
adicionar mais exemplos (risco de reintroduzir o viés da v2), e sim:
1. Aumentar `temperature=0.0` para garantir determinismo total (já está assim).
2. Rodar o mesmo caso 3-5x para checar se a falha é sistemática ou só
   variância do modelo pequeno — isso muda a resposta (ajustar prompt vs.
   aceitar como limitação de hardware documentada).
