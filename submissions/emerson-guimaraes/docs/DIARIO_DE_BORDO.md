# Diário de Bordo — Challenge 002

Registro corrido das decisões, becos sem saída e correções de rota. Escrito **durante** o trabalho, não reconstruído no fim — é a matéria-prima do process log.

**Status atual:** Fase 1 concluída · Fases 2 a 5 pendentes

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

O resultado foi muito além da suspeita. **8 dos 9 testes condenam o arquivo.** Detalhamento completo em [`solution/relatorio/01_laudo_auditoria.md`](../solution/relatorio/01_laudo_auditoria.md).

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

---

## Gaps e riscos em aberto

| # | Item | Natureza | Status |
|---|---|---|---|
| 1 | Brief promete ~30.000 registros no DS1; existem 8.469 | Divergência factual do enunciado | Documentado no laudo |
| 2 | Brief promete "texto real"; é template + Faker | Divergência factual do enunciado | Documentado no laudo |
| 3 | `submissions/` no `.gitignore` | Falha silenciosa de submissão | Contornado com `git add -f` |
| 4 | DS2 tem rótulos ruidosos (ex.: pedido de acesso rotulado como "HR Support") | Teto de acurácia do classificador | **A quantificar na Fase 3** |
| 5 | DS2 desbalanceado 7,74× | Risco de viés do modelo para classe majoritária | **A tratar na Fase 3** |
| 6 | DS2 vem pré-processado (stopwords removidas, lematizado, PII mascarada) | Impede usar o texto cru; limita ganho de LLM sobre TF-IDF | **A avaliar na Fase 3** |
| 7 | Sem dados temporais reais, não há cálculo honesto de horas desperdiçadas | Impacta o pedido de ROI do Diretor | **Mitigação: modelo paramétrico na Fase 4** |

### Risco principal da estratégia

Denunciar o dataset é a maior aposta desta submissão. Se o avaliador esperar o relatório convencional de gargalos, a entrega pode ser lida como fuga do escopo.

**Mitigação adotada:** não parar na denúncia. Entregar as três respostas que o Diretor pediu, pelo caminho honesto — instrumento parametrizável em vez de números inventados — e deixar explícito, com números reproduzíveis, por que este é o único caminho defensável. O critério de avaliação declarado no README (*"a análise distingue correlação de causalidade"*) sustenta a escolha.

---

## Próximas etapas

- **Fase 2** — Diagnóstico sobre o que é real: análise do DS2 e estrutura de custo parametrizada
- **Fase 3** — Classificador sobre os 47.837 tickets reais, com acurácia medida e matriz de confusão por classe
- **Fase 4** — Desenho do fluxo: o que automatizar, o que não automatizar, e onde fica a fronteira
- **Fase 5** — Protótipo funcional + finalização do process log
