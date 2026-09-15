# Process Log — evidências

O relato completo está em dois lugares, ambos escritos **durante** o trabalho:

| Evidência | Onde | O que mostra |
|---|---|---|
| **Narrativa escrita** | [`docs/DIARIO_DE_BORDO.md`](../docs/DIARIO_DE_BORDO.md) | Decisões, percalços, gaps abertos e as correções de rota, em ordem cronológica |
| **Process log estruturado** | [`README.md`](../README.md#process-log--como-usei-ia) | Ferramentas, workflow, onde a IA errou, o que acrescentei |
| **Screenshots cronológicos** | [`screenshots/`](screenshots/) | 15 capturas da sessão real com o Claude Code, do clone do repositório ao checklist final |
| **Resumo visual** | [Case File 002](https://claude.ai/artifact/UEutxhGMDpEbQpWEB8xVBZ) | Página com a linha do tempo dos 9 marcos da sessão — complementa, não substitui, o diário e os screenshots |
| **Git history** | `git log --oneline` nesta branch | Evolução do raciocínio nas mensagens de commit |
| **Código reproduzível** | [`../solution/scripts/`](../solution/scripts/) | Todo número da submissão sai daqui, executável de ponta a ponta |
| **Saídas brutas** | [`../solution/outputs/`](../solution/outputs/) | JSONs com estatísticas e p-valores, para conferência independente |

## Screenshots

Capturas em sequência da sessão real de trabalho com o Claude Code — prompt, raciocínio e comandos executados, sem edição de conteúdo.

| # | Arquivo | Momento |
|---|---|---|
| 1 | `01-inicio-clone-repositorio.png` | Clone do repositório e primeira leitura da estrutura |
| 2 | `02-leitura-do-brief-e-escolha-do-desafio.png` | Resumo do case e escolha do Challenge 002 |
| 3 | `03-plano-de-ataque-e-hipotese-inicial.png` | Plano de 5 fases e a hipótese inicial sobre o Dataset 1 |
| 4 | `04-armadilha-gitignore-e-auditoria-iniciada.png` | Descoberta da armadilha do `.gitignore` + início da auditoria |
| 5 | `05-descoberta-dataset1-sintetico-5-provas.png` | As primeiras 5 provas de que o Dataset 1 é sintético |
| 6 | `06-retratacao-uniformidade-das-categoricas.png` | Retratação: teste de uniformidade derruba a hipótese estrutural |
| 7 | `07-fechamento-fase1-laudo-e-diario.png` | Fechamento da Fase 1, laudo e diário entregues |
| 8 | `08-redirecionamento-usuario-foco-no-brief.png` | Correção de rumo: focar nos 4 itens do brief, não só na auditoria |
| 9 | `09-curva-cobertura-acuracia-classificador.png` | Resultado do classificador e curva cobertura × acurácia |
| 10 | `10-roi-medido-e-inicio-do-prototipo.png` | ROI com cobertura medida + início do protótipo Streamlit |
| 11 | `11-autocorrecao-exemplos-cherry-picked.png` | Autocorreção: exemplos escritos à mão trocados por tickets reais |
| 12 | `12-validacao-prototipo-streamlit.png` | Validação de sintaxe e smoke-test do app |
| 13 | `13-entrega-completa-4-itens-do-brief.png` | Entrega completa dos 4 itens do brief |
| 14 | `14-tentativa-weasyprint-e-pivot-edge-headless.png` | WeasyPrint falha no Windows; pivô para Edge headless |
| 15 | `15-auditoria-final-e-checklist-de-submissao.png` | Auditoria de qualidade final e checklist de submissão |

**Nota de segurança:** as capturas 4 e 5 continham originalmente um token da API do Kaggle colado em texto puro durante a configuração do ambiente, no momento em que o candidato demonstrava o passo de autenticação. A região foi redigida (coberta) antes da publicação — o restante do conteúdo de ambas as imagens não foi alterado. O token já foi expirado em kaggle.com/settings e não concede mais acesso a nada; a redação é uma camada de cuidado adicional, não uma correção de um acesso ainda ativo.

## Os três erros corrigidos durante o trabalho

Resumo; o detalhamento está no diário.

**1. Aceitar os dados como válidos.** O comportamento padrão de qualquer assistente é executar a análise que o brief pediu. Ninguém mandou duvidar dos dados. A correção foi de premissa, não de sintaxe — e mudou a entrega inteira.

**2. Ceticismo pela metade.** Detectei que as métricas eram ruído e concluí cedo demais que os campos estruturais sobreviveriam, afirmando que os "67,3% de tickets nunca fechados" eram um backlog real. O teste de uniformidade com correção de Bonferroni derrubou isso: 6 de 6 categóricas uniformes. Retratado no anexo e no diário.

**3. Exemplos do protótipo mal rotulados.** Escrevi quatro exemplos à mão para a demo; ao testar, o rotulado "Acesso" saiu como Storage com 99,9% — e o modelo estava certo, o texto dizia *shared folder*. Substituí por tickets reais sorteados do dataset, com o rótulo verdadeiro visível.

## Como verificar

```bash
git log --oneline submission/emerson-guimaraes
```

As mensagens de commit registram a sequência, incluindo o commit em que a hipótese estrutural foi retratada.
