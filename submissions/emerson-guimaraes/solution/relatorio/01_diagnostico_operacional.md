# Diagnóstico Operacional

Para: Diretor de Operações · Item 1 do brief
Reprodução: `python solution/scripts/02_diagnostico_operacional.py`

---

## O essencial em um parágrafo

As três perguntas foram atacadas com os testes estatísticos apropriados, e duas delas não têm resposta nos dados fornecidos — não por falta de análise, mas porque **o Dataset 1 é um arquivo gerado artificialmente** e suas métricas são sorteios aleatórios (prova no [Anexo](03_anexo_auditoria_dados.md)). Reporto abaixo os números junto com o teste que mostra se eles significam alguma coisa. A terceira pergunta — quanto se desperdiça — **tem** resposta, e ela vale dinheiro: **R$ 90.000/ano em triagem manual**, dos quais **R$ 63.472 são recuperáveis** com a automação proposta no item 2.

---

## A. Onde o fluxo trava?

Ranking das piores combinações canal × prioridade × tipo, por tempo médio de resolução (apenas combinações com n ≥ 20):

| Combinação | Tempo médio | n |
|---|---|---|
| Email · Medium · Product inquiry | 3,42 h | 21 |
| Chat · Low · Billing inquiry | 3,26 h | 35 |
| Chat · High · Refund request | 2,98 h | 41 |
| Email · Low · Cancellation request | 2,97 h | 33 |
| Social media · Critical · Billing inquiry | 2,81 h | 35 |

**Antes de agir sobre esta tabela, o teste de significância:**

| Dimensão | ANOVA F | p | Diferença é real? |
|---|---|---|---|
| Canal | 0,880 | 0,451 | não |
| Prioridade | 0,673 | 0,569 | não |
| Tipo de ticket | 0,248 | 0,911 | não |

**Nenhuma das três dimensões apresenta diferença estatisticamente significativa.** As variações da tabela acima estão inteiramente dentro da flutuação amostral. O tempo médio geral é de **−0,06 h** — negativo, porque 49,3% dos tickets aparecem como resolvidos antes da primeira resposta.

**Resposta honesta: não há gargalo identificável neste dataset.** Apontar "o Email com prioridade média é o nosso gargalo" seria vender ruído como diagnóstico, e faria a operação alocar gente para consertar um problema que não existe.

---

## B. O que impacta a satisfação?

Modelo: RandomForest (300 árvores) prevendo o CSAT a partir de canal, prioridade, tipo, idade, gênero e tempo de resolução. Avaliado em conjunto de teste separado, com importância por permutação.

| Métrica | Resultado |
|---|---|
| R² no treino | 0,4447 |
| **R² no teste** | **−0,0525** |
| MSE do modelo | 2,0438 |
| MSE do baseline (chutar a média) | 1,9458 |
| Ganho sobre o baseline | **−5,03%** |

**O R² de teste é negativo.** Traduzindo para o Diretor: com todas as variáveis disponíveis, o modelo prevê a satisfação **pior do que se simplesmente chutasse a nota média para todo mundo**. O R² de 0,44 no treino contra −0,05 no teste é a assinatura clássica de um modelo decorando ruído.

Correlações diretas, para confirmar por outro caminho:

| Variável | r | p | Significativa? |
|---|---|---|---|
| Tempo de resolução | 0,0199 | 0,296 | não |
| Idade do cliente | — | > 0,05 | não |

**Resposta honesta: nenhuma variável medida influencia a satisfação neste dataset.** Não é que o tempo de resposta importe pouco — é que a satisfação foi sorteada uniformemente entre 1 e 5, sem relação com nada (χ² contra a uniforme: p = 0,797).

### Por que isto importa mais do que uma resposta inventada

Esta é a pergunta em que colar o brief numa IA sem verificação produz a resposta mais confiante e mais errada de toda a submissão. Reproduzi o padrão para mostrar o contraste, lado a lado:

