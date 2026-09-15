# Laudo de Auditoria — Dataset 1 (`customer_support_tickets.csv`)

**Veredito: 8 dos 9 testes condenam o arquivo. O dataset foi gerado integralmente por biblioteca de dados falsos (Faker). Nenhum KPI operacional pode ser derivado dele.**

Reprodução: `python solution/scripts/01_auditoria_integridade.py`
Saída bruta: `solution/outputs/auditoria_resultados.json`

---

## Por que esta auditoria existe

O brief pede três respostas com base neste arquivo: onde o fluxo trava, o que impacta satisfação, e quanto se desperdiça. As três são perguntas causais. Antes de respondê-las, a pergunta anterior precisa ser feita: **estes dados suportam uma afirmação causal?**

A resposta é não. E isso não é um detalhe metodológico — muda o que é honesto entregar.

---

## As nove provas

### 1. Placeholders de template não substituídos — **100% das descrições**

Todas as 8.469 descrições de ticket contêm marcadores de template literalmente não preenchidos:

> `"I'm having an issue with the {product_purchased}. Please assist."`

Após normalizar os placeholders, restam 8.077 variações — geradas por combinação de um punhado de frases-molde. O brief descreve este campo como *"texto completo da reclamação do cliente"*. Não é texto de cliente; é um molde com a variável exposta.

### 2. Janela temporal de 27 horas para "um ano de operação"

| | |
|---|---|
| Primeiro timestamp | 2023-05-31 21:53:30 |
| Último timestamp | 2023-06-02 00:55:33 |
| Amplitude total | **27,03 horas** |
| Tickets | 8.469 |

Uma operação real espalha tickets por meses. Estes foram todos carimbados no momento em que o arquivo foi gerado.

### 3. Metade dos tickets foi resolvida *antes* de ser respondida

Comparando `First Response Time` com `Time to Resolution` nos 2.769 pares válidos:

- **1.365 tickets (49,3%)** têm resolução **anterior** à primeira resposta
- Delta médio: **−0,06 horas** (essencialmente zero)

Isso é fisicamente impossível. É a assinatura de dois timestamps sorteados de forma independente dentro da mesma janela — metade cai de cada lado, como esperado de moeda honesta.

### 4. Satisfação uniformemente distribuída

| Nota | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| Tickets | 553 | 549 | 580 | 543 | 544 |

Qui-quadrado contra a uniforme: **χ²=1,67 · p=0,797**. Ou seja, indistinguível de um sorteio.

CSAT real nunca é uniforme — é uma curva em J, com acúmulo nos extremos (quem se dá ao trabalho de avaliar está muito satisfeito ou muito irritado). Uma operação com satisfação perfeitamente plana entre 1 e 5 não existe.

### 5. Ausência total de sinal

| Teste | Estatística | p | Leitura |
|---|---|---|---|
| Pearson: CSAT × tempo de resolução | r = 0,0199 | 0,296 | sem relação |
| ANOVA: CSAT por canal | F = 1,281 | 0,279 | canais idênticos |
| χ²: canal × prioridade | 15,48 | 0,079 | independentes |
| χ²: tipo × prioridade | 10,63 | 0,561 | independentes |
| χ²: canal × tipo | 11,85 | 0,458 | independentes |

CSAT médio por canal: Chat 3,08 · Email 2,96 · Phone 2,95 · Social 2,97. **Amplitude de 0,13 ponto** — todos convergindo para 3,0, a média de um sorteio uniforme em 1–5.

A pergunta do brief *"o que impacta satisfação? é o tempo de resposta? o canal?"* tem uma única resposta verdadeira neste arquivo: **nada impacta nada, porque tudo foi sorteado de forma independente.**

### 6. Assinatura do Faker nos e-mails — **100%**

| Domínio | Tickets |
|---|---|
| example.com | 2.904 |
| example.org | 2.796 |
| example.net | 2.769 |

Os três são domínios **reservados pela RFC 2606** exclusivamente para documentação e teste — não podem ser registrados por ninguém. São também o conjunto padrão da biblioteca Python **Faker**. Nenhum cliente real tem e-mail nesses domínios.

Esta é a prova que fecha o caso: não é "dado de baixa qualidade", é **dado fabricado por geração automática**.

### 7. O campo de resolução é salada de palavras

Amostras reais do campo que o brief chama de *"texto da resolução aplicada pelo agente"*:

> *"Case maybe show recently my computer follow."*
> *"Try capital clearly never color toward story."*
> *"West decision evidence bit."*

