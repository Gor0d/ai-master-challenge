# Diário de Bordo — Challenge 002

Registro corrido das decisões, becos sem saída e correções de rota. Escrito **durante** o trabalho, não reconstruído no fim — é a matéria-prima do process log.

**Status atual:** entrega completa e pronta para o PR — itens 1 a 4 do brief atendidos, revisada e reexecutada do zero na Etapa 16, português do código corrigido na Etapa 17

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

### Etapa 5 — Correção de rota: eu parei a auditoria antes que ela virasse a entrega

A descoberta do Dataset 1 sintético era empolgante, e foi por isso que quase custou a submissão. A auditoria estava se tornando o eixo do trabalho, consumindo esforço que os quatro itens do brief precisavam.

**Interrompi a linha de trabalho com um diagnóstico direto:** estávamos gastando energia e token numa coisa que o desafio não pediu. Recoloquei os quatro entregáveis do brief na mesa, um por um, e exigi que o esforço voltasse para eles. A resposta foi *"você tem razão, e vou ajustar"* — a auditoria virou custo afundado, mantida como validação metodológica, e o investimento nela parou ali.

Registro em [`process-log/screenshots/08-redirecionamento-usuario-foco-no-brief.png`](../process-log/screenshots/08-redirecionamento-usuario-foco-no-brief.png).

**Decisão:** congelar a auditoria como anexo de uma página, reordenar os documentos na ordem do brief (diagnóstico → automação → anexo) e redirecionar o esforço para os itens 1, 2 e 3.

**Por que isto importa mais do que parece:** sem essa parada, a entrega seria um laudo forense impecável que não responde ao que o Diretor de Operações perguntou. A IA não tinha como fazer esse corte sozinha — ela estava produzindo bom trabalho, apenas na direção errada, e nada no resultado parcial sinalizava o desvio. Saber quando um trabalho de boa qualidade está sendo feito no lugar errado é julgamento de quem responde pela entrega, não de quem executa a tarefa.

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

### Etapa 14 — Ajustes finais, fork, e um artifact como resumo visual

Três correções pontuais pedidas pelo usuário, após aprovação dos testes de estresse do protótipo:

- **Emoji removido.** O único emoji do projeto (🎫, no `app.py`) foi trocado por um ícone Material Symbols (`:material/inbox:`) — vetorial, não emoji. Varredura em todo `.py`/`.md` confirmou que não havia mais nenhum.
- **Acentuação inconsistente corrigida.** Três linhas do `app.py` usavam acentos (`sensível`, `confiança`) quebrando a convenção sem-acento do resto do arquivo (deliberada, por segurança de encoding em terminal). Padronizado, e duas legendas sem ponto final foram alinhadas ao padrão das demais.
- **Bug do `groupby().apply()` confirmado como não existente no código entregue** — só havia aparecido num script descartável usado para gerar exemplos de teste para o usuário, já corrigido ali com a mesma técnica aplicada no script 04 (concatenação manual em vez de `apply`).

**Fork e push para o repositório oficial.** Criado `Gor0d/ai-master-challenge` via `gh repo fork`, e enviada a branch `submission/emerson-guimaraes` com o nome exato pedido pelo `CONTRIBUTING.md`. Isso não torna nada público para o G4 — só a abertura do PR de fato notifica o repositório oficial, e essa etapa ficou para confirmação explícita do usuário antes de executar.

**Artifact como resumo visual do processo.** A pedido do usuário, publicada uma página ("Case File 002") sintetizando os 9 marcos reais da sessão em formato de dossiê/timeline, com um gráfico comparando TF-IDF/embeddings/zero-shot. Deixei explícito na própria página que ela complementa, não substitui, o diário e os 15 screenshots — para não criar a impressão de que o resumo visual é o process log completo. O usuário compartilhou o link publicamente antes de eu referenciá-lo no README.

---

### Etapa 15 — Fechando os últimos três pontos: modelo commitado, comparação explícita, ROI ampliado

O usuário pediu nota para a entrega (8,5/10 na minha avaliação honesta) e depois "vamos fazer o serviço completo" para subir essa nota. Três ações, nesta ordem de execução:

**1. Modelo treinado passou a ser versionado.** Até aqui `modelo_triagem.joblib` ficava fora do git (regra local no `.gitignore` da pasta), exigindo rodar `03_classificador.py` antes do `streamlit run`. Isso é fricção desnecessária para um avaliador que só quer clicar e ver funcionando — troquei a prioridade (reprodutibilidade documentada continua disponível como opção) por "clona e roda direto".