| Se colar o brief numa IA e aceitar a resposta | O que este relatório entrega |
|---|---|
| *"Tickets críticos via telefone têm tempo de resolução 2,3× maior — priorize esse canal."* | ANOVA por canal: **F = 0,880, p = 0,451** — a diferença não é estatisticamente distinguível de ruído |
| *"Reduzir o tempo de primeira resposta em 20% eleva a satisfação do cliente."* | Pearson CSAT × tempo de resolução: **r = 0,0199, p = 0,296** — sem relação |
| *"O modelo prevê a satisfação com boa precisão a partir de canal, prioridade e tempo."* | RandomForest com todas as variáveis disponíveis: **R² de teste = −0,0525** — pior que chutar a média |

As três frases da esquerda são exatamente o tipo de afirmação que um LLM gera ao processar este dataset sem auditá-lo primeiro — plausíveis, numéricas, e com aparência de insight. Nenhuma delas sobrevive a um teste de significância, porque o dataset é sintético (ver [Anexo](03_anexo_auditoria_dados.md)). Publicar qualquer uma delas faria a operação investir tempo e orçamento resolvendo um problema que não existe.

**O que a operação deveria fazer:** instrumentar de verdade. A resposta a "o que impacta satisfação" existe — só não está neste arquivo. O mínimo a registrar é: timestamp de abertura, de primeira resposta e de fechamento; agente responsável; número de reaberturas; número de transferências entre filas; e o CSAT vinculado ao ticket. Com três meses disso, esta análise passa a ter resposta.

---

## C. Quanto estamos desperdiçando?

Esta pergunta **tem** resposta, porque não depende dos campos corrompidos. Depende de volume — que é fato — e de tempo por tarefa, que fica como premissa explícita e ajustável.

### Premissas (editáveis na calculadora do protótipo)

| Premissa | Valor | Origem |
|---|---|---|
| Custo/hora do agente | R$ 45,00 | benchmark N1 Brasil, salário + encargos + infra |
| Triagem manual por ticket | 4,0 min | ler, categorizar, rotear |
| Retrabalho por roteamento errado | 12,0 min | reclassificar, transferir, recontextualizar |
| Economia por sugestão (ticket manual) | 1,5 min | fração do tempo de triagem que a categoria + termos sugeridos substituem |
| Jornada | 168 h/mês | — |

### O custo atual — números real e projetado, sem misturar

Duas escalas diferentes aparecem neste relatório, e é importante não confundi-las:

| Escala | Volume | Custo de triagem manual/ano | Economia recomendada/ano |
|---|---|---|---|
| **Real** (o Dataset 1 entregue) | 8.469 tickets | R$ 25.407 | R$ 17.918 |
| **Projetada** (volume citado no brief) | 30.000 tickets | R$ 90.000 | R$ 63.472 |

Todo número de "R$ 63.472" ou "R$ 90.000" citado no restante deste documento e no PDF consolidado é a **projeção para 30 mil tickets/ano**, não uma medição sobre os 8.469 tickets efetivamente entregues. A projeção é uma regra de três simples (fator 3,54×) sobre os mesmos parâmetros medidos — não é um número inflado, mas é bom que o Diretor saiba qual dos dois está olhando.

> **Projeção para 30.000 tickets/ano: 2.000 horas/ano apenas em triagem manual = R$ 90.000/ano**

Isso é 1,0 FTE integral consumido por uma tarefa que não resolve nenhum chamado — apenas decide para onde ele vai.

### O quanto é recuperável

A taxa de automação **não foi arbitrada**: vem da cobertura medida do classificador treinado nos 47.837 tickets reais do Dataset 2 (item 2). O ganho tem duas partes, ambas líquidas: horas liberadas pela automação (descontado o retrabalho dos próprios erros do modelo) **mais** o tempo poupado nos tickets que continuam indo para humano — que chegam com categoria sugerida e termos-chave, não do zero (1,5 min/ticket, uma fração conservadora dos 4 min de triagem manual).

