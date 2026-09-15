# Process Log — evidências

O relato completo está em dois lugares, ambos escritos **durante** o trabalho:

| Evidência | Onde | O que mostra |
|---|---|---|
| **Narrativa escrita** | [`docs/DIARIO_DE_BORDO.md`](../docs/DIARIO_DE_BORDO.md) | Decisões, percalços, gaps abertos e as correções de rota, em ordem cronológica |
| **Process log estruturado** | [`README.md`](../README.md#process-log--como-usei-ia) | Ferramentas, workflow, onde a IA errou, o que acrescentei |
| **Git history** | `git log --oneline` nesta branch | Evolução do raciocínio nas mensagens de commit |
| **Código reproduzível** | [`../solution/scripts/`](../solution/scripts/) | Todo número da submissão sai daqui, executável de ponta a ponta |
| **Saídas brutas** | [`../solution/outputs/`](../solution/outputs/) | JSONs com estatísticas e p-valores, para conferência independente |

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