**2. Comparação lado a lado com o que uma IA sem verificação responderia.** A seção B do diagnóstico ganhou uma tabela de três linhas contrastando afirmações plausíveis-mas-falsas que um LLM geraria colando o brief cru ("tickets críticos via telefone...") com o teste estatístico real que as invalida. Isso estava implícito antes; agora é impossível de não notar, e ataca de frente o critério #1 do brief ("usou ambos os datasets... o poder está no cruzamento" e "superar o baseline de IA").

**3. Tentativa honesta de melhorar a acurácia do classificador, e ROI ampliado com um resultado real.** Testei 4 variações do TF-IDF (n-gramas de caractere, LinearSVC, vocabulário maior) — nenhuma superou a configuração atual de forma significativa (86,20%–86,40%, contra 86,40% já em produção). Não troquei o modelo: mudança sem ganho real seria movimento por aparência, não por mérito. Documentei a diligência em uma linha na proposta.

Só depois veio a mudança que efetivamente melhorou o número: adicionei ao ROI o tempo poupado nos tickets que **não** são automatizados, porque chegam ao humano com categoria sugerida em vez de do zero (premissa nova, conservadora: 1,5 min/ticket, contra os 4 min de triagem manual completa). Isso não era um ajuste de maquiagem — é um ganho real que a proposta já descrevia (item 1.2, "sugestão de categoria para o agente") mas que o cálculo financeiro não capturava. Resultado: economia recomendada subiu de R$ 50.009 para **R$ 63.472/ano** (30k tickets), e o payback caiu de 3,4 para **2,6 meses**. Propaguei os números novos para os 4 lugares onde apareciam (diagnóstico, proposta, README, calculadora do app) e revalidei que reproduzem do zero.

**O que não fiz:** não reescrevi os números antigos nas entradas anteriores deste diário (Etapa 11, por exemplo, ainda cita "R$ 50.009" e "3,4 meses"). Esses valores eram corretos no momento em que foram escritos — reescrever o passado do diário para bater com o presente destruiria a única coisa que dá credibilidade a um diário: ele registra o que aconteceu, não o que é verdade agora.

---

### Etapa 16 — Revisão final antes do PR: um bug no protótipo e duas contradições numéricas

Última passada antes de abrir o pull request, num clone limpo e num ambiente
novo (Python 3.14, scikit-learn 1.9.1, sem os CSVs baixados) — de propósito,
para ver a submissão como o avaliador vai ver. Treze problemas encontrados,
três deles graves.

**1. O protótipo tinha um bug que quebrava a aba de dados reais.** O
`app.py` resolvia a raiz do repositório com `AQUI.parents[5]`; o índice
correto é `parents[4]`, que é o que os quatro scripts usam. O app procurava
os CSVs em `C:\Projetos` em vez de `C:\Projetos\CASE-G4` e nunca os
encontrava. Efeito prático: a aba "Lote (dados reais)" mostrava erro e os
exemplos de tickets reais desapareciam da aba de triagem — justamente as
duas coisas que respondem ao critério *"funciona com dados reais, não com 3
exemplos cherry-picked"*. O bug passou porque a validação anterior do
protótipo (Etapa 8) foi feita com o app rodando de um diretório em que o
caminho errado, por coincidência, ainda resolvia.

**2. O PDF contradizia a si mesmo no número principal.** O sumário
executivo do `build_pdf.py` é escrito à mão, e a Etapa 15 atualizou os
markdowns e o README para R$ 63.472 / 0,71 FTE sem atualizar o gerador. A
página 3 do PDF dizia R$ 50.009 / 0,57 FTE enquanto as páginas 5, 7, 8 e 13
do mesmo arquivo diziam 63.472. É a primeira página que o Diretor lê.
Corrigido, e o sumário ganhou as linhas de payback, sensibilidade e
TF-IDF-vs-embeddings que já existiam no README.

**3. Um número do relatório era desmentido pela própria evidência
versionada.** A proposta afirmava "~170s de encoding em CPU" para os
embeddings; o `embeddings_zeroshot_metricas.json`, no mesmo repositório,
registra 1.258,5s. Quem abrisse o JSON pegaria a inconsistência. Corrigido
para ~21 min, com o valor medido ao lado.

**Os outros dez** foram de consistência e de atrito para quem avalia: três
afirmações deste diário que a própria entrega já havia superado (o gap 6
dado como "em aberto" depois de fechado na Etapa 13; "transformer não foi
testado" na seção do que ficou de fora; "screenshots ainda não capturados"
com 15 deles no process log), a Etapa 10 fora de ordem cronológica,
contagem errada de commits e de páginas do PDF, o `.gitignore` local ainda
dizendo que o modelo não pertence ao PR depois de a Etapa 15 decidir
versioná-lo, `requirements.txt` obrigando 2,5 GB de torch em quem só quer
ver o app rodar (separado em `requirements-experimento.txt`), o tempo do
script 04 subestimado em 3× no SETUP, e um `.replace(",", ".")` aplicado
sobre a frase inteira que trocava as vírgulas da prosa por pontos na saída
JSON do payback.

