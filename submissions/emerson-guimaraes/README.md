# Submissão — Emerson Guimarães — Challenge 002 (Redesign de Suporte)

## Sobre mim

- **Nome:** Emerson Guimarães
- **LinkedIn:** _(preencher)_
- **Challenge escolhido:** 002 — Redesign de Suporte

---

## Executive Summary

Auditei os dois datasets antes de analisar qualquer coisa, e descobri que o **Dataset 1 foi inteiramente gerado por biblioteca de dados falsos** — 8 de 9 testes estatísticos o condenam, incluindo 100% dos e-mails em domínios reservados da RFC 2606 e um campo de "resolução do agente" que é salada de palavras. Isso significa que duas das três perguntas do diagnóstico (gargalos e drivers de satisfação) **não têm resposta verdadeira** nos dados fornecidos, e eu reporto isso com os testes que provam, em vez de inventar números. A terceira pergunta tem resposta e vale dinheiro: **R$ 90.000/ano gastos em triagem manual**. Construí então um classificador sobre os 47.837 tickets **reais** do Dataset 2 que atinge **86,4% de acurácia** e, calibrado a um limiar de confiança de 0,80, **roteia sozinho 60,11% dos tickets com 97,48% de acerto** — recuperando **R$ 50.009/ano (0,57 FTE)**, já descontado o retrabalho dos próprios erros. A recomendação principal é implantar a triagem automática em fases, mantendo decisões de privilégio e de gasto obrigatoriamente com humanos.

---

## Solução

### Abordagem

Ataquei o problema em quatro movimentos, nesta ordem deliberada:

**1. Auditar antes de analisar.** O brief pede três respostas causais. A pergunta anterior a essas três é se os dados suportam qualquer afirmação causal. Rodei nove testes de integridade antes de olhar para qualquer KPI.

**2. Reportar o que os dados sustentam, com o teste junto.** Onde a diferença entre grupos não é estatisticamente significativa, isso está dito na mesma tabela. Ranking sem teste é ranking de ruído.

**3. Pôr o peso quantitativo onde o dado é real.** O Dataset 2 é autêntico — 47.837 tickets corporativos, 8 categorias, zero placeholders. É sobre ele que o classificador foi treinado e medido.

**4. Cruzar os dois datasets no ROI.** A cobertura **medida** do classificador (Dataset 2) aplicada ao volume de tickets (Dataset 1) produz o número de horas e reais. A taxa de automação não foi arbitrada em nenhum momento.

### Resultados / Findings

**Relatório consolidado em PDF** (capa, sumário, arquitetura e fluxo de decisão em diagrama):
[`solution/relatorio/Relatorio_Redesign_Suporte_Emerson_Guimaraes.pdf`](solution/relatorio/Relatorio_Redesign_Suporte_Emerson_Guimaraes.pdf)
— reune os três documentos abaixo em 20 páginas. Regenerável com
`python solution/relatorio/build_pdf.py` (usa Edge/Chrome headless, sem dependências pesadas).

**Documentos-fonte, na ordem de leitura:**

| # | Documento | Conteúdo |
|---|---|---|
| 1 | [Diagnóstico Operacional](solution/relatorio/01_diagnostico_operacional.md) | Item 1 do brief — as três perguntas, com testes de significância |
| 2 | [Proposta de Automação](solution/relatorio/02_proposta_automacao.md) | Item 2 — o que automatizar, o que **não**, e o fluxo desenhado |
| 3 | [Anexo: Auditoria dos Dados](solution/relatorio/03_anexo_auditoria_dados.md) | As 9 provas de que o Dataset 1 é sintético |
| 4 | [Diário de Bordo](docs/DIARIO_DE_BORDO.md) | Decisões, percalços, gaps e erros de percurso |

**Principais números:**

| Achado | Evidência |
|---|---|
| Dataset 1 é gerado artificialmente | 8/9 testes; 100% dos e-mails em `example.com/.org/.net` (RFC 2606) |
| Não há gargalo identificável | ANOVA por canal p=0,451 · prioridade p=0,569 · tipo p=0,911 |
| Nada explica a satisfação | R² de teste = **−0,0525** (pior que chutar a média) |
| Classificador funciona | **86,40%** de acurácia vs 28,47% do baseline (+57,93 p.p.), F1 macro 0,865 |
| Automação viável e medida | limiar 0,80 → **60,11%** de cobertura a **97,48%** de acurácia |
| Ganho financeiro | **R$ 50.009/ano** líquidos (0,57 FTE) em 30 mil tickets |

### Recomendações

Por ordem de prioridade:

