# Setup

## 1. Dependências

```bash
pip install -r submissions/emerson-guimaraes/solution/requirements.txt
```

Instalação leve: pandas, scikit-learn, scipy, joblib, streamlit e markdown. Sem torch, sem GPU, sem chave de API.

As dependências do experimento comparativo (script 04 — embeddings e zero-shot) ficam em `requirements-experimento.txt` porque somam ~2,5 GB e **não** são necessárias para o diagnóstico, o classificador ou o protótipo.

## 2. Dados

Os dois CSVs do Kaggle precisam estar em `datasets/raw/` na **raiz do repositório**
(essa pasta já é ignorada pelo `.gitignore`, então os dados não vão para o PR).

```
datasets/raw/
├── customer_support_tickets.csv              (Dataset 1)
└── all_tickets_processed_improved_v3.csv     (Dataset 2)
```

### Via API do Kaggle

**Atenção:** o Kaggle migrou o sistema de autenticação. O fluxo antigo
("Create New Token" gerando um `kaggle.json`) **não funciona mais** — hoje a
plataforma emite um token único no formato `KGAT_...`.

```bash
pip install kaggle

# kaggle.com/settings -> API -> Create New Token  (copie o token KGAT_...)
mkdir -p ~/.kaggle
echo "SEU_TOKEN_KGAT_AQUI" > ~/.kaggle/access_token
chmod 600 ~/.kaggle/access_token

python -m kaggle datasets download -d suraj520/customer-support-ticket-dataset \
  -p datasets/raw --unzip
python -m kaggle datasets download -d adisongoh/it-service-ticket-classification-dataset \
  -p datasets/raw --unzip
```

### Manualmente

- [Customer Support Ticket Dataset](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset)
- [IT Service Ticket Classification Dataset](https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset)

## 3. Reproduzir os resultados

Na ordem — o script 02 consome a saída do 03, então rode o 03 antes:

```bash
cd submissions/emerson-guimaraes/solution

python scripts/01_auditoria_integridade.py     # 9 testes de integridade
python scripts/03_classificador.py             # treina o modelo (~1 min)
python scripts/02_diagnostico_operacional.py   # diagnóstico + ROI

# Opcional - compara TF-IDF com embeddings e zero-shot (~30 min em CPU).
# Requer as dependencias extras e baixa ~1,7GB de modelos na 1a execucao:
#   pip install -r requirements-experimento.txt
python scripts/04_embeddings_zeroshot.py
```

Saídas em `solution/outputs/`:

| Arquivo | Conteúdo |
|---|---|
| `auditoria_resultados.json` | Os 9 testes de integridade, com estatísticas e p-valores |
| `classificador_metricas.json` | Acurácia, F1 por classe, matriz de confusão, curva de cobertura |
| `diagnostico_operacional.json` | Gargalos, drivers de CSAT e cenários de ROI |
| `modelo_triagem.joblib` | Modelo treinado, usado pelo protótipo |
| `embeddings_zeroshot_metricas.json` | Comparação TF-IDF vs. embeddings vs. zero-shot (opcional) |

## 4. Rodar o protótipo

```bash
streamlit run app/app.py
```

Abre em `http://localhost:8501`.

## Ambiente de referência

Python 3.14 · pandas 3.0.2 · scikit-learn 1.9.0 · streamlit 1.60.0 · Windows 11
