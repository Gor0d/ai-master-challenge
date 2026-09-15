# Proposta de Automação com IA

Para: Diretor de Operações · Baseado nos dois datasets · Números medidos, não estimados

---

## Resumo em cinco linhas

Treinei um classificador nos 47.837 tickets reais do Dataset 2. Ele acerta **86,4%** dos casos contra 28,47% do baseline. Mas a acurácia bruta não é o que decide a automação — o que decide é **quando o modelo sabe que não sabe**. Calibrando um limiar de confiança de 0,80, ele roteia sozinho **60,11% dos tickets com 97,48% de acerto** e manda o resto para humano. Isso libera **1.111 horas/ano (R$ 50 mil, 0,57 FTE)** numa operação de 30 mil tickets — já descontado o retrabalho dos próprios erros.

---

## 1. O que automatizar

### 1.1 Triagem e roteamento por categoria — **automatizar**

É o caso mais forte, e é onde está o volume. O modelo lê o texto do chamado e o encaminha para uma das 8 filas.

| Métrica | Valor |
|---|---|
| Acurácia global | 86,40% |
| Baseline (sempre a classe majoritária) | 28,47% |
| Ganho | **+57,93 p.p.** |
| F1 macro | 0,8653 |
| Tempo de inferência | milissegundos, em CPU |

**A curva que importa para a decisão operacional:**

| Limiar | Cobertura automática | Acurácia no automatizado | Erros por 1.000 tickets |
|---|---|---|---|
| sem limiar | 100% | 86,40% | 136 |
| 0,70 | 69,67% | 95,91% | 29 |
| **0,80 (recomendado)** | **60,11%** | **97,48%** | **15** |
| 0,90 | 47,51% | 98,77% | 6 |

Ler assim: a 0,80, seis em cada dez tickets são roteados sem tocar em ninguém, e **15 em mil** caem na fila errada. Os outros quatro em dez chegam ao humano já com uma sugestão de categoria e o grau de confiança — ele não parte do zero.

### 1.2 Sugestão de categoria para o agente — **automatizar como apoio**

Nos 40% que vão para revisão humana, o modelo não fica calado: entrega sua melhor hipótese, as três alternativas seguintes e **os termos que pesaram na decisão**. Exemplo real de saída do protótipo, para um chamado de caixa postal cheia:

> `mailbox (+3,302)` · `archive (+1,750)` · `increase (+1,637)` · `full (+1,509)` · `quota (+1,096)` → **Storage**

O agente valida ou corrige em segundos, em vez de ler o chamado inteiro para descobrir a fila. E cada correção é dado de retreino.

### 1.3 Detecção de confiança baixa como sinal de qualidade — **automatizar**

Um ticket com confiança abaixo de 0,50 costuma ser um chamado mal escrito, genérico ou com vários assuntos misturados. Testei com o texto `"hi thanks"`: o modelo devolveu Miscellaneous com 38,2% e mandou para humano — comportamento correto.

Esse sinal tem uso secundário: **volume alto de baixa confiança em um produto ou período indica que o formulário de abertura está mal desenhado.** É diagnóstico de processo saindo de graça do classificador.

---

## 2. O que NÃO automatizar

Esta seção é a mais importante da proposta, e cada exclusão está justificada com número.

### 2.1 `Administrative rights` — nunca roteia sozinho

| | |
|---|---|
| Precisão | **0,733** — a pior das 8 classes |
| Recall | 0,825 |
| Volume | 1.760 tickets (a menor classe) |

**Um em cada quatro tickets que o modelo manda para esta fila não pertence a ela.** E o conteúdo é concessão de privilégio administrativo. O custo de errar é assimétrico: roteamento errado para "Hardware" gera irritação e retrabalho; concessão indevida de privilégio administrativo é incidente de segurança.

Quando o custo do falso positivo e o do falso negativo são de ordens de grandeza diferentes, otimizar acurácia média é a métrica errada. Fica em revisão humana obrigatória, **independentemente da confiança**.

### 2.2 `Purchase` — nunca roteia sozinho

Precisão alta (0,946), então não é um problema de modelo. É um problema de consequência: são decisões de gasto, com fornecedor, prazo e orçamento. Automatizar triagem aqui economiza segundos e cria risco de compromisso financeiro mal encaminhado. **A conta não fecha.**

### 2.3 A zona cinzenta Hardware ↔ Miscellaneous ↔ HR Support

As três confusões mais frequentes do modelo:

| Real | Previsto | Casos | % da classe |
|---|---|---|---|
| Hardware | Miscellaneous | 161 | 4,73% |
| HR Support | Hardware | 153 | 5,61% |
| Hardware | HR Support | 150 | 4,41% |

Isso **não é falha do modelo — é ambiguidade real do rótulo**. Um pedido de notebook para um funcionário novo é Hardware ou HR Support? Depende de convenção interna, e a própria base rotula de formas diferentes. Nenhum modelo resolve inconsistência de taxonomia.

A saída não é técnica: é **revisar a taxonomia** com a operação. Enquanto isso, o limiar de confiança já contém o dano, porque casos ambíguos naturalmente produzem confiança baixa.

### 2.4 Resposta automática ao cliente — **não automatizar agora**

O brief menciona respostas sugeridas. Descartei, e o motivo é de dado, não de opinião: o único campo de resolução disponível está no Dataset 1 e é texto gerado por biblioteca de dados falsos — *"West decision evidence bit."* — sem uma única ocorrência de `refund`, `replace`, `resolved` ou `reset` em 2.769 registros (ver [laudo](03_anexo_auditoria_dados.md)).

