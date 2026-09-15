"""
01 - Auditoria de integridade dos datasets
==========================================
Antes de diagnosticar a operacao, e preciso saber se os dados sustentam
qualquer conclusao. Este script executa seis testes independentes de
integridade sobre o Dataset 1 (customer_support_tickets.csv) e um perfil
de qualidade sobre o Dataset 2 (all_tickets_processed_improved_v3.csv).

Conclusao (reproduzivel abaixo): as metricas operacionais do Dataset 1 sao
ruido gerado aleatoriamente. Os campos estruturais sobrevivem.

Uso:   python 01_auditoria_integridade.py
Saida: outputs/auditoria_resultados.json  +  relatorio em stdout
"""
import json
from pathlib import Path

import pandas as pd
from scipy import stats

AQUI = Path(__file__).resolve()
RAIZ_REPO = AQUI.parents[4]
DADOS = RAIZ_REPO / "datasets" / "raw"
SAIDA = AQUI.parents[1] / "outputs"
SAIDA.mkdir(parents=True, exist_ok=True)

ALFA = 0.05  # nivel de significancia para todos os testes


def carregar():
    ds1 = pd.read_csv(DADOS / "customer_support_tickets.csv")
    ds2 = pd.read_csv(DADOS / "all_tickets_processed_improved_v3.csv")
    return ds1, ds2


def _deltas_horas(ds1):
    """Horas entre primeira resposta e resolucao. Negativo = impossivel."""
    frt = pd.to_datetime(ds1["First Response Time"], errors="coerce")
    ttr = pd.to_datetime(ds1["Time to Resolution"], errors="coerce")
    return frt, ttr, (ttr - frt).dt.total_seconds() / 3600


# ---------------------------------------------------------------- testes DS1

def teste_1_placeholders(ds1):
    """Texto real de cliente nao contem placeholders de template."""
    desc = ds1["Ticket Description"].fillna("")
    com_ph = desc.str.contains(r"\{[a-z_]+\}", regex=True)
    normalizado = desc.str.replace(r"\{[a-z_]+\}", "X", regex=True)
    return {
        "nome": "Placeholders nao substituidos no texto",
        "pct_descricoes_com_placeholder": round(float(com_ph.mean()) * 100, 2),
        "n_descricoes": int(len(desc)),
        "templates_unicos_apos_normalizar": int(normalizado.nunique()),
        "esperado_se_real": "0% de placeholders",
        "veredito": "SINTETICO" if com_ph.mean() > 0.5 else "ok",
    }


def teste_2_janela_temporal(ds1):
    """Uma operacao real espalha tickets ao longo de meses."""
    frt, ttr, _ = _deltas_horas(ds1)
    todos = pd.concat([frt, ttr]).dropna()
    span_h = (todos.max() - todos.min()).total_seconds() / 3600
    return {
        "nome": "Janela temporal de todos os timestamps",
        "inicio": str(todos.min()),
        "fim": str(todos.max()),
        "amplitude_horas": round(span_h, 2),
        "n_tickets": int(len(ds1)),
        "esperado_se_real": "meses ou anos de amplitude",
        "veredito": "SINTETICO" if span_h < 24 * 30 else "ok",
    }


def teste_3_causalidade_temporal(ds1):
    """Resolucao nao pode anteceder a primeira resposta."""
    _, _, delta = _deltas_horas(ds1)
    validos = delta.notna()
    negativos = (delta < 0) & validos
    return {
        "nome": "Resolucao anterior a primeira resposta (impossivel)",
        "n_pares_validos": int(validos.sum()),
        "n_negativos": int(negativos.sum()),
        "pct_negativos": round(float(negativos.sum()) / int(validos.sum()) * 100, 2),
        "delta_medio_horas": round(float(delta[validos].mean()), 4),
        "esperado_se_real": "0% negativos e delta medio positivo",
        "veredito": "SINTETICO" if negativos.sum() / validos.sum() > 0.05 else "ok",
    }


def teste_4_uniformidade_csat(ds1):
    """CSAT real e enviesado (curva J), nunca uniforme."""
    csat = ds1["Customer Satisfaction Rating"].dropna()
    contagem = csat.value_counts().sort_index()
    chi2, p = stats.chisquare(contagem.values)
    return {
        "nome": "Uniformidade da distribuicao de CSAT",
        "contagem_por_nota": {str(k): int(v) for k, v in contagem.items()},
        "chi2_vs_uniforme": round(float(chi2), 4),
        "p_valor": round(float(p), 4),
        "interpretacao": "p alto = indistinguivel de sorteio uniforme",
        "esperado_se_real": "p < 0.05 (distribuicao enviesada)",
        "veredito": "SINTETICO" if p > ALFA else "ok",
    }