**A validação que fecha a rodada:** com os CSVs baixados de novo, o pipeline
foi reexecutado do zero num ambiente diferente do original.
`auditoria_resultados.json` e `classificador_metricas.json` saíram **byte a
byte idênticos** aos commitados — 86,40% de acurácia, F1 macro 0,8653,
cobertura de 60,11% a 97,48%, mesma matriz de confusão. O único diff em
`diagnostico_operacional.json` foi a linha da vírgula corrigida. O modelo
retreinado dá predições idênticas em 3.000 tickets (diferença máxima de
probabilidade: 5,7e-05, ruído de convergência entre scikit-learn 1.9.0 e
1.9.1), então o binário commitado foi mantido em vez de gerar 8 MB de diff
sem efeito.

A aba de lote, agora com o caminho certo, roda sobre 400 tickets reais e
entrega 59,0% de cobertura automática a 99,2% de acurácia — coerente com os
60,11% a 97,48% medidos no conjunto de teste completo. Um dos oito exemplos
reais (um ticket de Hardware) é classificado errado, com 63,2% de
confiança: abaixo do limiar, portanto vai para humano. O comportamento
correto, e o motivo de os exemplos serem sorteados do dataset com o rótulo
verdadeiro à vista em vez de escritos para a demo.

**Aprendizado:** as três correções graves são todas de *propagação* — não de
raciocínio. Um número mudou na Etapa 15 e não chegou a um dos quatro
lugares onde aparecia; um caminho foi escrito uma vez e nunca reexecutado do
diretório certo; um tempo foi citado de memória em vez de lido do JSON ao
lado. Nenhuma delas seria pega relendo o texto: só reexecutando num
ambiente limpo e conferindo cada número contra a saída que o gerou.

---

### Etapa 17 — Reversão da convenção sem acento: português correto no código também

Os relatórios e o README sempre estiveram em português correto. O código
não: docstrings, comentários, mensagens de `print`, rótulos da interface do
protótipo e campos de texto dos JSONs estavam sem acento. A Etapa 14
registra isso como decisão deliberada — "por segurança de encoding em
terminal" — e a decisão tinha uma razão real: o console do Windows usa
cp1252 por padrão, e imprimir `acurácia` levanta `UnicodeEncodeError`.

**O problema é que a razão era tratável e eu tratei o sintoma.** A solução
correta não era escrever português errado; era reconfigurar a saída:

```python
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
```

Quatro linhas no topo de cada script, e o problema deixa de existir — sem
depender de `PYTHONIOENCODING` nem de `-X utf8` na linha de comando.
Verifiquei rodando os três scripts **sem** nenhuma flag: saída acentuada,
zero erro.

**O que foi acentuado, e o que deliberadamente não foi.** Identificadores
de Python e chaves de JSON continuam sem acento, por dois motivos: é o
padrão da linguagem, e as chaves são contrato entre os scripts e o
protótipo (`curva_cobertura_x_acuracia` é lida pelo script 02 e pelo app —
acentuar quebraria a leitura). Todo texto destinado a leitura humana foi
corrigido: docstrings, comentários, `print`, rótulos da UI, campos de texto
dos JSONs, e os rótulos dos dois diagramas SVG que são renderizados dentro
do PDF ("ROTEAMENTO AUTOMÁTICO", "Categoria sensível?", "Confiança ≥ 0,80").
A capa do PDF dizia "Diagnostico operacional, proposta de automacao" — na
primeira página do documento entregue.

**Um bug encontrado no caminho.** A formatação de moeda no protótipo usava
`.replace(",", ".")` sobre a string inteira, o mesmo padrão que a Etapa 16
já havia corrigido no script 02. Substituído por uma função `num_br()` que
troca os dois separadores de uma vez, e que agora formata também os números
da interface no padrão brasileiro: a acurácia aparece como `86,40%`, não
`86.4%`, e o R² como `−0,0525`, com vírgula decimal e sinal de menos
tipográfico — a mesma notação dos relatórios, para que o número conferido
na tela seja reconhecível no documento.

**O que ficou de fora:** `outputs/embeddings_zeroshot_metricas.json`. Os
números dele são os atuais e conferem com o que os relatórios citam, mas os
campos de texto descritivo continuam sem acento, porque regerar o arquivo
exige reinstalar torch e transformers (~2,5 GB), baixar ~1,7 GB de modelos e
esperar ~30 min de CPU. O script 04 já está acentuado — rodá-lo regenera o
arquivo corrigido. A pendência está anotada no próprio cabeçalho do script,
onde quem for reproduzir vai ler.