**Não existe base de respostas boas para aprender.** Construir sugestão de resposta sobre isso produziria um gerador de texto plausível e errado, entregue direto ao cliente — o pior lugar possível para um erro. Volta à mesa quando houver 3 a 6 meses de resoluções reais registradas.

### 2.5 Definição de prioridade e SLA — **não automatizar agora**

Mesma razão. Prioridade no Dataset 1 é uniforme (χ²=4,59, p=0,205) — sorteada. Não há sinal de prioridade real para aprender. Automatizar priorização sem dado histórico verdadeiro é transformar palpite em regra, com aparência de sistema.

---

## 3. Como funcionaria na prática

```
                        ┌─────────────────────────┐
   Ticket entra ───────▶│  Classificador          │
   (e-mail, chat,       │  TF-IDF + LogReg        │
    telefone, social)   │  saída: categoria +     │
                        │  confiança 0-1          │
                        └───────────┬─────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
         ┌──────────────────────┐        ┌─────────────────────┐
         │ Categoria sensível?  │  sim   │  FILA HUMANA        │
         │ (Admin rights,       ├───────▶│  com sugestão do    │
         │  Purchase)           │        │  modelo + termos    │
         └──────────┬───────────┘        │  que pesaram        │
                    │ não                └─────────────────────┘
                    ▼                               ▲
         ┌──────────────────────┐        não        │
         │ Confiança ≥ 0,80 ?   ├───────────────────┘
         └──────────┬───────────┘
                    │ sim  (60,11% dos tickets)
                    ▼
         ┌──────────────────────┐
         │  ROTEAMENTO          │
         │  AUTOMÁTICO          │──▶ fila especializada
         │  97,48% de acerto    │
         └──────────────────────┘
```

**Onde a IA atua:** leitura do texto, classificação, cálculo de confiança, e produção da explicação.

**Onde o humano é insubstituível:** decisões de privilégio e de gasto; casos de baixa confiança; correção do rótulo, que vira dado de retreino; e a revisão periódica da taxonomia.

**O ciclo de melhoria:** toda correção humana é registrada. O modelo é retreinado mensalmente com o acumulado. Conforme a precisão de uma classe sobe de forma estável, seu limiar pode ser reduzido — a cobertura automática cresce **por evidência**, não por decisão de calendário.

---

## 4. ROI

Premissas explícitas — e todas editáveis na calculadora do protótipo:

| Premissa | Valor adotado |
|---|---|
| Custo/hora do agente | R$ 45,00 |
| Triagem manual por ticket | 4,0 min |
| Retrabalho por roteamento errado | 12,0 min |
| Jornada | 168 h/mês |

**Operação de 30.000 tickets/ano:**

| Cenário | Limiar | Cobertura | Horas líquidas/ano | Economia/ano | FTE |
|---|---|---|---|---|---|
| Conservador | 0,90 | 47,51% | 915 | R$ 41.181 | 0,46 |
| **Recomendado** | **0,80** | **60,11%** | **1.111** | **R$ 50.009** | **0,57** |
| Agressivo | 0,70 | 69,67% | 1.223 | R$ 55.009 | 0,60 |

O custo total da triagem manual hoje, nas mesmas premissas, é de 2.000 h/ano (R$ 90.000).

**O detalhe que muda a decisão:** entre o cenário recomendado e o agressivo, a cobertura sobe 9,6 pontos, mas o ganho sobe apenas R$ 5 mil. O retrabalho dos erros adicionais consome quase todo o ganho. **Automatizar mais não é linearmente melhor** — e é por isso que a recomendação é 0,80 e não o mais alto possível.

---

## 5. Implantação sugerida

| Fase | Duração | O que acontece |
|---|---|---|
| **1. Sombra** | 2–4 semanas | Modelo classifica tudo, roteia nada. Compara-se a sugestão com a decisão do agente. Mede-se a acurácia na operação real, que é o único número que vale. |
| **2. Piloto** | 4 semanas | Roteamento automático ativo em 2 ou 3 filas de maior precisão (Purchase e Admin rights ficam de fora). Limiar conservador em 0,90. |
| **3. Expansão** | contínua | Baixa o limiar para 0,80 conforme a acurácia real confirma. Retreino mensal com as correções. |

**Critério de parada:** se a acurácia medida na fase de sombra ficar abaixo de 90% no limiar escolhido, não avança — investiga-se a diferença entre o dataset de treino e os tickets reais da operação.

---

## 6. Limitações

1. **O modelo foi treinado em tickets de TI corporativo em inglês**, já pré-processados (lematizados, sem stopwords, PII mascarada). Aplicado a chamados em português ou de outro domínio, a acurácia cai. A fase de sombra existe exatamente para medir isso antes de qualquer decisão.
2. **A taxonomia de 8 categorias veio do dataset, não da operação.** Se as filas reais forem outras, o modelo precisa ser retreinado com os rótulos certos — a arquitetura não muda.
3. **Os rótulos de treino têm ruído** (a ambiguidade Hardware/HR Support é da própria base). Os 86,4% provavelmente subestimam o desempenho com taxonomia limpa.
4. **Nenhum número de tempo ou satisfação do Dataset 1 foi usado**, porque o arquivo não passou na auditoria. O ROI depende de premissas de tempo por tarefa — que o Diretor deve substituir pelos números reais da operação dele.
