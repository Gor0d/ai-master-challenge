"""
04 — Embeddings e zero-shot classification (Dataset 2)
======================================================
Resposta direta ao benchmark que o próprio brief cita como exemplo de
resposta "específica": classificar em 8 categorias usando embeddings e
zero-shot classification.

Compara três abordagens no MESMO split de teste do script 03
(random_state=42, test_size=0.25, stratify=y), para que a comparação
seja justa — mesmos tickets de teste em todas:

  1. TF-IDF + LogisticRegression   (baseline já reportado no script 03)
  2. Embeddings (MiniLM) + LogisticRegression   (dataset de teste inteiro)
  3. Zero-shot local (BART-MNLI)   (amostra estratificada do teste, por
     custo computacional: ~1,7s/ticket em CPU, 8 hipóteses por ticket)

Tudo roda local, sem chave de API e sem GPU. Reprodução completa, sem
dependência de serviço externo.

Convenção: identificadores em Python e chaves de JSON seguem sem acento
(as chaves são contrato entre os scripts); todo texto destinado a leitura
humana é escrito em português correto.

NOTA SOBRE A SAÍDA VERSIONADA: o arquivo
outputs/embeddings_zeroshot_metricas.json que está no repositório foi
gerado antes da revisão de acentuação. Os números dele são os atuais e
conferem com o que os relatórios citam; os campos de texto descritivo
("objetivo", "nota_metodologica", "custo") aparecem lá sem acento porque
reproduzir o experimento custa ~2,5 GB de dependências, ~1,7 GB de modelos
e ~30 min em CPU. Rodar este script novamente regenera o arquivo já com a
acentuação correta.

Uso:   python 04_embeddings_zeroshot.py
Saída: outputs/embeddings_zeroshot_metricas.json
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, classification_report
from sklearn.model_selection import train_test_split

# O relatório em stdout é acentuado e o console do Windows usa cp1252 por
# padrão, o que levantaria UnicodeEncodeError.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = Path(__file__).resolve()
RAIZ_REPO = AQUI.parents[4]
DADOS = RAIZ_REPO / "datasets" / "raw"
SAIDA = AQUI.parents[1] / "outputs"
SAIDA.mkdir(parents=True, exist_ok=True)

SEMENTE = 42
N_AMOSTRA_ZEROSHOT = 240  # ~30 por classe; custo dominante do experimento


def carregar():
    d = pd.read_csv(DADOS / "all_tickets_processed_improved_v3.csv")
    d = d.dropna(subset=["Document", "Topic_group"])
    return d


def split_identico_ao_script_03(d):
    """Mesmo split do 03_classificador.py — garante comparação justa."""
    X, y = d["Document"], d["Topic_group"]
    return train_test_split(X, y, test_size=0.25, random_state=SEMENTE,
                            stratify=y)


def carregar_tfidf_baseline():
    """Lê o resultado já calculado pelo script 03, para não duplicar treino."""
    arq = SAIDA / "classificador_metricas.json"
    if not arq.exists():
        return None
    d = json.loads(arq.read_text(encoding="utf-8"))
    return d["desempenho_global"]


# ------------------------------------------------------ 1. embeddings

def avaliar_embeddings(X_tr, X_te, y_tr, y_te):
    from sentence_transformers import SentenceTransformer

    print("Carregando modelo de embeddings (all-MiniLM-L6-v2)...")
    t0 = time.time()
    modelo_emb = SentenceTransformer("all-MiniLM-L6-v2")
    t_carga = time.time() - t0

    print(f"Gerando embeddings para {len(X_tr) + len(X_te)} tickets...")
    t0 = time.time()
    E_tr = modelo_emb.encode(X_tr.tolist(), batch_size=64, show_progress_bar=False)
    E_te = modelo_emb.encode(X_te.tolist(), batch_size=64, show_progress_bar=False)
    t_encode = time.time() - t0

    clf = LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced")
    t0 = time.time()
    clf.fit(E_tr, y_tr)
    t_treino = time.time() - t0

    y_pred = clf.predict(E_te)
    acc = float(accuracy_score(y_te, y_pred))
    f1m = float(f1_score(y_te, y_pred, average="macro"))
    f1w = float(f1_score(y_te, y_pred, average="weighted"))
    rel = classification_report(y_te, y_pred, output_dict=True, zero_division=0)

    return {
        "modelo": "sentence-transformers/all-MiniLM-L6-v2 (384 dim) + LogisticRegression",
        "n_treino": int(len(X_tr)), "n_teste": int(len(X_te)),
        "tempo_carga_modelo_s": round(t_carga, 1),
        "tempo_encoding_s": round(t_encode, 1),
        "tempo_treino_classificador_s": round(t_treino, 2),
        "acuracia_pct": round(acc * 100, 2),
        "f1_macro": round(f1m, 4),
        "f1_ponderado": round(f1w, 4),
        "desempenho_por_classe": {
            c: {k: round(float(v), 4) for k, v in rel[c].items()}
            for c in clf.classes_ if c in rel
        },
    }


# ------------------------------------------------------ 2. zero-shot

def avaliar_zero_shot(X_te, y_te, classes):
    from transformers import pipeline

    # Amostra estratificada do TESTE (mesmos tickets que os outros dois
    # métodos viram) — o custo computacional impede rodar no teste inteiro.
    df_te = pd.DataFrame({"texto": X_te.values, "rotulo": y_te.values})
    por_classe = max(1, N_AMOSTRA_ZEROSHOT // len(classes))
    # Não usar groupby().apply(): no pandas 3.x a coluna de agrupamento é
    # excluída do grupo passado à função por padrão, derrubando 'rotulo' do
    # resultado. A concatenação manual evita a armadilha.
    amostra = pd.concat(
        [g.sample(n=min(len(g), por_classe), random_state=SEMENTE)
         for _, g in df_te.groupby("rotulo")],
        ignore_index=True,
    )

    print("Carregando modelo zero-shot (facebook/bart-large-mnli)...")
    t0 = time.time()
    clf = pipeline("zero-shot-classification", model="facebook/bart-large-mnli",
                   device=-1)
    t_carga = time.time() - t0

    print(f"Classificando {len(amostra)} tickets via zero-shot "
          f"(~{len(amostra) * 1.7 / 60:.1f} min estimados)...")
    t0 = time.time()
    previstos = []
    for texto in amostra["texto"]:
        r = clf(texto[:512], classes, multi_label=False)
        previstos.append(r["labels"][0])
    t_infer = time.time() - t0

    y_true = amostra["rotulo"].tolist()
    acc = float(accuracy_score(y_true, previstos))
    f1m = float(f1_score(y_true, previstos, average="macro", zero_division=0))

    return {
        "modelo": "facebook/bart-large-mnli (zero-shot, sem treino)",
        "n_amostra": int(len(amostra)),
        "amostra_do_conjunto_de_teste": True,
        "tempo_carga_modelo_s": round(t_carga, 1),
        "tempo_inferencia_total_s": round(t_infer, 1),
        "tempo_medio_por_ticket_s": round(t_infer / len(amostra), 3),
        "acuracia_pct": round(acc * 100, 2),
        "f1_macro": round(f1m, 4),
        "nota_metodologica": (
            f"Amostra estratificada de {len(amostra)} tickets do MESMO "
            "conjunto de teste usado pelo TF-IDF e pelos embeddings — não "
            "é o teste inteiro (11.960 tickets) por custo computacional: "
            "o MNLI avalia 8 hipóteses de entailment por ticket em CPU, "
            f"~{t_infer / len(amostra):.2f}s/ticket. Comparação válida "
            "estatisticamente, mas com intervalo de confiança maior que "
            "os outros dois métodos."),
    }


def main():
    d = carregar()
    X_tr, X_te, y_tr, y_te = split_identico_ao_script_03(d)
    classes = sorted(d["Topic_group"].unique())

    tfidf = carregar_tfidf_baseline()
    if tfidf is None:
        print("AVISO: rode 03_classificador.py antes, para ter o baseline "
              "TF-IDF para comparação.")

    print("=" * 78)
    print("EXPERIMENTO: EMBEDDINGS E ZERO-SHOT vs. TF-IDF")
    print("=" * 78)

    resultado_emb = avaliar_embeddings(X_tr, X_te, y_tr, y_te)
    print(f"\n[EMBEDDINGS] acurácia={resultado_emb['acuracia_pct']}% "
          f"f1_macro={resultado_emb['f1_macro']}")

    resultado_zs = avaliar_zero_shot(X_te, y_te, classes)
    print(f"\n[ZERO-SHOT]  acurácia={resultado_zs['acuracia_pct']}% "
          f"f1_macro={resultado_zs['f1_macro']} "
          f"(amostra n={resultado_zs['n_amostra']})")

    comparacao = {
        "tfidf_logreg": {
            "acuracia_pct": tfidf["acuracia_pct"] if tfidf else None,
            "f1_macro": tfidf["f1_macro"] if tfidf else None,
            "n_teste": 11960,
            "custo": "nenhum — CPU, sem download de modelo",
        },
        "embeddings_minilm_logreg": {
            "acuracia_pct": resultado_emb["acuracia_pct"],
            "f1_macro": resultado_emb["f1_macro"],
            "n_teste": resultado_emb["n_teste"],
            "custo": (f"download ~80MB; {resultado_emb['tempo_encoding_s']}s "
                      "de encoding em CPU"),
        },
        "zero_shot_bart_mnli": {
            "acuracia_pct": resultado_zs["acuracia_pct"],
            "f1_macro": resultado_zs["f1_macro"],
            "n_teste": resultado_zs["n_amostra"],
            "custo": (f"download ~1.6GB; "
                      f"{resultado_zs['tempo_medio_por_ticket_s']}s/ticket "
                      "em CPU, sem treino"),
        },
    }

    resultado = {
        "objetivo": ("Testar se embeddings e zero-shot superam o baseline "
                     "TF-IDF + LogisticRegression já reportado, no mesmo "
                     "split de teste."),
        "embeddings": resultado_emb,
        "zero_shot": resultado_zs,
        "comparacao_resumida": comparacao,
    }

    destino = SAIDA / "embeddings_zeroshot_metricas.json"
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False),
                       encoding="utf-8")

    print("\n" + "=" * 78)
    print("COMPARAÇÃO FINAL (mesmo split de teste)")
    print("=" * 78)
    print(f"{'Método':<28} {'Acurácia':>10} {'F1 macro':>10} {'N teste':>10}")
    for nome, c in comparacao.items():
        acc = f"{c['acuracia_pct']:.2f}%" if c['acuracia_pct'] is not None else "N/A"
        f1 = f"{c['f1_macro']:.4f}" if c['f1_macro'] is not None else "N/A"
        print(f"{nome:<28} {acc:>10} {f1:>10} {c['n_teste']:>10}")
    print(f"\nJSON salvo em: {destino}")
    print("=" * 78)


if __name__ == "__main__":
    main()
