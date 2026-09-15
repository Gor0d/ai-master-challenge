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

### Etapa 11 — Revisão crítica externa e correção de cinco pontos concretos

Pedi uma avaliação honesta do case contra os critérios de qualidade do brief, e recebi de volta uma revisão com objeções específicas e verificáveis — o tipo de crítica que vale mais do que elogio. Cinco delas geraram mudança real:

1. **Número real vs. projetado misturados sem aviso.** O relatório citava "R$ 50.009/ano" e "R$ 90.000/ano" como se fossem sobre o mesmo volume, quando são a projeção para 30 mil tickets/ano — sobre os 8.469 tickets efetivamente entregues, o número é R$ 14.118 e R$ 25.407. Corrigido com uma tabela explícita que separa as duas escalas antes de qualquer outro número aparecer.

2. **Premissa de custo/hora apresentada como fato.** R$ 45/h é benchmark, não a folha real de ninguém, e o ROI escala linearmente com ela. Adicionei ao script (`sensibilidade_custo_hora()`) o cálculo em R$ 30/h e R$ 60/h — R$ 33.339 e R$ 66.679/ano — e uma tabela no relatório, não só uma frase.

3. **Faltava custo de implantação e payback.** Adicionei `custo_implantacao_e_payback()` ao script: fase de sombra a custo zero (é inferência em lote, sem integração), deploy estimado em R$ 12.000, manutenção de R$ 600/mês, payback de **3,4 meses**. Marcado explicitamente como estimativa de esforço, não orçamento medido.

4. **Detecção de duplicatas descartada só no diário, não na proposta.** O brief cita como exemplo de automação; quem lesse só o PDF podia achar que eu tinha ignorado o item. Movida a justificativa (zero duplicatas exatas no DS2, mas sem ID de cliente ou timestamp para detectar reaberturas — que é o caso que importa) para a seção 2 do relatório de automação, com o que seria necessário para resolver no futuro.

5. **Regra de negócio escondida no código, no protótipo.** A aba de lote mostrava "HUMANO" sem dizer se foi por confiança baixa ou por categoria sensível. Adicionei coluna `motivo` na tabela e testei a consistência (`humano = sensível + confiança_baixa`) sobre uma amostra real de 400 tickets antes de aceitar.

**O que não mudei:** a estrutura da resposta ao item 1 (onde o fluxo trava / o que impacta satisfação) continua sendo "não há resposta verdadeira, e aqui está o teste que prova". A revisão concordou que isso fortalece a recomendação por fases em vez de invalidá-la — o ponto de atenção era de transparência de premissa, não de metodologia.

**Pendências que a revisão confirmou:** screenshots/Loom do workflow (capturado e organizado na Etapa 12) e testar embeddings/zero-shot contra o benchmark de 92% que o brief cita (resolvido na Etapa 13 — TF-IDF venceu ambos, com explicação).

---

### Etapa 12 — Screenshots capturados, e um vazamento de token pego antes da publicação

O usuário capturou 15 screenshots da sessão real (clone → escolha do desafio → auditoria → retratação → classificador → protótipo → checklist final) e pediu para organizá-los no process log.

**Antes de copiar qualquer coisa, inspecionei as 15 uma a uma.** Duas delas (4 e 5) expunham o **token da API do Kaggle em texto puro** — a mesma mensagem que havia sido colada na sessão para autenticar. As outras 13 estavam limpas.

**Correção:** redigi (cobri com retângulo preto) apenas a região do token nas duas imagens, preservando o resto do conteúdo — que é justamente onde aparecem as primeiras 5 provas do Faker, material valioso do process log. Conferi visualmente as duas redações antes de aceitar.

**O que não fiz:** não afirmei no README que o token "já foi revogado" — eu não tinha como verificar isso no momento. Errei essa frase duas vezes tentando adivinhar o tempo verbal certo antes de perceber que o correto era não afirmar um fato que não podia confirmar, e sim recomendar a ação ao usuário. A nota ficou como recomendação até o usuário confirmar que já havia expirado o token — só então a nota do process log foi atualizada para declarar o fato.

Arquivos renomeados de `1.png`...`15.png` para nomes descritivos (`05-descoberta-dataset1-sintetico-5-provas.png` etc.) e indexados em `process-log/README.md` com uma linha por captura.

---

### Etapa 13 — Fechando o gap de embeddings/zero-shot, e um resultado que surpreendeu

O revisor apontou que a entrega ficava abaixo do benchmark de "92% com embeddings + zero-shot" que o próprio brief cita como exemplo. Antes de implementar, checei o ambiente: CPU only, sem GPU, sem `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` configuradas. Apresentei 4 opções ao usuário (embeddings locais, zero-shot local, zero-shot via API paga, ou não mexer) — escolhida a combinação embeddings locais + zero-shot local numa amostra de validação, mantendo tudo reproduzível sem custo de API.

