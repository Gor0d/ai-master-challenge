"""
02 - Diagnostico operacional (Dataset 1)
========================================
Responde as tres perguntas do item 1 do brief:

  a) Onde o fluxo trava?      -> gargalos por canal x prioridade x tipo
  b) O que impacta satisfacao? -> importancia de variaveis sobre o CSAT
  c) Quanto desperdicamos?     -> horas e custo, com premissas explicitas

Cada numero vem acompanhado de teste de significancia. Onde a diferenca
entre grupos nao e estatisticamente significativa, isso e dito - ranking
sem teste e ranking de ruido.

Uso:   python 02_diagnostico_operacional.py
Saida: outputs/diagnostico_operacional.json + relatorio em stdout
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

AQUI = Path(__file__).resolve()
RAIZ_REPO = AQUI.parents[4]
DADOS = RAIZ_REPO / "datasets" / "raw"
SAIDA = AQUI.parents[1] / "outputs"
SAIDA.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- premissas
# Explicitas e editaveis: o Diretor de Operacoes deve poder discordar de
# cada uma e recalcular. Nenhuma premissa esta escondida no codigo.
PREMISSAS = {
    "custo_hora_agente_brl": 45.00,      # salario + encargos + infra
    "minutos_triagem_manual": 4.0,       # ler, categorizar, rotear
    "minutos_por_ticket_retrabalho": 12.0,  # custo de um roteamento errado
    "jornada_horas_mes": 168,
    "fonte_premissas": ("Benchmarks de mercado para suporte N1 no Brasil. "
                        "Devem ser substituidos pelos numeros reais da "
                        "operacao antes de qualquer decisao de investimento."),
}

ALFA = 0.05


def carregar():
    d = pd.read_csv(DADOS / "customer_support_tickets.csv")
    frt = pd.to_datetime(d["First Response Time"], errors="coerce")
    ttr = pd.to_datetime(d["Time to Resolution"], errors="coerce")
    d["horas_resolucao"] = (ttr - frt).dt.total_seconds() / 3600
    return d


# ------------------------------------------------- a) onde o fluxo trava

def gargalos(d):
    """Ranking de combinacoes canal x prioridade x tipo por tempo medio."""
    base = d.dropna(subset=["horas_resolucao"])

    def resumo(chaves):
        g = (base.groupby(chaves)["horas_resolucao"]
             .agg(n="count", media="mean", mediana="median", desvio="std")
             .sort_values("media", ascending=False))
        return g

    por_canal = resumo(["Ticket Channel"])
    por_prioridade = resumo(["Ticket Priority"])
    por_tipo = resumo(["Ticket Type"])
    combo = resumo(["Ticket Channel", "Ticket Priority", "Ticket Type"])
    combo_relevante = combo[combo["n"] >= 20]

    # A diferenca entre os grupos e real ou e flutuacao amostral?
    testes = {}
    for col in ["Ticket Channel", "Ticket Priority", "Ticket Type"]:
        grupos = [g["horas_resolucao"].dropna().values for _, g in base.groupby(col)]
        f, p = stats.f_oneway(*grupos)
        testes[col] = {"F": round(float(f), 4), "p": round(float(p), 4),
                       "diferenca_significativa": bool(p < ALFA)}

    return {
        "n_tickets_com_tempo": int(len(base)),
        "tempo_medio_geral_horas": round(float(base["horas_resolucao"].mean()), 2),
        "por_canal": por_canal.round(2).to_dict("index"),
        "por_prioridade": por_prioridade.round(2).to_dict("index"),
        "por_tipo": por_tipo.round(2).to_dict("index"),
        "piores_5_combinacoes": {
            " | ".join(map(str, k)): {kk: round(float(vv), 2)
                                      for kk, vv in v.items()}
            for k, v in combo_relevante.head(5).to_dict("index").items()},
        "anova_por_dimensao": testes,
        "leitura": _leitura_gargalos(testes),
    }


def _leitura_gargalos(testes):
    sig = [k for k, v in testes.items() if v["diferenca_significativa"]]
    if not sig:
        return ("Nenhuma dimensao (canal, prioridade ou tipo) apresenta "
                "diferenca estatisticamente significativa de tempo de "
                "resolucao. O ranking acima existe, mas as diferencas estao "
                "dentro da flutuacao amostral: nao ha gargalo identificavel "
                "neste dataset. Priorizar o 'pior canal' seria agir sobre ruido.")
    return f"Dimensoes com diferenca significativa: {', '.join(sig)}."


# ------------------------------------------------- b) o que impacta CSAT

def drivers_satisfacao(d):
    """Importancia de cada variavel para prever o CSAT."""
    base = d.dropna(subset=["Customer Satisfaction Rating"]).copy()
    features = ["Ticket Channel", "Ticket Priority", "Ticket Type",
                "Customer Age", "Customer Gender", "horas_resolucao"]
    X = pd.get_dummies(base[features].fillna({"horas_resolucao": 0}),
                       columns=["Ticket Channel", "Ticket Priority",
                                "Ticket Type", "Customer Gender"])
    y = base["Customer Satisfaction Rating"]

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3,
                                              random_state=42)
    modelo = RandomForestRegressor(n_estimators=300, random_state=42,
                                   min_samples_leaf=5, n_jobs=-1)
    modelo.fit(X_tr, y_tr)

    r2_treino = float(modelo.score(X_tr, y_tr))
    r2_teste = float(modelo.score(X_te, y_te))

    imp = permutation_importance(modelo, X_te, y_te, n_repeats=20,
                                 random_state=42, n_jobs=-1)
    ranking = (pd.Series(imp.importances_mean, index=X.columns)
               .sort_values(ascending=False))

    # baseline: prever sempre a media
    baseline_mse = float(((y_te - y_tr.mean()) ** 2).mean())
    modelo_mse = float(((y_te - modelo.predict(X_te)) ** 2).mean())

    # correlacoes diretas
    correlacoes = {}
    for col in ["horas_resolucao", "Customer Age"]:
        sub = base.dropna(subset=[col])
        r, p = stats.pearsonr(sub[col], sub["Customer Satisfaction Rating"])
        correlacoes[col] = {"r": round(float(r), 4), "p": round(float(p), 4),
                            "significativa": bool(p < ALFA)}

    return {
        "r2_treino": round(r2_treino, 4),
        "r2_teste": round(r2_teste, 4),
        "mse_modelo": round(modelo_mse, 4),
        "mse_baseline_media": round(baseline_mse, 4),
        "ganho_sobre_baseline_pct": round((baseline_mse - modelo_mse)
                                          / baseline_mse * 100, 2),
        "top_10_variaveis": {k: round(float(v), 6)
                             for k, v in ranking.head(10).items()},
        "correlacoes_diretas": correlacoes,
        "leitura": _leitura_csat(r2_teste, correlacoes),
    }


def _leitura_csat(r2_teste, correlacoes):
    sig = [k for k, v in correlacoes.items() if v["significativa"]]
    if r2_teste <= 0:
        return (f"R2 de teste = {r2_teste:.4f} (negativo ou zero): o modelo "
                "preve o CSAT PIOR do que simplesmente chutar a media. "
                "Nenhuma variavel operacional disponivel - canal, prioridade, "
                "tipo, tempo de resolucao, idade ou genero - tem poder "
                "preditivo sobre a satisfacao neste dataset. A resposta "
                "honesta a pergunta 'o que impacta satisfacao?' e: nada "
                "que esteja medido aqui. Ver laudo de auditoria.")
    return f"Variaveis com correlacao significativa: {', '.join(sig) or 'nenhuma'}."


# ------------------------------------------------- c) quanto desperdicamos

def _curva_medida():
    """Le a curva cobertura x acuracia produzida pelo script 03.

    Este e o cruzamento entre os dois datasets: a taxa de automacao nao e
    estimada, e a cobertura MEDIDA do classificador treinado no Dataset 2,
    aplicada ao volume de tickets do Dataset 1.
    """
    arq = SAIDA / "classificador_metricas.json"
    if not arq.exists():
        return None
    dados = json.loads(arq.read_text(encoding="utf-8"))
    return dados["curva_cobertura_x_acuracia"]


def desperdicio(d):
    """Horas e custo de triagem manual, e quanto e recuperavel.

    O calculo NAO depende dos timestamps do Dataset 1 (que sao invalidos).
    Depende de volume - fato verificavel - e de premissas de tempo por
    tarefa, explicitas e ajustaveis. A taxa de automacao vem medida do
    classificador, nao arbitrada.
    """
    n_tickets = int(len(d))
    p = PREMISSAS
    horas_triagem_ano = n_tickets * p["minutos_triagem_manual"] / 60
    custo_triagem_ano = horas_triagem_ano * p["custo_hora_agente_brl"]

    curva = _curva_medida()
    cenarios = {}
    if curva:
        # tres pontos de operacao reais da curva, do mais cauteloso ao mais agressivo
        alvos = {"conservador": 0.90, "recomendado": 0.80, "agressivo": 0.70}
        por_limiar = {r["limiar_confianca"]: r for r in curva}
        for nome, limiar in alvos.items():
            r = por_limiar.get(limiar)
            if not r:
                continue
            cobertura = r["cobertura_pct"] / 100
            horas_brutas = horas_triagem_ano * cobertura
            # erros de roteamento custam retrabalho e precisam ser descontados
            taxa_erro = 1 - r["acuracia_no_aceito_pct"] / 100
            horas_retrabalho = (n_tickets * cobertura * taxa_erro
                                * p["minutos_por_ticket_retrabalho"] / 60)
            horas_liquidas = horas_brutas - horas_retrabalho
            cenarios[nome] = {
                "limiar_confianca": limiar,
                "cobertura_medida_pct": r["cobertura_pct"],
                "acuracia_no_automatizado_pct": r["acuracia_no_aceito_pct"],
                "horas_brutas_liberadas_ano": round(horas_brutas, 1),
                "horas_perdidas_em_retrabalho_ano": round(horas_retrabalho, 1),
                "horas_liquidas_ano": round(horas_liquidas, 1),
                "horas_liquidas_mes": round(horas_liquidas / 12, 1),
                "economia_liquida_brl_ano": round(
                    horas_liquidas * p["custo_hora_agente_brl"], 2),
                "equivalente_fte": round(
                    horas_liquidas / 12 / p["jornada_horas_mes"], 2),
            }

    fator = 30000 / n_tickets
    proj = {}
    for nome, c in cenarios.items():
        proj[nome] = {
            "horas_liquidas_ano": round(c["horas_liquidas_ano"] * fator, 1),
            "economia_liquida_brl_ano": round(
                c["economia_liquida_brl_ano"] * fator, 2),
            "equivalente_fte": round(c["equivalente_fte"] * fator, 2),
        }

    return {
        "premissas": p,
        "volume_tickets": n_tickets,
        "horas_triagem_manual_ano": round(horas_triagem_ano, 1),
        "custo_triagem_manual_ano_brl": round(custo_triagem_ano, 2),
        "cenarios_de_recuperacao": cenarios,
        "projecao_30k_tickets_ano": proj,
        "nota_metodologica": (
            "Volume (fato) x tempo por tarefa (premissa) x cobertura MEDIDA "
            "do classificador do script 03. Nao usa os campos de tempo do "
            "Dataset 1, que falharam na auditoria. O ganho e liquido: "
            "desconta o retrabalho gerado pelos proprios erros do modelo. "
            f"Projecao para 30.000 tickets/ano usa fator {fator:.2f}."),
    }


def main():
    d = carregar()
    resultado = {
        "a_onde_o_fluxo_trava": gargalos(d),
        "b_o_que_impacta_satisfacao": drivers_satisfacao(d),
        "c_quanto_desperdicamos": desperdicio(d),
    }
    destino = SAIDA / "diagnostico_operacional.json"
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False,
                                  default=str), encoding="utf-8")

    print("=" * 78)
    print("DIAGNOSTICO OPERACIONAL")
    print("=" * 78)

    g = resultado["a_onde_o_fluxo_trava"]
    print(f"\n[A] ONDE O FLUXO TRAVA  (n={g['n_tickets_com_tempo']}, "
          f"media geral {g['tempo_medio_geral_horas']}h)")
    print("\n  Piores combinacoes canal|prioridade|tipo:")
    for k, v in g["piores_5_combinacoes"].items():
        print(f"    {k:55s} media={v['media']:6.2f}h  n={int(v['n'])}")
    print("\n  Teste de significancia por dimensao:")
    for k, v in g["anova_por_dimensao"].items():
        marca = "SIGNIFICATIVO" if v["diferenca_significativa"] else "nao significativo"
        print(f"    {k:20s} F={v['F']:7.4f}  p={v['p']:.4f}  -> {marca}")
    print(f"\n  >> {g['leitura']}")

    c = resultado["b_o_que_impacta_satisfacao"]
    print(f"\n[B] O QUE IMPACTA SATISFACAO")
    print(f"    R2 treino={c['r2_treino']:.4f} | R2 teste={c['r2_teste']:.4f}")
    print(f"    MSE modelo={c['mse_modelo']:.4f} vs "
          f"baseline(media)={c['mse_baseline_media']:.4f} "
          f"-> ganho {c['ganho_sobre_baseline_pct']}%")
    print("    Top 5 variaveis por importancia de permutacao:")
    for k, v in list(c["top_10_variaveis"].items())[:5]:
        print(f"      {k:40s} {v:+.6f}")
    print(f"\n  >> {c['leitura']}")

    w = resultado["c_quanto_desperdicamos"]
    print(f"\n[C] QUANTO DESPERDICAMOS")
    print(f"    Volume: {w['volume_tickets']} tickets")
    print(f"    Triagem manual: {w['horas_triagem_manual_ano']}h/ano = "
          f"R$ {w['custo_triagem_manual_ano_brl']:,.2f}/ano")
    if not w["cenarios_de_recuperacao"]:
        print("    !! Rode 03_classificador.py primeiro para obter a "
              "cobertura medida.")
    else:
        print("    Cenarios (cobertura MEDIDA do classificador, ganho liquido):")
        for nome, v in w["cenarios_de_recuperacao"].items():
            print(f"      {nome:13s} limiar {v['limiar_confianca']:.2f} -> "
                  f"cobre {v['cobertura_medida_pct']:5.2f}% a "
                  f"{v['acuracia_no_automatizado_pct']:5.2f}% de acuracia | "
                  f"{v['horas_liquidas_mes']:6.1f}h/mes | "
                  f"R$ {v['economia_liquida_brl_ano']:>11,.2f}/ano | "
                  f"{v['equivalente_fte']} FTE")
        print("\n    Projecao para 30.000 tickets/ano:")
        for nome, v in w["projecao_30k_tickets_ano"].items():
            print(f"      {nome:13s} {v['horas_liquidas_ano']:>8.1f}h/ano | "
                  f"R$ {v['economia_liquida_brl_ano']:>12,.2f}/ano | "
                  f"{v['equivalente_fte']} FTE")

    print("\n" + "=" * 78)
    print(f"JSON salvo em: {destino}")
    print("=" * 78)


if __name__ == "__main__":
    main()
