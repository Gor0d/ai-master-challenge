# Diário de Bordo — Challenge 002

Registro corrido das decisões, becos sem saída e correções de rota. Escrito **durante** o trabalho, não reconstruído no fim — é a matéria-prima do process log.

**Status atual:** entrega completa — itens 1 a 4 do brief atendidos

---

## Linha do tempo

### Etapa 0 — Leitura do case e escolha do desafio

Quatro desafios disponíveis. Escolhido o **002 (Redesign de Suporte)** por ser o único que combina as três competências ao mesmo tempo — diagnóstico analítico, desenho de processo e construção de software — e por ser o mais próximo da rotina real de gestão de operação.

**Decisão registrada:** preferir o desafio com maior superfície de julgamento humano, porque o critério declarado do G4 é superar o baseline de IA. Desafios puramente analíticos são mais fáceis de uma IA replicar sozinha.

### Etapa 1 — Percalço: acesso ao Kaggle

O Kaggle migrou o sistema de autenticação. A instrução clássica ("Create New Token" → baixa `kaggle.json`) **não gera mais arquivo nenhum** — agora emite um token único no formato `KGAT_...`, que vai em `~/.kaggle/access_token` ou na variável `KAGGLE_API_TOKEN`.

Perdemos alguns minutos procurando um arquivo que nunca existiria.

**Gap identificado:** toda documentação e tutorial disponível descreve o fluxo antigo. Vale registrar porque afeta reprodutibilidade — quem for rodar esta submissão vai passar pelo mesmo problema.

### Etapa 2 — Percalço: o `.gitignore` do repositório ignora as submissões

O `.gitignore` do repo do G4 contém:

```
# Submissions (if candidates fork)
submissions/
```

Como a regra do `CONTRIBUTING.md` proíbe modificar arquivos fora da pasta da submissão, não é permitido editar o `.gitignore` para corrigir isso.

**Efeito prático:** quem criar `submissions/seu-nome/`, rodar `git add .` e abrir o PR **submete um PR vazio** — o git ignora a pasta em silêncio, sem erro nem aviso. Confirmado empiricamente: `git status --short` não retorna nada após criar a estrutura.

**Solução adotada:** `git add -f submissions/emerson-guimaraes/`.

**Leitura:** pode ser armadilha proposital (parte do teste é saber trabalhar com git) ou descuido do repositório. Em qualquer dos casos, é um ponto de falha silenciosa que provavelmente elimina candidatos sem que eles entendam o motivo.

### Etapa 3 — A virada: o Dataset 1 é fabricado

Decisão metodológica tomada **antes** de qualquer análise: auditar a integridade dos dados antes de extrair qualquer conclusão. A hipótese inicial era suspeita moderada — o dataset tinha cara de sintético.

O resultado foi muito além da suspeita. **8 dos 9 testes condenam o arquivo.** Detalhamento completo em [`solution/relatorio/03_anexo_auditoria_dados.md`](../solution/relatorio/03_anexo_auditoria_dados.md).

As duas provas que encerram a discussão:

1. **100% dos e-mails** estão em `example.com` / `.org` / `.net` — domínios reservados pela RFC 2606, padrão-fábrica da biblioteca Faker
2. O campo "resolução do agente" é salada de palavras (*"West decision evidence bit."*), com **zero ocorrências** de `refund`, `replace`, `ticket`, `resolved` ou `reset`

**Consequência:** a pergunta central do brief — *"o que impacta satisfação?"* — não tem resposta verdadeira neste arquivo.

### Etapa 4 — Correção de rota: minha própria hipótese estava errada

Registro aberto de um erro meu, porque ele é instrutivo.

Depois de detectar que as métricas eram ruído, assumi que os **campos estruturais sobreviveriam** — que ainda daria para analisar a composição do volume ("canal X concentra Y% dos chamados") e que os 67,3% de tickets não fechados representavam um backlog real. Cheguei a comunicar isso como achado.

Ao testar uniformidade de **todas** as categóricas, a hipótese caiu: canal (p=0,72), prioridade (p=0,20), tipo (p=0,11), status (p=0,33) e produto (p=0,48) são **todos** uniformes. Suporte real obedece a Pareto; 42 produtos com frequência estatisticamente idêntica não acontece na natureza.

Os "67,3% nunca fechados" são 1/3 por status atribuído aleatoriamente. **Não é backlog. Retratado.**

**Aprendizado:** ceticismo aplicado pela metade produz um erro mais perigoso do que ceticismo nenhum, porque vem com aparência de rigor. Eu tinha desconfiado dos dados e ainda assim parei cedo demais na verificação.

### Etapa 5 — Correção de rota: a auditoria estava virando a entrega inteira

Percebi (com o alerta certo) que estava gastando energia demais na auditoria e transformando-a no eixo da submissão. O brief pede quatro entregas concretas, e a auditoria é **fundamento** delas, não substituta.

**Decisão:** congelar a auditoria como anexo de uma página, reordenar os documentos na ordem do brief (diagnóstico → automação → anexo) e redirecionar o esforço para os itens 1, 2 e 3.

**Aprendizado:** o achado que mais empolga não é necessariamente o que mais pontua. Rigor que não vira entrega é auto-indulgência.

### Etapa 6 — Diagnóstico entregue com os testes ao lado

