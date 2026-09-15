"""
03 - Classificador de tickets (Dataset 2)
=========================================
Treina e avalia o motor de triagem automatica sobre os 47.837 tickets reais.

O ponto central nao e a acuracia bruta: e a CURVA DE COBERTURA x ACURACIA.
Um classificador que acerta 85% no geral e inutil para automacao se nao
souber quando esta inseguro. O que importa operacionalmente e:

    "acima do limiar X de confianca, o modelo cobre Y% dos tickets
     com Z% de acuracia - e os (100-Y)% restantes vao para humano"

Esse Y medido e o que alimenta o calculo de ROI. Substitui premissa por dado.

Uso:   python 03_classificador.py
Saida: outputs/classificador_metricas.json
       outputs/modelo_triagem.joblib
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix,
                             f1_score, accuracy_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

AQUI = Path(__file__).resolve()
RAIZ_REPO = AQUI.parents[4]
DADOS = RAIZ_REPO / "datasets" / "raw"
SAIDA = AQUI.parents[1] / "outputs"
SAIDA.mkdir(parents=True, exist_ok=True)

SEMENTE = 42
LIMIARES = [0.0, 0.50, 0.60, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95]


def carregar():
    d = pd.read_csv(DADOS / "all_tickets_processed_improved_v3.csv")
    d = d.dropna(subset=["Document", "Topic_group"])
    return d


def construir_pipeline():
    """TF-IDF + regressao logistica.

    Escolha deliberada por modelo linear e nao por LLM/transformer:
    - roda em CPU, sem GPU e sem custo por chamada
    - inferencia em milissegundos, compativel com triagem em tempo real
    - class_weight balanced compensa o desbalanceamento de 7,74x
    - e auditavel: da para extrair os termos que levaram a cada decisao,
      o que importa quando um agente questiona o roteamento
    """
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=3,
                                  max_features=120_000, sublinear_tf=True,
                                  strip_accents="unicode")),
        ("clf", LogisticRegression(max_iter=2000, C=4.0,
                                   class_weight="balanced")),
    ])


def curva_cobertura(y_true, y_pred, confianca):
    """Para cada limiar: quanto o modelo cobre e com que acuracia."""
    linhas = []
    for limiar in LIMIARES:
        aceito = confianca >= limiar
        n_aceito = int(aceito.sum())
        if n_aceito == 0:
            continue
        acc = float(accuracy_score(y_true[aceito], y_pred[aceito]))
        linhas.append({
            "limiar_confianca": limiar,
            "cobertura_pct": round(n_aceito / len(y_true) * 100, 2),
            "n_automatizados": n_aceito,
            "acuracia_no_aceito_pct": round(acc * 100, 2),
            "n_escalados_para_humano": int(len(y_true) - n_aceito),
            "erros_que_passariam": int(round((1 - acc) * n_aceito)),
        })
    return linhas


def desempenho_por_classe(y_true, y_pred, classes):
    rel = classification_report(y_true, y_pred, output_dict=True,
                                zero_division=0)
    saida = {}
    for c in classes:
        if c in rel:
            saida[c] = {k: round(float(v), 4) for k, v in rel[c].items()}
    return saida


def main():
    d = carregar()
    X, y = d["Document"], d["Topic_group"]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=SEMENTE, stratify=y)

    print(f"Treino: {len(X_tr)} | Teste: {len(X_te)}")
    print("Treinando TF-IDF + LogisticRegression...")
    pipe = construir_pipeline()
    pipe.fit(X_tr, y_tr)

    proba = pipe.predict_proba(X_te)
    classes = list(pipe.named_steps["clf"].classes_)
    y_pred = np.array(classes)[proba.argmax(axis=1)]
    confianca = proba.max(axis=1)
    y_te_arr = y_te.to_numpy()

    acc = float(accuracy_score(y_te_arr, y_pred))
    f1m = float(f1_score(y_te_arr, y_pred, average="macro"))
    f1w = float(f1_score(y_te_arr, y_pred, average="weighted"))

    # baseline: sempre a classe majoritaria
    majoritaria = y_tr.value_counts().idxmax()
    acc_baseline = float((y_te_arr == majoritaria).mean())

    curva = curva_cobertura(y_te_arr, y_pred, confianca)
    por_classe = desempenho_por_classe(y_te_arr, y_pred, classes)
    cm = confusion_matrix(y_te_arr, y_pred, labels=classes)

    # confusoes mais frequentes: onde o modelo erra sistematicamente
    confusoes = []
    for i, real in enumerate(classes):
        for j, previsto in enumerate(classes):
            if i != j and cm[i, j] > 0:
                confusoes.append({"real": real, "previsto": previsto,
                                  "n": int(cm[i, j]),
                                  "pct_da_classe_real": round(
                                      cm[i, j] / cm[i].sum() * 100, 2)})
    confusoes.sort(key=lambda r: r["n"], reverse=True)

    # classes com recall baixo nao devem ser automatizadas
    frageis = {c: m for c, m in por_classe.items() if m.get("recall", 1) < 0.70}

    resultado = {
        "configuracao": {
            "n_treino": int(len(X_tr)), "n_teste": int(len(X_te)),
            "n_classes": len(classes), "classes": classes,
            "modelo": "TF-IDF (1-2 gramas) + LogisticRegression balanced",
            "semente": SEMENTE,
        },
        "desempenho_global": {
            "acuracia_pct": round(acc * 100, 2),
            "f1_macro": round(f1m, 4),
            "f1_ponderado": round(f1w, 4),
            "baseline_classe_majoritaria_pct": round(acc_baseline * 100, 2),
            "ganho_sobre_baseline_pp": round((acc - acc_baseline) * 100, 2),
        },
        "curva_cobertura_x_acuracia": curva,
        "desempenho_por_classe": por_classe,
        "matriz_confusao": {"labels": classes, "matriz": cm.tolist()},
        "confusoes_mais_frequentes": confusoes[:10],
        "classes_frageis_recall_abaixo_70": list(frageis.keys()),
    }

    (SAIDA / "classificador_metricas.json").write_text(
        json.dumps(resultado, indent=2, ensure_ascii=False), encoding="utf-8")
    dump(pipe, SAIDA / "modelo_triagem.joblib")

    # --------------------------------------------------------- relatorio
    print("\n" + "=" * 78)
    print("CLASSIFICADOR DE TRIAGEM - RESULTADOS")
    print("=" * 78)
    g = resultado["desempenho_global"]
    print(f"\nAcuracia global: {g['acuracia_pct']}%  "
          f"(baseline classe majoritaria: {g['baseline_classe_majoritaria_pct']}%, "
          f"ganho +{g['ganho_sobre_baseline_pp']} p.p.)")
    print(f"F1 macro: {g['f1_macro']} | F1 ponderado: {g['f1_ponderado']}")

    print("\nCURVA COBERTURA x ACURACIA (o numero que importa p/ automacao)")
    print(f"{'limiar':>8} {'cobertura':>11} {'acuracia':>10} "
          f"{'p/ humano':>11} {'erros':>8}")
    for r in curva:
        print(f"{r['limiar_confianca']:>8.2f} "
              f"{r['cobertura_pct']:>10.2f}% "
              f"{r['acuracia_no_aceito_pct']:>9.2f}% "
              f"{r['n_escalados_para_humano']:>11d} "
              f"{r['erros_que_passariam']:>8d}")

    print("\nDESEMPENHO POR CLASSE")
    print(f"{'classe':>24} {'precisao':>9} {'recall':>8} {'f1':>8} {'n':>7}")
    for c, m in sorted(por_classe.items(), key=lambda kv: -kv[1]["f1-score"]):
        print(f"{c:>24} {m['precision']:>9.3f} {m['recall']:>8.3f} "
              f"{m['f1-score']:>8.3f} {int(m['support']):>7d}")

    print("\nCONFUSOES MAIS FREQUENTES")
    for r in confusoes[:6]:
        print(f"  {r['real']:>22} -> {r['previsto']:<22} "
              f"{r['n']:>4} ({r['pct_da_classe_real']}% da classe)")

    if frageis:
        print(f"\nCLASSES FRAGEIS (recall < 70%): {', '.join(frageis)}")
        print("  -> candidatas a NAO automatizar; ver item 2 do relatorio.")

    print("\n" + "=" * 78)
    print(f"Modelo salvo em: {SAIDA / 'modelo_triagem.joblib'}")
    print("=" * 78)


if __name__ == "__main__":
    main()
