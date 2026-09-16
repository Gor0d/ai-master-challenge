"""
01 — Auditoria de integridade dos datasets
==========================================
Antes de diagnosticar a operação, é preciso saber se os dados sustentam
qualquer conclusão. Este script executa nove testes independentes de
integridade sobre o Dataset 1 (customer_support_tickets.csv) e um perfil
de qualidade sobre o Dataset 2 (all_tickets_processed_improved_v3.csv).

Conclusão (reproduzível abaixo): 8 dos 9 testes condenam o Dataset 1. Ele
foi gerado integralmente pela biblioteca Faker — assinatura confirmada
pelos domínios RFC 2606 em 100% dos e-mails e pelo vocabulário aleatório
do campo Resolution. Não são apenas as métricas: TODAS as categóricas são
uniformes, portanto nem a composição de volume por canal/tipo/produto tem
informação. Nenhum KPI operacional pode ser derivado deste arquivo.

O Dataset 2, ao contrário, é real e sustenta a solução quantitativa.

Convenção: identificadores em Python e chaves de JSON seguem sem acento
(as chaves são contrato entre os scripts e o protótipo); todo texto
destinado a leitura humana é escrito em português correto.

Uso:   python 01_auditoria_integridade.py
Saída: outputs/auditoria_resultados.json  +  relatório em stdout
"""
import json
import sys
from pathlib import Path

import pandas as pd
from scipy import stats

# O relatório em stdout é acentuado e o console do Windows usa cp1252 por
# padrão, o que levantaria UnicodeEncodeError. Reconfigurar aqui evita
# depender de PYTHONIOENCODING ou do modo -X utf8 na linha de comando.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = Path(__file__).resolve()
RAIZ_REPO = AQUI.parents[4]
DADOS = RAIZ_REPO / "datasets" / "raw"
SAIDA = AQUI.parents[1] / "outputs"
SAIDA.mkdir(parents=True, exist_ok=True)

ALFA = 0.05  # nível de significância para todos os testes

# Vereditos possíveis. Constantes em vez de literais repetidos: o valor é
# comparado no fim do script, e uma divergência de grafia passaria calada.
SINTETICO = "SINTÉTICO"
OK = "ok"
CONTEXTO = "CONTEXTO"
REAL_UTILIZAVEL = "REAL_UTILIZÁVEL"


def carregar():
    ds1 = pd.read_csv(DADOS / "customer_support_tickets.csv")
    ds2 = pd.read_csv(DADOS / "all_tickets_processed_improved_v3.csv")
    return ds1, ds2


def _deltas_horas(ds1):
    """Horas entre primeira resposta e resolução. Negativo = impossível."""
    frt = pd.to_datetime(ds1["First Response Time"], errors="coerce")
    ttr = pd.to_datetime(ds1["Time to Resolution"], errors="coerce")
    return frt, ttr, (ttr - frt).dt.total_seconds() / 3600


# ---------------------------------------------------------------- testes DS1

def teste_1_placeholders(ds1):
    """Texto real de cliente não contém placeholders de template."""
    desc = ds1["Ticket Description"].fillna("")
    com_ph = desc.str.contains(r"\{[a-z_]+\}", regex=True)
    normalizado = desc.str.replace(r"\{[a-z_]+\}", "X", regex=True)
    return {
        "nome": "Placeholders não substituídos no texto",
        "pct_descricoes_com_placeholder": round(float(com_ph.mean()) * 100, 2),
        "n_descricoes": int(len(desc)),
        "templates_unicos_apos_normalizar": int(normalizado.nunique()),
        "esperado_se_real": "0% de placeholders",
        "veredito": SINTETICO if com_ph.mean() > 0.5 else OK,
    }


def teste_2_janela_temporal(ds1):
    """Uma operação real espalha tickets ao longo de meses."""
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
        "veredito": SINTETICO if span_h < 24 * 30 else OK,
    }