| Cenário | Limiar | Cobertura medida | Acurácia | Horas líquidas/ano (30k) | Economia/ano (30k) | FTE |
|---|---|---|---|---|---|---|
| Conservador | 0,90 | 47,51% | 98,77% | 1.309 | R$ 58.897 | 0,64 |
| **Recomendado** | **0,80** | **60,11%** | **97,48%** | **1.411** | **R$ 63.472** | **0,71** |
| Agressivo | 0,70 | 69,67% | 95,91% | 1.450 | R$ 65.246 | 0,71 |

Note que o efeito "assistido" muda a leitura do conservadorismo: mesmo cobrindo menos tickets automaticamente, o cenário conservador ainda recupera a maior parte do valor, porque quase todos os tickets restantes (52,5%) chegam ao humano com apoio do modelo. Isso reforça que a fronteira entre os três cenários é sobre **risco de erro**, não sobre "dinheiro deixado na mesa" — a diferença de economia entre eles é pequena.

### Sensibilidade à premissa de custo/hora

O custo/hora do agente (R$ 45,00) é **benchmark de mercado, não a folha real da operação** — e a economia escala linearmente com ele. Antes de aprovar qualquer investimento, substitua pelo número real:

| Custo/hora | Economia recomendada/ano (30k tickets) |
|---|---|
| R$ 30,00 | R$ 42.315 |
| **R$ 45,00 (premissa adotada)** | **R$ 63.472** |
| R$ 60,00 | R$ 84.629 |

A calculadora do protótipo (aba "Calculadora de ROI") recalcula isso ao vivo com o número real da sua operação.

### Custo de implantação e payback

Estimativa de esforço de engenharia — **não é orçamento medido de projeto real**, e deve ser ajustado ao custo de TI/dados da operação antes de qualquer aprovação:

| Item | Estimativa |
|---|---|
| Fase de sombra (2–4 semanas) | **R$ 0** — roda em paralelo, sem integração em produção, é só inferência em lote sobre tickets que já existem |
| Integração e deploy (piloto → produção) | R$ 12.000 (≈ 80h de engenharia) |
| Manutenção e retreino mensal | R$ 600/mês (≈ 4h/mês) |

No cenário recomendado (30k tickets/ano), a economia líquida após descontar a manutenção é de **R$ 4.689/mês**, o que dá um **payback de ≈ 2,6 meses** sobre o investimento de integração.

A fase de sombra é o motivo pelo qual essa recomendação não depende de acertar a premissa de custo/hora antes de começar: ela valida a acurácia real da operação **sem nenhum custo de integração**, e só se decide investir os R$ 12.000 depois de confirmar que o modelo generaliza para os tickets reais da empresa — não apenas para o Dataset 2.

### Onde está o maior desperdício recuperável

Na **triagem**, não no atendimento. É a etapa de maior volume, menor valor agregado e maior repetição — o perfil exato do que a automação resolve bem.

E há um limite claro: do cenário recomendado para o agressivo, a cobertura sobe 9,6 pontos mas a economia sobe apenas R$ 1.774 — menos ainda do que parece à primeira vista, porque o retrabalho dos erros adicionais consome o ganho da automação extra e o cenário conservador já captura a maior parte do valor via o tempo assistido. **O ótimo não é automatizar o máximo possível** — é 0,80, e o gráfico de sensibilidade no protótipo mostra a curva achatando.

---

## Síntese para decisão

| Pergunta | Resposta | Confiança |
|---|---|---|
| Onde o fluxo trava? | Não identificável nos dados fornecidos (p > 0,45 em todas as dimensões) | Alta — testado |
| O que impacta satisfação? | Nenhuma variável medida (R² de teste negativo) | Alta — testado |
| Quanto desperdiçamos? | R$ 90.000/ano em triagem; R$ 63.472 recuperáveis | Média — volume é fato, tempo por tarefa é premissa |

**Recomendação de prioridade:**

1. **Implantar a triagem automática** (item 2) — é o único ganho quantificável e comprovado, com caminho de implantação em fases
2. **Instrumentar a operação** — sem timestamps e CSAT confiáveis, as perguntas A e B continuarão sem resposta no próximo trimestre
3. **Revisar a taxonomia de filas** — a ambiguidade entre categorias limita tanto o humano quanto a máquina