1. **Implantar triagem automática em três fases** (sombra → piloto → expansão). É o único ganho quantificável e comprovado. Critério de parada explícito: se a acurácia real na fase de sombra ficar abaixo de 90%, não avança.
2. **Manter `Administrative rights` e `Purchase` sempre com humano**, qualquer confiança. Precisão de 0,733 em concessão de privilégio é risco de segurança, não ineficiência.
3. **Instrumentar a operação.** Sem timestamps de abertura/resposta/fechamento, agente, reaberturas e transferências, as perguntas de gargalo e satisfação continuarão sem resposta no próximo trimestre.
4. **Revisar a taxonomia de filas.** As confusões Hardware ↔ Miscellaneous ↔ HR Support são ambiguidade real de rótulo, não falha de modelo. Nenhum algoritmo conserta taxonomia inconsistente.
5. **Não construir resposta automática ao cliente agora.** Não existe base de resoluções reais para aprender. Revisitar após 3–6 meses de histórico verdadeiro.

### Limitações

- O classificador foi treinado em tickets de **TI corporativo em inglês**, já lematizados e sem stopwords. Aplicado a chamados em português ou de outro domínio, a acurácia cai — a fase de sombra existe para medir isso.
- A **taxonomia de 8 categorias veio do dataset**, não de uma operação real. Se as filas forem outras, é preciso retreinar com os rótulos certos.
- Os **rótulos de treino têm ruído**; os 86,4% provavelmente subestimam o desempenho com taxonomia limpa.
- O **ROI depende de premissas de tempo por tarefa** (4 min de triagem, 12 min de retrabalho). São benchmarks, não medições da operação. Todas editáveis no protótipo.
- **Não testei transformers/LLM** contra o baseline TF-IDF. Com o texto já pré-processado e lematizado, o ganho esperado seria pequeno e o custo por chamada, permanente — mas é uma verificação que ficou em aberto.

---

## Protótipo funcional

**Mesa de Triagem** — aplicação Streamlit rodando sobre o modelo real.

```bash
cd submissions/emerson-guimaraes/solution
pip install -r requirements.txt
python scripts/03_classificador.py     # treina e salva o modelo (~1 min)
streamlit run app/app.py
```

Três telas:

- **Triagem** — cola o texto de um ticket e recebe categoria, confiança, decisão de roteamento e **os termos que pesaram na decisão**. Os exemplos são tickets reais sorteados do dataset, com o rótulo verdadeiro à vista — não exemplos escritos para a demo.
- **Lote** — roda sobre uma amostra aleatória real e mostra cobertura, acurácia no automatizado e distribuição por fila.
- **Calculadora de ROI** — o Diretor ajusta cada premissa e vê o número recalcular, incluindo a curva de sensibilidade ao limiar.

**Pré-requisito:** os CSVs do Kaggle em `datasets/raw/` na raiz do repositório. Ver [setup](docs/SETUP.md).

---

## Process Log — Como usei IA

### Ferramentas usadas

| Ferramenta | Para que usei |
|---|---|
| **Claude Code (Opus 5)** | Par de trabalho principal: auditoria estatística, construção dos scripts, treino do classificador e do protótipo Streamlit |
| **Kaggle API** | Obtenção reprodutível dos datasets |
| **scikit-learn / scipy** | Testes de hipótese, modelagem e métricas |

### Workflow

1. **Li o brief e escolhi o desafio** com um critério explícito: o 002 é o que tem maior superfície de julgamento humano. Desafios puramente analíticos são mais fáceis de a IA replicar sozinha — e o critério declarado do G4 é superar o baseline de IA.
2. **Auditei os dados antes de qualquer análise.** Esta foi a decisão que definiu a submissão inteira. A hipótese inicial era suspeita moderada; virou certeza a cada teste.
3. **Descartei minha própria hipótese intermediária** quando ela não sobreviveu ao teste (detalhes abaixo).
4. **Entreguei o diagnóstico mesmo assim**, com os testes de significância ao lado de cada número, em vez de omitir ou inventar.
5. **Treinei e calibrei o classificador** no dataset real, focando na curva cobertura × acurácia em vez da acurácia bruta.
6. **Liguei os dois datasets no ROI** — cobertura medida × volume, com desconto de retrabalho.
7. **Construí e testei o protótipo**, corrigindo o que quebrou (abaixo).

### Onde a IA errou e como corrigi

Três correções concretas, todas registradas no [Diário de Bordo](docs/DIARIO_DE_BORDO.md) e no histórico de commits:

**1. A IA aceitou os dados como válidos por padrão.** O comportamento inicial — meu e de qualquer assistente — é partir para a análise que o brief pediu. Ninguém mandou duvidar dos dados. A correção não foi de sintaxe; foi de **premissa**, e ela mudou a entrega inteira.