def teste_3_causalidade_temporal(ds1):
    """Resolução não pode anteceder a primeira resposta."""
    _, _, delta = _deltas_horas(ds1)
    validos = delta.notna()
    negativos = (delta < 0) & validos
    return {
        "nome": "Resolução anterior à primeira resposta (impossível)",
        "n_pares_validos": int(validos.sum()),
        "n_negativos": int(negativos.sum()),
        "pct_negativos": round(float(negativos.sum()) / int(validos.sum()) * 100, 2),
        "delta_medio_horas": round(float(delta[validos].mean()), 4),
        "esperado_se_real": "0% negativos e delta médio positivo",
        "veredito": SINTETICO if negativos.sum() / validos.sum() > 0.05 else OK,
    }


def teste_4_uniformidade_csat(ds1):
    """CSAT real é enviesado (curva J), nunca uniforme."""
    csat = ds1["Customer Satisfaction Rating"].dropna()
    contagem = csat.value_counts().sort_index()
    chi2, p = stats.chisquare(contagem.values)
    return {
        "nome": "Uniformidade da distribuição de CSAT",
        "contagem_por_nota": {str(k): int(v) for k, v in contagem.items()},
        "chi2_vs_uniforme": round(float(chi2), 4),
        "p_valor": round(float(p), 4),
        "interpretacao": "p alto = indistinguível de sorteio uniforme",
        "esperado_se_real": "p < 0,05 (distribuição enviesada)",
        "veredito": SINTETICO if p > ALFA else OK,
    }


def teste_5_ausencia_de_sinal(ds1):
    """Em operação real, tempo de resolução e canal afetam a satisfação."""
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
        "nome": "Ausência de sinal entre variáveis operacionais e CSAT",
        "pearson_csat_x_tempo_resolucao": {"r": round(float(r), 4),
                                           "p": round(float(p_r), 4),
                                           "n": int(len(sub))},
        "anova_csat_por_canal": {"F": round(float(f_stat), 4),
                                 "p": round(float(p_anova), 4)},
        "qui_quadrado_independencia": associacoes,
        "csat_medio_por_canal": {k: round(float(v), 4) for k, v in medias.items()},
        "amplitude_csat_medio": round(float(medias.max() - medias.min()), 4),
        "esperado_se_real": "ao menos uma associação significativa (p < 0,05)",
        "veredito": SINTETICO if (p_r > ALFA and p_anova > ALFA) else OK,
    }


def teste_6_dominios_email(ds1):
    """example.com/org/net são reservados pela RFC 2606 e são o padrão do Faker."""
    dominios = ds1["Customer Email"].str.split("@").str[1]
    reservados = dominios.isin(["example.com", "example.org", "example.net"])
    return {
        "nome": "Domínios de e-mail reservados (assinatura do Faker)",
        "distribuicao_dominios": {str(k): int(v)
                                  for k, v in dominios.value_counts().items()},
        "pct_dominios_reservados_rfc2606": round(float(reservados.mean()) * 100, 2),
        "esperado_se_real": "domínios variados de provedores reais",
        "veredito": SINTETICO if reservados.mean() > 0.5 else OK,
    }


def teste_7_vocabulario_resolucao(ds1):
    """O campo Resolution deveria conter linguagem de atendimento."""
    res = ds1["Resolution"].dropna()
    palavras = pd.Series(" ".join(res).lower().replace(".", "").split())
    termos = ["refund", "replace", "ticket", "resolved", "reset",
              "support", "customer", "issue", "account"]
    ocorrencias = {t: int(palavras.eq(t).sum()) for t in termos}
    ausentes = [t for t, n in ocorrencias.items() if n == 0]
    return {
        "nome": "Vocabulário do campo Resolution",
        "n_resolucoes": int(len(res)),
        "palavras_unicas": int(palavras.nunique()),
        "top_10_palavras": {str(k): int(v)
                            for k, v in palavras.value_counts().head(10).items()},
        "ocorrencias_termos_de_suporte": ocorrencias,
        "termos_com_zero_ocorrencias": ausentes,
        "amostras": res.head(3).tolist(),
        "esperado_se_real": "vocabulário dominado por termos de atendimento",
        "veredito": SINTETICO if len(ausentes) >= 3 else OK,
    }