Item 1 construído para responder exatamente as três perguntas, cada número acompanhado do seu teste de significância. O resultado mais forte veio da pergunta B: **R² de teste = −0,0525**, ou seja, o modelo prevê satisfação pior do que chutar a média — com R² de 0,44 no treino, a assinatura clássica de decorar ruído.

### Etapa 7 — Classificador e o cruzamento dos datasets

TF-IDF + LogisticRegression balanceada sobre os 47.837 tickets reais: **86,4%** de acurácia contra 28,47% do baseline.

A decisão de projeto que mais importou foi **não otimizar acurácia bruta, e sim a curva cobertura × acurácia**. Um modelo que acerta 86% é inútil para automação se não souber quando está inseguro. No limiar 0,80 ele cobre 60,11% dos tickets a 97,48% de acerto.

Esse número medido substituiu os percentuais de automação que eu havia chutado (50/70/85%) no cálculo de ROI — é o cruzamento entre os dois datasets que o critério de qualidade cobra: cobertura medida no DS2 aplicada ao volume do DS1.

Acrescentei o desconto de retrabalho ao ganho, e ele revelou algo que o cálculo ingênuo esconderia: **o cenário agressivo rende só R$ 5 mil a mais que o recomendado**, porque os erros adicionais consomem o ganho.

### Etapa 8 — Percalço: meus próprios exemplos do protótipo estavam errados

Escrevi quatro exemplos de ticket à mão para a demo. No teste, o exemplo que rotulei "Acesso" foi classificado como Storage com 99,9% de confiança.

O modelo estava certo — meu texto dizia *shared folder*. **O erro era meu.**

**Correção:** substituí todos por tickets reais sorteados do dataset, com o rótulo verdadeiro à vista. Exemplo escrito à mão contém as palavras que o autor acha que definem a classe, o que infla artificialmente a confiança — exatamente o cherry-picking que o critério de qualidade condena.

### Etapa 9 — Fechamento

Pipeline validado do zero: apagados os outputs e reexecutados os três scripts na ordem documentada. Números idênticos. O modelo de 8 MB ficou fora do versionamento (regenerável em ~1 min), com `.gitignore` local — dentro da minha pasta, sem violar a regra de não tocar em arquivos de terceiros.

---

## Gaps e riscos em aberto

| # | Item | Natureza | Status |
|---|---|---|---|
| 1 | Brief promete ~30.000 registros no DS1; existem 8.469 | Divergência factual do enunciado | Documentado no laudo |
| 2 | Brief promete "texto real"; é template + Faker | Divergência factual do enunciado | Documentado no laudo |
| 3 | `submissions/` no `.gitignore` | Falha silenciosa de submissão | Contornado com `git add -f` |
| 4 | DS2 tem rótulos ruidosos (ex.: pedido de acesso rotulado como "HR Support") | Teto de acurácia do classificador | Quantificado: confusões Hardware↔Misc↔HR somam ~5% por classe. Tratado como limite de taxonomia, não de modelo |
| 5 | DS2 desbalanceado 7,74× | Risco de viés para a classe majoritária | Resolvido com `class_weight="balanced"`; F1 macro 0,865 e nenhuma classe com recall < 70% |
| 6 | DS2 vem pré-processado (lematizado, sem stopwords, PII mascarada) | Limita o ganho de LLM sobre TF-IDF | **Em aberto** — não testei transformer contra o baseline. Ganho esperado pequeno, custo por chamada permanente |
| 7 | Sem dados temporais reais, não há cálculo honesto de horas desperdiçadas | Impacta o pedido de ROI | Mitigado: ROI por volume (fato) × tempo/tarefa (premissa explícita) × cobertura medida. Todas as premissas editáveis no protótipo |
| 8 | Modelo treinado em TI corporativo em inglês | Acurácia cai em outro domínio/idioma | **Em aberto** — mitigação proposta: fase de sombra antes de rotear |

### Risco principal da estratégia

Denunciar o dataset é a maior aposta desta submissão. Se o avaliador esperar o relatório convencional de gargalos, a entrega pode ser lida como fuga do escopo.

**Mitigação adotada:** não parar na denúncia. Entregar as três respostas que o Diretor pediu, pelo caminho honesto — instrumento parametrizável em vez de números inventados — e deixar explícito, com números reproduzíveis, por que este é o único caminho defensável. O critério de avaliação declarado no README (*"a análise distingue correlação de causalidade"*) sustenta a escolha.

---

## O que ficou de fora, e por quê

- **Transformer/LLM como classificador.** Com o texto já lematizado e sem stopwords, o ganho sobre TF-IDF tende a ser pequeno, e o custo por chamada é permanente. Deveria ser testado antes de uma decisão definitiva de arquitetura — não foi, e está declarado nas limitações.
- **Detecção de duplicatas.** O brief cita como possibilidade. O DS2 tem zero duplicatas exatas, e sem ID de cliente ou timestamp não dá para detectar reaberturas — que é o caso que realmente importa.
- **Respostas sugeridas.** Descartado por falta de base: o único campo de resolução disponível é texto gerado por Faker.

## Evidência que depende do candidato

Screenshots e screen recording do workflow ainda não foram capturados. O git history, o código reproduzível e este diário cobrem a narrativa, mas o guia de submissão valoriza evidência visual — vale acrescentar antes de abrir o PR.