**2. Ceticismo pela metade produziu um erro pior que ceticismo nenhum.** Depois de detectar que as métricas eram ruído, concluí que os campos estruturais sobreviveriam, e afirmei que os "67,3% de tickets nunca fechados" eram um backlog real. **Estava errado.** Ao testar uniformidade de *todas* as categóricas com correção de Bonferroni, deu 6 de 6 uniformes — os 67,3% são 1/3 por sorteio de status. Retratei no anexo e no diário. O aprendizado: parar cedo demais na verificação é perigoso porque o resultado *parece* rigoroso.

**3. Os exemplos do protótipo estavam mal rotulados — por mim.** Escrevi quatro exemplos de ticket à mão para a demo. Ao testar, o exemplo rotulado "Acesso" foi classificado como Storage com 99,9% de confiança. O modelo estava certo: meu texto mencionava *shared folder*. Troquei todos por **tickets reais sorteados do dataset, com o rótulo verdadeiro visível**. Exemplo escrito à mão contém as palavras que o autor acha que definem a classe, o que infla artificialmente a confiança — exatamente o "cherry-picking" que o critério de qualidade condena.

### O que eu adicionei que a IA sozinha não faria

**Duvidar do enunciado.** O brief afirma "texto real de descrição e resolução" e "~30.000 registros". Ambas são falsas — o texto é template com placeholder exposto e são 8.469 registros. Uma IA respondendo ao brief trata o enunciado como verdade; verificar o enunciado contra o arquivo é decisão de quem já levou prejuízo confiando em documentação de sistema.

**Saber que R² negativo é a entrega, não o fracasso.** O impulso natural ao ver um modelo que não funciona é trocar de modelo até algum dar número apresentável. Reconhecer que o R² negativo **é a resposta à pergunta do Diretor** — e que insistir produziria overfitting disfarçado de insight — é julgamento, não cálculo.

**Definir a fronteira da automação por consequência, não por métrica.** `Purchase` tem precisão de 0,946 — pela métrica, é a segunda melhor classe e deveria ser automatizada. Mantive em revisão humana porque são decisões de gasto. Inversamente, `Administrative rights` sai por métrica ruim *e* por risco de segurança. Otimizar acurácia média ignora que o custo do erro é assimétrico — isso vem de operar processo, não de ler dados.

**Descontar o retrabalho do próprio ganho.** O cálculo de ROI ingênuo multiplica volume por tempo economizado. O honesto subtrai as horas que os erros do modelo vão custar — e é isso que revela que o cenário agressivo só rende R$ 5 mil a mais que o recomendado. Quem já viu automação mal calibrada gerar mais trabalho do que resolve faz essa conta por reflexo.

### Iterações

Aproximadamente 20 ciclos de trabalho, com 4 commits temáticos. A auditoria sozinha passou por três rodadas: suspeita inicial → 6 testes → 9 testes com a assinatura do Faker → retratação da hipótese estrutural.

---

## Evidências

- [x] **Git history** — 4+ commits temáticos com a evolução do raciocínio nas mensagens, incluindo o commit que registra a retratação
- [x] **Narrativa escrita** — [Diário de Bordo](docs/DIARIO_DE_BORDO.md), escrito durante o trabalho e não reconstruído no fim
- [x] **Código reproduzível** — todos os números desta submissão saem de `solution/scripts/`, executáveis de ponta a ponta
- [x] **Saídas brutas versionadas** — JSONs em `solution/outputs/` para conferência independente
- [ ] Screenshots das conversas com IA
- [ ] Screen recording do workflow

---

## Estrutura da entrega

```
submissions/emerson-guimaraes/
├── README.md                    ← este arquivo
├── solution/
│   ├── scripts/
│   │   ├── 01_auditoria_integridade.py     9 testes de integridade
│   │   ├── 02_diagnostico_operacional.py   item 1 do brief
│   │   └── 03_classificador.py             treino + curva de cobertura
│   ├── app/app.py                          protótipo Streamlit
│   ├── outputs/                            JSONs + modelo treinado
│   ├── relatorio/
│   │   ├── Relatorio_Redesign_Suporte_Emerson_Guimaraes.pdf  ← consolidado
│   │   ├── build_pdf.py
│   │   ├── 01_diagnostico_operacional.md
│   │   ├── 02_proposta_automacao.md
│   │   └── 03_anexo_auditoria_dados.md
│   └── requirements.txt
└── docs/
    ├── DIARIO_DE_BORDO.md
    └── SETUP.md
```

---

_Submissão enviada em: setembro de 2026_