Vocabulário: 971 palavras únicas em 2.769 resoluções, lideradas por *evidence* (30), *piece* (29), *billion* (25), *leg* (25), *camera* (24) — a lista de palavras aleatórias do Faker.

Contagem de termos que **deveriam** dominar um campo de resolução de suporte:

| Termo | Ocorrências |
|---|---|
| `refund` | **0** |
| `replace` | **0** |
| `ticket` | **0** |
| `resolved` | **0** |
| `reset` | **0** |

Um campo de resolução de suporte em que a palavra "resolvido" nunca aparece.

### 8. Todas as categóricas são uniformes — nem o mix de volume sobrevive

Qui-quadrado contra a uniforme, com correção de Bonferroni (α = 0,0083 para 6 testes):

| Coluna | k | χ² | p | Uniforme? |
|---|---|---|---|---|
| Ticket Channel | 4 | 1,35 | 0,718 | sim |
| Ticket Priority | 4 | 4,59 | 0,205 | sim |
| Ticket Type | 5 | 7,43 | 0,115 | sim |
| Ticket Status | 3 | 2,23 | 0,328 | sim |
| Product Purchased | 42 | 40,82 | 0,478 | sim |
| Ticket Subject | 16 | 27,86 | 0,023 | sim |

**6 de 6 uniformes.** Este é o teste mais consequente do laudo, e foi o que me obrigou a descartar minha própria hipótese inicial.

Eu havia assumido que, mesmo com as métricas corrompidas, a *composição* do volume sobreviveria — que ainda daria para dizer "tal canal concentra tanto do volume". Não dá. Suporte real obedece a Pareto: poucos tipos de problema geram a maioria dos chamados. Aqui, os 42 produtos aparecem com frequência estatisticamente idêntica, e os 4 canais também.

**Consequência direta:** os "67,3% de tickets nunca fechados" **não são um backlog**. `Ticket Status` é uniforme entre três valores — é 1/3 em cada, por sorteio. Qualquer leitura de "temos uma crise de backlog" seria invenção.

### 9. Completude — e a divergência com o brief

| | |
|---|---|
| Registros no arquivo | **8.469** |
| Registros prometidos no brief | ~30.000 |
| Divergência | **−21.531** |

`Resolution`, `Time to Resolution` e `Customer Satisfaction Rating` têm exatamente **5.700 nulos cada** — os três só existem para tickets `Closed`, o que é coerente (e é o único comportamento estruturalmente plausível do arquivo inteiro).

---

## Divergências entre o brief e os arquivos entregues

| Afirmação do brief | Realidade | Impacto |
|---|---|---|
| "~30.000 registros" (Dataset 1) | 8.469 | Volume 3,5× menor |
| "Texto real de descrição e resolução" | Template com placeholder + Faker | Invalida qualquer NLP sobre o DS1 |
| "~48.000 registros" (Dataset 2) | 47.837 | Confere |

---

## O que isto significa para a entrega

Três consequências, em ordem de importância:

**1. As três perguntas do diagnóstico não têm resposta verdadeira neste arquivo.** Gargalos por canal, drivers de satisfação e horas desperdiçadas são todos derivados de campos sorteados. Qualquer número apresentado seria ficção com aparência de análise.

**2. Este é exatamente o erro que uma IA sem supervisão comete.** Colar o brief em um LLM produz, com alta confiança e formatação impecável, afirmações como *"tickets críticos via Social Media levam 2,3× mais tempo — priorize esse canal"*. O número existe; ele simplesmente não significa nada. Aqui, a contribuição humana não foi corrigir a sintaxe do que a IA escreveu — foi **duvidar da premissa que ninguém mandou duvidar**.

**3. O Dataset 2 é real e assume a carga quantitativa.** 47.837 tickets corporativos autênticos, 8 categorias, zero placeholders, zero duplicatas, desbalanceamento de 7,74× (Hardware 13.617 → Administrative rights 1.760). É sobre ele que o classificador e o cálculo de ROI serão construídos — com acurácia medida de verdade.

---

## Nota sobre o dataset descartado

Descartar o Dataset 1 **não** significa ignorar a primeira parte do brief. A entrega para o Diretor de Operações continua respondendo "onde travamos" e "quanto desperdiçamos" — mas pelo caminho honesto, detalhado nos documentos seguintes: um **instrumento de diagnóstico** parametrizável, alimentado pelos dados reais disponíveis, acompanhado da especificação exata do que a operação precisa passar a registrar para que essas perguntas tenham resposta no mês que vem.

Entregar o termômetro calibrado vale mais do que inventar a temperatura.