**Revalidação:** os três scripts reexecutados, todos os números idênticos
(86,40% de acurácia, R$ 63.471,98/ano, payback de 2,6 meses, R² de teste
−0,0525). A aba de lote confere: 59,0% de cobertura a 99,2% de acurácia
sobre 400 tickets reais, com o invariante `humano = sensível + confiança
baixa` fechando. PDF reconstruído em 26 páginas, sem nenhuma palavra
portuguesa sem acento — só nomes de arquivo, que continuam como devem ser.

**Aprendizado:** convenção documentada não é convenção justificada. Eu
tinha registrado a escolha no diário, o que a fez parecer decidida em vez de
apenas conveniente. Escrever a razão ("segurança de encoding") sem testar se
ela era contornável transformou uma limitação de ferramenta em regra de
estilo — e regra de estilo herdada de limitação não questionada é como
código fica errado por anos com aparência de intencional.

---

## Gaps e riscos em aberto

| # | Item | Natureza | Status |
|---|---|---|---|
| 1 | Brief promete ~30.000 registros no DS1; existem 8.469 | Divergência factual do enunciado | Documentado no laudo |
| 2 | Brief promete "texto real"; é template + Faker | Divergência factual do enunciado | Documentado no laudo |
| 3 | `submissions/` no `.gitignore` | Falha silenciosa de submissão | Contornado com `git add -f` |
| 4 | DS2 tem rótulos ruidosos (ex.: pedido de acesso rotulado como "HR Support") | Teto de acurácia do classificador | Quantificado: confusões Hardware↔Misc↔HR somam ~5% por classe. Tratado como limite de taxonomia, não de modelo |
| 5 | DS2 desbalanceado 7,74× | Risco de viés para a classe majoritária | Resolvido com `class_weight="balanced"`; F1 macro 0,865 e nenhuma classe com recall < 70% |
| 6 | DS2 vem pré-processado (lematizado, sem stopwords, PII mascarada) | Limita o ganho de LLM sobre TF-IDF | **Fechado na Etapa 13** — embeddings (MiniLM) e zero-shot (BART-MNLI) testados no mesmo split: 78,07% e 23,75% contra 86,40% do TF-IDF. O pré-processamento é a causa, e está explicada na proposta |
| 7 | Sem dados temporais reais, não há cálculo honesto de horas desperdiçadas | Impacta o pedido de ROI | Mitigado: ROI por volume (fato) × tempo/tarefa (premissa explícita) × cobertura medida. Todas as premissas editáveis no protótipo |
| 8 | Modelo treinado em TI corporativo em inglês | Acurácia cai em outro domínio/idioma | **Em aberto** — mitigação proposta: fase de sombra antes de rotear |

### Risco principal da estratégia

Denunciar o dataset é a maior aposta desta submissão. Se o avaliador esperar o relatório convencional de gargalos, a entrega pode ser lida como fuga do escopo.

**Mitigação adotada:** não parar na denúncia. Entregar as três respostas que o Diretor pediu, pelo caminho honesto — instrumento parametrizável em vez de números inventados — e deixar explícito, com números reproduzíveis, por que este é o único caminho defensável. O critério de avaliação declarado no README (*"a análise distingue correlação de causalidade"*) sustenta a escolha.

## O que ficou de fora, e por quê

- **LLM proprietário via API como classificador.** Embeddings locais e zero-shot local foram testados (Etapa 13) e perderam do TF-IDF. O que ficou de fora foi o teste com um LLM pago (GPT/Claude) como classificador: exigiria chave de API e custo por chamada permanente, e o resultado dos dois testes locais indica que o limite aqui é o formato do texto — já lematizado e sem stopwords — não a capacidade do modelo.
- **Detecção de duplicatas.** O brief cita como possibilidade. O DS2 tem zero duplicatas exatas, e sem ID de cliente ou timestamp não dá para detectar reaberturas — que é o caso que realmente importa.
- **Respostas sugeridas.** Descartado por falta de base: o único campo de resolução disponível é texto gerado por Faker.

## Decisão sobre a evidência visual

Os 15 screenshots da sessão real foram capturados e indexados na Etapa 12 (`process-log/screenshots/`). **O screen recording foi descartado por opção.** O guia de submissão lista os formatos de process log como alternativas combináveis, não como uma lista obrigatória, e esta entrega traz quatro: screenshots cronológicos, narrativa escrita (este diário), git history e código reproduzível de ponta a ponta. A gravação acrescentaria a demonstração do protótipo em movimento — que quem avalia obtém em dois comandos, com o modelo já versionado no repositório, sem precisar treinar nada.

O raciocínio da escolha: vídeo é a evidência mais custosa de produzir e a mais custosa de consumir. Um avaliador com mais de cem pull requests na fila lê um diário e roda um `streamlit run` mais rápido do que assiste a quatro minutos de narração.