**Percalço 1 — bug de compatibilidade do pandas 3.x.** `groupby("rotulo").apply(lambda g: g.sample(...))` quebrou com `KeyError: 'rotulo'`. A causa: pandas 3.x passou a excluir por padrão a própria coluna de agrupamento do que é entregue à função (`include_groups`), então a amostra resultante simplesmente não tinha mais essa coluna. Troquei por concatenação manual (`pd.concat([g.sample(...) for _, g in df.groupby(...)])`), que não sofre desse efeito colateral.

**Percalço 2 — tempo de execução subestimado.** O zero-shot local roda 8 hipóteses de entailment por ticket em CPU (~1,7s/ticket) — rodar isso passou dos 10 minutos do timeout padrão da ferramenta duas vezes (uma antes do bug, outra depois de corrigi-lo) e caiu para execução em background nas duas. Nada de errado, só é um processo genuinamente longo em CPU sem GPU.

**O resultado surpreendeu, e é o tipo de achado que só aparece testando de verdade:**

| Método | Acurácia | F1 macro |
|---|---|---|
| TF-IDF + LogReg (o que já estava em produção na submissão) | 86,40% | 0,8653 |
| Embeddings (MiniLM) + LogReg | 78,07% | 0,7777 |
| Zero-shot (BART-MNLI, sem treino) | **23,75%** | 0,1325 |

O zero-shot ficou **abaixo do baseline ingênuo** de 28,47% (sempre a classe majoritária). Investiguei a causa em vez de só reportar o número: o Dataset 2 vem pré-lematizado e sem stopwords pelo autor original (`"work experience user work experience user hi..."`), formato que favorece contagem de termos (TF-IDF) e é veneno para um modelo de entailment que precisa de frases fluentes para julgar "isto implica aquilo". Confirmei isso lendo amostras reais do texto antes de escrever a explicação — não assumi a causa, verifiquei.

**Por que isto fecha o gap melhor do que simplesmente "ter testado embeddings":** a resposta ao brief não é "usamos embeddings e deu X%" — é "testamos as três abordagens que o brief sugere, escolhemos a que os dados comprovaram ser melhor, e sabemos explicar por quê". É exatamente o oposto de aplicar a técnica mais nova por reflexo.

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

### Etapa 10 — Auditoria de qualidade e PDF consolidado

Pedido do usuário: auditar o que foi entregue e converter os markdowns em
um PDF apresentável, com diagramas de arquitetura.

**Auditoria de qualidade:** pipeline reexecutado do zero (outputs apagados
e regerados) — números idênticos. Links internos, cobertura de
`requirements.txt` e consistência numérica entre os 4 documentos
conferidos por script, não de memória. Sinais de formatação (moeda,
R², χ², sinal de menos tipográfico) auditados por regex — nenhuma
inconsistência real (uma falsa suspeita de mojibake era artefato do
terminal, não do arquivo).

**PDF consolidado:** WeasyPrint foi descartado por depender de
bibliotecas GTK nativas ausentes no Windows. Caminho adotado: HTML com
CSS de impressão + diagramas SVG inline, renderizado via **Edge headless**
(`msedge --headless=new --print-to-pdf`), que já vem instalado no Windows
e não exige nenhuma dependência nova pesada.

**Bug capturado na primeira renderização:** o diagrama de arquitetura
apareceu como texto literal `{DIAGRAMA_ARQUITETURA}` na página — a função
que monta o sumário executivo usava string tripla comum, não f-string.
Corrigido com placeholder + `.replace()` explícito, e a segunda
renderização foi inspecionada página a página (20 páginas, via PyMuPDF)
antes de aceitar o resultado. Também corrigidos no mesmo ciclo: título da
capa ilegível (herdava cor escura do body) e zebra-striping da tabela
global vazando para dentro da capa azul.

## O que ficou de fora, e por quê

- **Transformer/LLM como classificador.** Com o texto já lematizado e sem stopwords, o ganho sobre TF-IDF tende a ser pequeno, e o custo por chamada é permanente. Deveria ser testado antes de uma decisão definitiva de arquitetura — não foi, e está declarado nas limitações.
- **Detecção de duplicatas.** O brief cita como possibilidade. O DS2 tem zero duplicatas exatas, e sem ID de cliente ou timestamp não dá para detectar reaberturas — que é o caso que realmente importa.
- **Respostas sugeridas.** Descartado por falta de base: o único campo de resolução disponível é texto gerado por Faker.

## Evidência que depende do candidato

Screenshots e screen recording do workflow ainda não foram capturados. O git history, o código reproduzível e este diário cobrem a narrativa, mas o guia de submissão valoriza evidência visual — vale acrescentar antes de abrir o PR.