def teste_8_uniformidade_categoricas(ds1):
    """Se TODA categórica for uniforme, não há nem composição aproveitável."""
    colunas = ["Ticket Channel", "Ticket Priority", "Ticket Type",
               "Ticket Status", "Product Purchased", "Ticket Subject"]
    # Bonferroni: 6 testes simultâneos
    alfa_corrigido = ALFA / len(colunas)
    resultados = {}
    uniformes = 0
    for c in colunas:
        vc = ds1[c].value_counts()
        chi2, p = stats.chisquare(vc.values)
        eh_uniforme = p > alfa_corrigido
        uniformes += eh_uniforme
        resultados[c] = {"k_categorias": int(len(vc)),
                         "chi2": round(float(chi2), 2),
                         "p": round(float(p), 4),
                         "uniforme": bool(eh_uniforme)}
    return {
        "nome": "Uniformidade de TODAS as categóricas (chi2 vs. uniforme)",
        "alfa_bonferroni": round(alfa_corrigido, 5),
        "resultados": resultados,
        "n_colunas_uniformes": int(uniformes),
        "n_colunas_testadas": len(colunas),
        "implicacao": ("Categóricas uniformes = nem a composição de volume "
                       "por canal/tipo/produto carrega informação. O dataset "
                       "não sustenta sequer análise descritiva de mix."),
        "esperado_se_real": "mix desbalanceado (lei de Pareto no suporte)",
        "veredito": SINTETICO if uniformes == len(colunas) else OK,
    }


def teste_9_completude(ds1):
    """Este teste NÃO condena: mede o que sobra de aproveitável."""
    n = len(ds1)
    nulos = ds1.isna().sum()
    fechados = int((ds1["Ticket Status"] == "Closed").sum())
    return {
        "nome": "Completude e composição do backlog",
        "n_registros": int(n),
        "n_registros_prometido_no_brief": 30000,
        "divergencia_vs_brief": int(30000 - n),
        "campos_com_nulos": {c: int(v) for c, v in nulos.items() if v > 0},
        "tickets_fechados": fechados,
        "pct_nunca_fechados": round((n - fechados) / n * 100, 2),
        "observacao": ("Resolution, Time to Resolution e CSAT têm exatamente "
                       "o mesmo número de nulos: só existem para tickets "
                       "Closed. ATENÇÃO: como Ticket Status também é uniforme "
                       "(teste 8), os 67,3% 'nunca fechados' NÃO representam "
                       "um backlog real — é 1/3 por status atribuído "
                       "aleatoriamente."),
        "veredito": CONTEXTO,
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
        "veredito": REAL_UTILIZAVEL,
    }


def main():
    ds1, ds2 = carregar()
    testes = [teste_1_placeholders(ds1), teste_2_janela_temporal(ds1),
              teste_3_causalidade_temporal(ds1), teste_4_uniformidade_csat(ds1),
              teste_5_ausencia_de_sinal(ds1), teste_6_dominios_email(ds1),
              teste_7_vocabulario_resolucao(ds1),
              teste_8_uniformidade_categoricas(ds1), teste_9_completude(ds1)]
    ds2_perfil = perfil_ds2(ds2)
    condenatorios = [t for t in testes if t["veredito"] == SINTETICO]

    resultado = {
        "dataset_1": {
            "arquivo": "customer_support_tickets.csv",
            "testes": testes,
            "n_testes_condenatorios": len(condenatorios),
            "conclusao": ("Dataset integralmente gerado por biblioteca de "
                          "dados falsos (assinatura do Faker confirmada). "
                          "Não apenas as métricas: TODAS as categóricas são "
                          "uniformes, então nem a composição de volume por "
                          "canal/tipo/produto carrega informação. Nenhum KPI "
                          "operacional pode ser derivado deste arquivo."),
        },
        "dataset_2": ds2_perfil,
    }

    destino = SAIDA / "auditoria_resultados.json"
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False),
                       encoding="utf-8")

    print("=" * 78)
    print("AUDITORIA DE INTEGRIDADE — RESULTADO")
    print("=" * 78)
    for t in testes + [ds2_perfil]:
        print(f"\n[{t['veredito']:>22}]  {t['nome']}")
        for k, v in t.items():
            if k not in ("nome", "veredito"):
                print(f"     {k}: {v}")
    print("\n" + "=" * 78)
    print(f"VEREDITO: {len(condenatorios)}/{len(testes)} testes condenam "
          "o Dataset 1.")
    print(f"JSON salvo em: {destino}")
    print("=" * 78)


if __name__ == "__main__":
    main()
