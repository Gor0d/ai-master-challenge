"""
02 — Diagnóstico operacional (Dataset 1)
========================================
Responde as três perguntas do item 1 do brief:

  a) Onde o fluxo trava?       -> gargalos por canal × prioridade × tipo
  b) O que impacta satisfação? -> importância de variáveis sobre o CSAT
  c) Quanto desperdiçamos?     -> horas e custo, com premissas explícitas

Cada número vem acompanhado de teste de significância. Onde a diferença
entre grupos não é estatisticamente significativa, isso é dito — ranking
sem teste é ranking de ruído.

Convenção: identificadores em Python e chaves de JSON seguem sem acento
(as chaves são contrato entre os scripts e o protótipo); todo texto
destinado a leitura humana é escrito em português correto.

Uso:   python 02_diagnostico_operacional.py
Saída: outputs/diagnostico_operacional.json + relatório em stdout
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
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

# ---------------------------------------------------------------- premissas
# Explícitas e editáveis: o Diretor de Operações deve poder discordar de
# cada uma e recalcular. Nenhuma premissa está escondida no código.
PREMISSAS = {
    "custo_hora_agente_brl": 45.00,      # salário + encargos + infra
    "minutos_triagem_manual": 4.0,       # ler, categorizar, rotear
    "minutos_por_ticket_retrabalho": 12.0,  # custo de um roteamento errado
    "minutos_economia_sugestao_humano": 1.5,  # tempo poupado no ticket que
        # vai para humano mas chega com categoria sugerida + termos-chave —
        # não é o tempo de triagem inteiro (4 min), só a fração que a
        # sugestão do modelo substitui: ler o resumo em vez do ticket cru
    "jornada_horas_mes": 168,
    "fonte_premissas": ("Benchmarks de mercado para suporte N1 no Brasil. "
                        "Devem ser substituídos pelos números reais da "
                        "operação antes de qualquer decisão de investimento."),
}

ALFA = 0.05


def num_br(v, casas=0):
    """Formata número no padrão brasileiro: 1.234,56.

    Troca os dois separadores de uma vez. A versão anterior aplicava
    .replace(",", ".") sobre a frase inteira, o que trocava também as
    vírgulas do texto por pontos.
    """
    s = f"{v:,.{casas}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def num_br_sinal(v, casas=4):
    """Como num_br, mas com o sinal de menos tipográfico (−, U+2212).

    Os relatórios escrevem "R² de teste = −0,0525"; a saída do script deve
    usar a mesma notação, para que o número conferido na tela seja
    reconhecível no documento.
    """
    return ("−" + num_br(-v, casas)) if v < 0 else num_br(v, casas)


def carregar():
    d = pd.read_csv(DADOS / "customer_support_tickets.csv")
    frt = pd.to_datetime(d["First Response Time"], errors="coerce")
    ttr = pd.to_datetime(d["Time to Resolution"], errors="coerce")
    d["horas_resolucao"] = (ttr - frt).dt.total_seconds() / 3600
    return d


# ------------------------------------------------- a) onde o fluxo trava

def gargalos(d):
    """Ranking de combinações canal × prioridade × tipo por tempo médio."""
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

    # A diferença entre os grupos é real ou é flutuação amostral?
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
        return ("Nenhuma dimensão (canal, prioridade ou tipo) apresenta "
                "diferença estatisticamente significativa de tempo de "
                "resolução. O ranking acima existe, mas as diferenças estão "
                "dentro da flutuação amostral: não há gargalo identificável "
                "neste dataset. Priorizar o 'pior canal' seria agir sobre "
                "ruído.")
    return f"Dimensões com diferença significativa: {', '.join(sig)}."


# ------------------------------------------------- b) o que impacta CSAT

def drivers_satisfacao(d):
    """Importância de cada variável para prever o CSAT."""
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

    # baseline: prever sempre a média
    baseline_mse = float(((y_te - y_tr.mean()) ** 2).mean())
    modelo_mse = float(((y_te - modelo.predict(X_te)) ** 2).mean())

    # correlações diretas
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
        return (f"R² de teste = {num_br_sinal(r2_teste)} (negativo ou zero): "
                "o modelo "
                "prevê o CSAT PIOR do que simplesmente chutar a média. "
                "Nenhuma variável operacional disponível — canal, "
                "prioridade, tipo, tempo de resolução, idade ou gênero — tem "
                "poder preditivo sobre a satisfação neste dataset. A "
                "resposta honesta à pergunta 'o que impacta satisfação?' é: "
                "nada que esteja medido aqui. Ver laudo de auditoria.")
    return ("Variáveis com correlação significativa: "
            f"{', '.join(sig) or 'nenhuma'}.")


# ------------------------------------------------- c) quanto desperdiçamos

def _curva_medida():
    """Lê a curva cobertura × acurácia produzida pelo script 03.

    Este é o cruzamento entre os dois datasets: a taxa de automação não é
    estimada, é a cobertura MEDIDA do classificador treinado no Dataset 2,
    aplicada ao volume de tickets do Dataset 1.
    """
    arq = SAIDA / "classificador_metricas.json"
    if not arq.exists():
        return None
    dados = json.loads(arq.read_text(encoding="utf-8"))
    return dados["curva_cobertura_x_acuracia"]


def desperdicio(d):
    """Horas e custo de triagem manual, e quanto é recuperável.

    O cálculo NÃO depende dos timestamps do Dataset 1 (que são inválidos).
    Depende de volume — fato verificável — e de premissas de tempo por
    tarefa, explícitas e ajustáveis. A taxa de automação vem medida do
    classificador, não arbitrada.
    """
    n_tickets = int(len(d))
    p = PREMISSAS
    horas_triagem_ano = n_tickets * p["minutos_triagem_manual"] / 60
    custo_triagem_ano = horas_triagem_ano * p["custo_hora_agente_brl"]

    curva = _curva_medida()
    cenarios = {}
    if curva:
        # três pontos de operação reais da curva, do mais cauteloso ao
        # mais agressivo
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
            horas_liquidas_automacao = horas_brutas - horas_retrabalho

            # os tickets que vão para humano também ganham tempo: chegam
            # com categoria sugerida + termos-chave, não do zero
            n_para_humano = n_tickets * (1 - cobertura)
            horas_assistidas = (n_para_humano
                                * p["minutos_economia_sugestao_humano"] / 60)

            horas_liquidas = horas_liquidas_automacao + horas_assistidas
            cenarios[nome] = {
                "limiar_confianca": limiar,
                "cobertura_medida_pct": r["cobertura_pct"],
                "acuracia_no_automatizado_pct": r["acuracia_no_aceito_pct"],
                "horas_brutas_liberadas_ano": round(horas_brutas, 1),
                "horas_perdidas_em_retrabalho_ano": round(horas_retrabalho, 1),
                "horas_liquidas_automacao_ano": round(horas_liquidas_automacao, 1),
                "horas_assistidas_ano": round(horas_assistidas, 1),
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
            "Volume (fato) × tempo por tarefa (premissa) × cobertura MEDIDA "
            "do classificador do script 03. Não usa os campos de tempo do "
            "Dataset 1, que falharam na auditoria. O ganho é líquido: "
            "desconta o retrabalho gerado pelos próprios erros do modelo. "
            "Inclui também o ganho parcial nos tickets NÃO automatizados "
            "(chegam ao humano com categoria sugerida, não do zero) — "
            f"{p['minutos_economia_sugestao_humano']} min/ticket, uma "
            "fração pequena e conservadora dos 4 min de triagem manual. "
            f"A projeção para 30.000 tickets/ano usa o fator "
            f"{num_br(fator, 2)}."),
    }


def sensibilidade_custo_hora(desp, valores=(30.0, 45.0, 60.0)):
    """O ROI escala linearmente com a premissa de custo/hora do agente.

    Isto NÃO é uma medição — é para deixar explícito o quanto a conclusão
    depende de uma premissa que o Diretor deve substituir pelo número real
    da folha antes de decidir investimento.
    """
    base_valor = desp["premissas"]["custo_hora_agente_brl"]
    linhas = {}
    for v in valores:
        fator = v / base_valor
        linhas[f"R$ {v:.0f}/h"] = {
            nome: round(c["economia_liquida_brl_ano"] * fator, 2)
            for nome, c in desp["projecao_30k_tickets_ano"].items()
        }
    return {
        "premissa_base_brl_hora": base_valor,
        "economia_recomendada_por_valor_hora": linhas,
        "nota": ("Escala linear: dobrar o custo/hora dobra a economia. Use "
                 "o número real da operação, não o benchmark, antes de "
                 "decidir investimento."),
    }


def custo_implantacao_e_payback(desp):
    """Estimativa de custo de implantar a triagem automática e o tempo de
    retorno, no cenário recomendado (limiar 0,80) projetado para 30 mil
    tickets/ano.

    Toda premissa de custo de implantação aqui é ESTIMATIVA, marcada como
    tal — não é medição de projeto real. A fase de sombra (rodar o modelo
    em paralelo, sem rotear nada) custa perto de zero porque não integra
    nada em produção: é só inferência em lote sobre tickets que já existem.
    """
    custos = {
        "fase_sombra_brl": 0.0,  # sem integração, roda em paralelo, custo ~nulo
        "integracao_e_deploy_brl": 12000.0,  # ~80h de engenharia a R$ 150/h
        "retreino_mensal_recorrente_brl_mes": 600.0,  # ~4h/mês de manutenção
    }
    economia_recomendada = desp["projecao_30k_tickets_ano"]["recomendado"]
    economia_mensal = economia_recomendada["economia_liquida_brl_ano"] / 12
    economia_mensal_liquida_manutencao = (economia_mensal
                                          - custos["retreino_mensal_recorrente_brl_mes"])
    payback_meses = (custos["integracao_e_deploy_brl"]
                     / economia_mensal_liquida_manutencao)
    return {
        "custos_estimados": custos,
        "nota_metodologica": ("Estimativas de esforço de engenharia, não "
                              "orçamento medido. Ajustar ao custo real de "
                              "TI/dados da operação antes de aprovar."),
        "economia_liquida_mensal_apos_manutencao_brl": round(
            economia_mensal_liquida_manutencao, 2),
        "payback_meses": round(payback_meses, 1),
        "leitura": (
            "Com integração estimada em R$ "
            f"{num_br(custos['integracao_e_deploy_brl'])} e manutenção de "
            f"R$ {num_br(custos['retreino_mensal_recorrente_brl_mes'])}/mês, "
            f"o investimento se paga em ~{num_br(payback_meses, 1)} meses no "
            "cenário recomendado. A fase de sombra (2 a 4 semanas) não tem "
            "custo de integração, porque valida a acurácia antes de qualquer "
            "investimento em deploy."
        ),
    }


def main():
    d = carregar()
    desp = desperdicio(d)
    resultado = {
        "a_onde_o_fluxo_trava": gargalos(d),
        "b_o_que_impacta_satisfacao": drivers_satisfacao(d),
        "c_quanto_desperdicamos": desp,
        "d_sensibilidade_custo_hora": sensibilidade_custo_hora(desp),
        "e_custo_implantacao_e_payback": custo_implantacao_e_payback(desp),
    }
    destino = SAIDA / "diagnostico_operacional.json"
    destino.write_text(json.dumps(resultado, indent=2, ensure_ascii=False,
                                  default=str), encoding="utf-8")

    print("=" * 78)
    print("DIAGNÓSTICO OPERACIONAL")
    print("=" * 78)

    g = resultado["a_onde_o_fluxo_trava"]
    print(f"\n[A] ONDE O FLUXO TRAVA  (n={g['n_tickets_com_tempo']}, "
          f"média geral {num_br(g['tempo_medio_geral_horas'], 2)}h)")
    print("\n  Piores combinações canal | prioridade | tipo:")
    for k, v in g["piores_5_combinacoes"].items():
        print(f"    {k:55s} média={v['media']:6.2f}h  n={int(v['n'])}")
    print("\n  Teste de significância por dimensão:")
    for k, v in g["anova_por_dimensao"].items():
        marca = ("SIGNIFICATIVO" if v["diferenca_significativa"]
                 else "não significativo")
        print(f"    {k:20s} F={v['F']:7.4f}  p={v['p']:.4f}  -> {marca}")
    print(f"\n  >> {g['leitura']}")

    c = resultado["b_o_que_impacta_satisfacao"]
    print("\n[B] O QUE IMPACTA A SATISFAÇÃO")
    print(f"    R² treino={num_br_sinal(c['r2_treino'])} | "
          f"R² teste={num_br_sinal(c['r2_teste'])}")
    print(f"    MSE do modelo={num_br(c['mse_modelo'], 4)} vs. "
          f"baseline (média)={num_br(c['mse_baseline_media'], 4)} "
          f"-> ganho {num_br_sinal(c['ganho_sobre_baseline_pct'], 2)}%")
    print("    Top 5 variáveis por importância de permutação:")
    for k, v in list(c["top_10_variaveis"].items())[:5]:
        print(f"      {k:40s} {v:+.6f}")
    print(f"\n  >> {c['leitura']}")

    w = resultado["c_quanto_desperdicamos"]
    print("\n[C] QUANTO DESPERDIÇAMOS")
    print(f"    Volume: {num_br(w['volume_tickets'])} tickets")
    print(f"    Triagem manual: {num_br(w['horas_triagem_manual_ano'], 1)}h/ano "
          f"= R$ {num_br(w['custo_triagem_manual_ano_brl'], 2)}/ano")
    if not w["cenarios_de_recuperacao"]:
        print("    !! Rode 03_classificador.py primeiro para obter a "
              "cobertura medida.")
    else:
        print("    Cenários (cobertura MEDIDA do classificador, ganho "
              "líquido):")
        for nome, v in w["cenarios_de_recuperacao"].items():
            print(f"      {nome:13s} limiar {v['limiar_confianca']:.2f} -> "
                  f"cobre {v['cobertura_medida_pct']:5.2f}% a "
                  f"{v['acuracia_no_automatizado_pct']:5.2f}% de acurácia | "
                  f"{v['horas_liquidas_mes']:6.1f}h/mês | "
                  f"R$ {num_br(v['economia_liquida_brl_ano'], 2):>12}/ano | "
                  f"{num_br(v['equivalente_fte'], 2)} FTE")
        print("\n    Projeção para 30.000 tickets/ano:")
        for nome, v in w["projecao_30k_tickets_ano"].items():
            print(f"      {nome:13s} "
                  f"{num_br(v['horas_liquidas_ano'], 1):>9}h/ano | "
                  f"R$ {num_br(v['economia_liquida_brl_ano'], 2):>12}/ano | "
                  f"{num_br(v['equivalente_fte'], 2)} FTE")

    s = resultado["d_sensibilidade_custo_hora"]
    print("\n[D] SENSIBILIDADE AO CUSTO/HORA "
          f"(base: R$ {s['premissa_base_brl_hora']:.0f}/h)")
    for valor_hora, cenarios in s["economia_recomendada_por_valor_hora"].items():
        print(f"    {valor_hora:>10s} -> economia recomendada "
              f"R$ {num_br(cenarios['recomendado'], 2):>12}/ano")

    pb = resultado["e_custo_implantacao_e_payback"]
    print("\n[E] CUSTO DE IMPLANTAÇÃO E PAYBACK")
    print("    Integração e deploy (estimativa): R$ "
          f"{num_br(pb['custos_estimados']['integracao_e_deploy_brl'], 2)}")
    print("    Manutenção/retreino: R$ "
          f"{num_br(pb['custos_estimados']['retreino_mensal_recorrente_brl_mes'], 2)}"
          "/mês")
    print("    Economia líquida após manutenção: R$ "
          f"{num_br(pb['economia_liquida_mensal_apos_manutencao_brl'], 2)}/mês")
    print(f"    Payback estimado: {num_br(pb['payback_meses'], 1)} meses")

    print("\n" + "=" * 78)
    print(f"JSON salvo em: {destino}")
    print("=" * 78)


if __name__ == "__main__":
    main()