def teste_5_ausencia_de_sinal(ds1):
    """Em operacao real, tempo de resolucao e canal afetam satisfacao."""
    _, _, delta = _deltas_horas(ds1)
    d = ds1.assign(delta_h=delta)
    sub = d.dropna(subset=["Customer Satisfaction Rating", "delta_h"])

    r, p_r = stats.pearsonr(sub["delta_h"], sub["Customer Satisfaction Rating"])
    grupos = [g["Customer Satisfaction Rating"].dropna().values
              for _, g in d.groupby("Ticket Channel")]
    f_stat, p_anova = stats.f_oneway(*grupos)

    associacoes = {}
    for a, b in [("Ticket Channel", "Ticket Priority"),
                 ("Ticket Type", "Ticket Priority"),
                 ("Ticket Channel", "Ticket Type")]:
        chi2, p_chi, _, _ = stats.chi2_contingency(pd.crosstab(d[a], d[b]))
        associacoes[f"{a} x {b}"] = {"chi2": round(float(chi2), 2),
                                     "p": round(float(p_chi), 4)}

    medias = d.groupby("Ticket Channel")["Customer Satisfaction Rating"].mean()
    return {
        "nome": "Ausencia de sinal entre variaveis operacionais e CSAT",
        "pearson_csat_x_tempo_resolucao": {"r": round(float(r), 4),
                                           "p": round(float(p_r), 4),
                                           "n": int(len(sub))},
        "anova_csat_por_canal": {"F": round(float(f_stat), 4),
                                 "p": round(float(p_anova), 4)},
        "qui_quadrado_independencia": associacoes,
        "csat_medio_por_canal": {k: round(float(v), 4) for k, v in medias.items()},
        "amplitude_csat_medio": round(float(medias.max() - medias.min()), 4),
        "esperado_se_real": "ao menos uma associacao significativa (p < 0.05)",
        "veredito": "SINTETICO" if (p_r > ALFA and p_anova > ALFA) else "ok",
    }


def teste_6_completude(ds1):
    """Este teste NAO condena: mede o que sobra de aproveitavel."""
    n = len(ds1)
    nulos = ds1.isna().sum()
    fechados = int((ds1["Ticket Status"] == "Closed").sum())
    return {
        "nome": "Completude e composicao do backlog",
        "n_registros": int(n),
        "n_registros_prometido_no_brief": 30000,
        "divergencia_vs_brief": int(30000 - n),
        "campos_com_nulos": {c: int(v) for c, v in nulos.items() if v > 0},
        "tickets_fechados": fechados,
        "pct_nunca_fechados": round((n - fechados) / n * 100, 2),
        "observacao": ("Resolution, Time to Resolution e CSAT tem exatamente o "
                       "mesmo numero de nulos: so existem para tickets Closed."),
        "veredito": "ESTRUTURAL_APROVEITAVEL",
    }


# ---------------------------------------------------------------- perfil DS2

def perfil_ds2(ds2):
    contagem = ds2["Topic_group"].value_counts()
    palavras = ds2["Document"].fillna("").str.split().str.len()
    com_ph = ds2["Document"].fillna("").str.contains(r"\{[a-z_]+\}", regex=True)
    return {
        "nome": "Perfil de qualidade do Dataset 2",
        "n_registros": int(len(ds2)),
        "n_registros_prometido_no_brief": 48000,
        "n_classes": int(len(contagem)),
        "distribuicao_classes": {str(k): int(v) for k, v in contagem.items()},
        "razao_desbalanceamento": round(float(contagem.max() / contagem.min()), 2),
        "pct_com_placeholder": round(float(com_ph.mean()) * 100, 2),
        "duplicatas_exatas": int(ds2["Document"].duplicated().sum()),
        "palavras_por_ticket": {
            "media": round(float(palavras.mean()), 1),
            "mediana": float(palavras.median()),
            "p25": float(palavras.quantile(0.25)),
            "p75": float(palavras.quantile(0.75)),
            "max": int(palavras.max()),
        },
        "veredito": "REAL_UTILIZAVEL",
    }


def main():
    ds1, ds2 = carregar()
    testes = [teste_1_placeholders(ds1), teste_2_janela_temporal(ds1),
              teste_3_causalidade_temporal(ds1), teste_4_uniformidade_csat(ds1),
              teste_5_ausencia_de_sinal(ds1), teste_6_completude(ds1)]
    ds2_perfil = perfil_ds2(ds2)
    condenatorios = [t for t in testes if t["veredito"] == "SINTETICO"]

    resultado = {
        "dataset_1": {
            "arquivo": "customer_support_tickets.csv",
            "testes": testes,
            "n_testes_condenatorios": len(condenatorios),
            "conclusao": ("Metricas operacionais (tempos, CSAT) sao ruido "
                          "aleatorio. Campos estruturais (canal, tipo, produto, "
                          "status) sao aproveitaveis para analise de composicao."),
        },
        "dataset_2": ds2_perfil,
    }

    destino = SAIDA / "auditoria_resultados.json"
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False),
                       encoding="utf-8")

    print("=" * 78)
    print("AUDITORIA DE INTEGRIDADE - RESULTADO")
    print("=" * 78)
    for t in testes + [ds2_perfil]:
        print(f"\n[{t['veredito']:>22}]  {t['nome']}")
        for k, v in t.items():
            if k not in ("nome", "veredito"):
                print(f"     {k}: {v}")
    print("\n" + "=" * 78)
    print(f"VEREDITO: {len(condenatorios)}/6 testes condenam o Dataset 1.")
    print(f"JSON salvo em: {destino}")
    print("=" * 78)


if __name__ == "__main__":
    main()
