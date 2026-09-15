"""
Mesa de Triagem - prototipo funcional
=====================================
Demonstra o fluxo proposto no item 2 do relatorio, rodando sobre o modelo
real treinado nos 47.837 tickets do Dataset 2.

Tres telas:
  1. Triagem      - cola o texto do ticket, recebe categoria + confianca +
                    decisao de roteamento (automatico ou humano)
  2. Lote         - roda sobre uma amostra real do dataset, nao sobre
                    exemplos escolhidos a dedo
  3. Calculadora  - o Diretor ajusta as premissas e ve o ROI recalcular

Uso:  streamlit run app.py
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from joblib import load

AQUI = Path(__file__).resolve()
SAIDA = AQUI.parents[1] / "outputs"
RAIZ_REPO = AQUI.parents[5]
DADOS = RAIZ_REPO / "datasets" / "raw"

st.set_page_config(page_title="Mesa de Triagem", page_icon="🎫",
                   layout="wide")


# ----------------------------------------------------------------- dados

@st.cache_resource
def carregar_modelo():
    caminho = SAIDA / "modelo_triagem.joblib"
    if not caminho.exists():
        return None
    return load(caminho)


@st.cache_data
def carregar_metricas():
    caminho = SAIDA / "classificador_metricas.json"
    if not caminho.exists():
        return None
    return json.loads(caminho.read_text(encoding="utf-8"))


@st.cache_data
def carregar_amostra(n=400):
    caminho = DADOS / "all_tickets_processed_improved_v3.csv"
    if not caminho.exists():
        return None
    d = pd.read_csv(caminho).dropna(subset=["Document", "Topic_group"])
    return d.sample(n=min(n, len(d)), random_state=7).reset_index(drop=True)


modelo = carregar_modelo()
metricas = carregar_metricas()

if modelo is None or metricas is None:
    st.error("Modelo nao encontrado. Rode antes:\n\n"
             "`python ../scripts/03_classificador.py`")
    st.stop()

CLASSES = list(modelo.named_steps["clf"].classes_)
CURVA = metricas["curva_cobertura_x_acuracia"]
POR_CLASSE = metricas["desempenho_por_classe"]

# Categorias que nunca sao roteadas sozinhas, independentemente da confianca.
# Justificativa no item 2 do relatorio: envolvem concessao de privilegio,
# decisao de gasto ou dado pessoal - onde o custo de errar e assimetrico.
SEMPRE_HUMANO = {"Administrative rights", "Purchase"}


def classificar(texto, limiar):
    proba = modelo.predict_proba([texto])[0]
    ordem = np.argsort(proba)[::-1]
    topo = CLASSES[ordem[0]]
    conf = float(proba[ordem[0]])

    if topo in SEMPRE_HUMANO:
        decisao, motivo = "HUMANO", f"categoria '{topo}' e de decisao sensivel"
    elif conf < limiar:
        decisao, motivo = "HUMANO", f"confianca {conf:.0%} abaixo do limiar {limiar:.0%}"
    else:
        decisao, motivo = "AUTOMATICO", f"confianca {conf:.0%} acima do limiar"

    return {
        "categoria": topo, "confianca": conf, "decisao": decisao,
        "motivo": motivo,
        "alternativas": [(CLASSES[i], float(proba[i])) for i in ordem[1:4]],
    }


@st.cache_data
def exemplos_reais():
    """Um ticket real de cada categoria, com o rotulo verdadeiro a vista.

    Preferir tickets reais a exemplos escritos para a demo: exemplo escrito
    a mao tende a conter as palavras que o autor acha que definem a classe,
    o que inflaciona artificialmente a confianca do modelo.
    """
    d = carregar_amostra(3000)
    if d is None:
        return {"(escrever manualmente)": ""}
    escolhidos = {"(escrever manualmente)": ""}
    for cat in sorted(d["Topic_group"].unique()):
        linha = d[d["Topic_group"] == cat].iloc[0]
        escolhidos[f"{cat} (rotulo real)"] = linha["Document"]
    return escolhidos


def termos_decisivos(texto, categoria, n=8):
    """Explicabilidade: quais palavras empurraram para esta categoria."""
    tfidf = modelo.named_steps["tfidf"]
    clf = modelo.named_steps["clf"]
    vetor = tfidf.transform([texto])
    idx_classe = list(clf.classes_).index(categoria)
    pesos = clf.coef_[idx_classe]
    nomes = tfidf.get_feature_names_out()
    contribs = [(nomes[j], vetor[0, j] * pesos[j])
                for j in vetor.nonzero()[1]]
    contribs.sort(key=lambda t: t[1], reverse=True)
    return contribs[:n]


# ------------------------------------------------------------------ UI

st.title("🎫 Mesa de Triagem")
st.caption("Classificacao e roteamento automatico de tickets · modelo "
           f"treinado em {metricas['configuracao']['n_treino']:,} tickets reais "
           f"· acuracia {metricas['desempenho_global']['acuracia_pct']}%"
           .replace(",", "."))

with st.sidebar:
    st.header("Configuracao")
    limiar = st.slider("Limiar de confianca para roteamento automatico",
                       0.50, 0.99, 0.80, 0.01,
                       help="Abaixo deste valor, o ticket vai para um humano.")

    ponto = min(CURVA, key=lambda r: abs(r["limiar_confianca"] - limiar))
    st.metric("Cobertura automatica", f"{ponto['cobertura_pct']:.1f}%")
    st.metric("Acuracia no automatizado",
              f"{ponto['acuracia_no_aceito_pct']:.2f}%")
    st.caption(f"A cada 1.000 tickets, ~{int(ponto['cobertura_pct'] * 10)} "
               f"sao roteados sozinhos e "
               f"~{round(ponto['cobertura_pct'] * 10 * (1 - ponto['acuracia_no_aceito_pct'] / 100))}"
               f" deles vao para a fila errada.")
    st.divider()
    st.caption("**Sempre humano**, qualquer confianca:\n\n"
               + "\n".join(f"- {c}" for c in sorted(SEMPRE_HUMANO)))

aba1, aba2, aba3 = st.tabs(["Triagem", "Lote (dados reais)",
                            "Calculadora de ROI"])

# ---------------------------------------------------------------- aba 1
with aba1:
    col_a, col_b = st.columns([3, 2])
    with col_a:
        exemplos = exemplos_reais()
        escolha = st.selectbox(
            "Carregar um ticket real do dataset", list(exemplos),
            help="Tickets sorteados do conjunto real, com o rotulo verdadeiro "
                 "entre parenteses. Nao sao exemplos escritos para a demo.")
        texto = st.text_area("Texto do ticket", value=exemplos[escolha],
                             height=180,
                             placeholder="Cole aqui o texto do chamado...")
        analisar = st.button("Classificar", type="primary")

    with col_b:
        if analisar and texto.strip():
            r = classificar(texto, limiar)
            if r["decisao"] == "AUTOMATICO":
                st.success(f"**{r['decisao']}** → fila *{r['categoria']}*")
            else:
                st.warning(f"**{r['decisao']}** → revisao manual")
            st.caption(f"Motivo: {r['motivo']}")
            st.metric("Categoria prevista", r["categoria"],
                      f"{r['confianca']:.1%} de confianca")

            st.write("**Outras hipoteses**")
            for cat, p in r["alternativas"]:
                st.write(f"- {cat} · {p:.1%}")

            st.write("**Por que esta categoria**")
            for termo, peso in termos_decisivos(texto, r["categoria"]):
                if peso > 0:
                    st.write(f"- `{termo}` (+{peso:.3f})")

            qualidade = POR_CLASSE.get(r["categoria"], {})
            if qualidade:
                st.caption(
                    f"Historico desta categoria no teste: precisao "
                    f"{qualidade['precision']:.1%} · recall "
                    f"{qualidade['recall']:.1%}")
        elif analisar:
            st.info("Cole o texto de um ticket.")

# ---------------------------------------------------------------- aba 2
with aba2:
    st.subheader("Simulacao sobre amostra real do dataset")
    st.caption("Amostra aleatoria (semente fixa) dos tickets reais — nao sao "
               "exemplos escolhidos a dedo. O rotulo verdadeiro esta na "
               "coluna final para conferencia.")

    amostra = carregar_amostra()
    if amostra is None:
        st.error("Dataset nao encontrado em datasets/raw/.")
    else:
        if st.button("Rodar triagem no lote", type="primary"):
            proba = modelo.predict_proba(amostra["Document"])
            previsto = np.array(CLASSES)[proba.argmax(axis=1)]
            conf = proba.max(axis=1)
            sensivel = np.isin(previsto, list(SEMPRE_HUMANO))
            auto = (conf >= limiar) & ~sensivel

            tabela = pd.DataFrame({
                "ticket": amostra["Document"].str.slice(0, 90) + "...",
                "previsto": previsto,
                "confianca": conf.round(3),
                "decisao": np.where(auto, "AUTOMATICO", "HUMANO"),
                "rotulo_real": amostra["Topic_group"],
                "acertou": previsto == amostra["Topic_group"],
            })

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tickets", len(tabela))
            c2.metric("Roteados sozinhos", f"{auto.mean():.1%}")
            acc_auto = tabela.loc[auto, "acertou"].mean() if auto.any() else 0
            c3.metric("Acuracia no automatico", f"{acc_auto:.1%}")
            c4.metric("Para humano", int((~auto).sum()))

            st.dataframe(tabela, use_container_width=True, height=420)

            st.write("**Distribuicao por fila**")
            st.bar_chart(tabela["previsto"].value_counts())

# ---------------------------------------------------------------- aba 3
with aba3:
    st.subheader("Quanto isso economiza")
    st.caption("Todas as premissas sao editaveis. Discorde de qualquer uma e "
               "o numero recalcula.")

    c1, c2, c3 = st.columns(3)
    volume = c1.number_input("Tickets por ano", 1_000, 500_000, 30_000, 1_000)
    custo_hora = c2.number_input("Custo/hora do agente (R$)", 10.0, 500.0,
                                 45.0, 5.0)
    min_triagem = c3.number_input("Minutos de triagem manual por ticket",
                                  0.5, 30.0, 4.0, 0.5)
    min_retrabalho = c1.number_input("Minutos de retrabalho por erro",
                                     1.0, 120.0, 12.0, 1.0)
    jornada = c2.number_input("Horas/mes por FTE", 100, 220, 168, 4)

    ponto = min(CURVA, key=lambda r: abs(r["limiar_confianca"] - limiar))
    cobertura = ponto["cobertura_pct"] / 100
    taxa_erro = 1 - ponto["acuracia_no_aceito_pct"] / 100

    horas_totais = volume * min_triagem / 60
    horas_brutas = horas_totais * cobertura
    horas_retrab = volume * cobertura * taxa_erro * min_retrabalho / 60
    horas_liq = horas_brutas - horas_retrab

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Custo atual da triagem",
              f"R$ {horas_totais * custo_hora:,.0f}/ano".replace(",", "."))
    m2.metric("Horas liquidas liberadas",
              f"{horas_liq:,.0f}/ano".replace(",", "."),
              f"-{horas_retrab:,.0f}h de retrabalho".replace(",", "."))
    m3.metric("Economia liquida",
              f"R$ {horas_liq * custo_hora:,.0f}/ano".replace(",", "."))
    m4.metric("Equivalente", f"{horas_liq / 12 / jornada:.2f} FTE")

    st.write("**Sensibilidade ao limiar** — mais automacao nao e linearmente "
             "melhor: acima de certo ponto, o erro consome o ganho.")
    linhas = []
    for r in CURVA:
        if r["limiar_confianca"] < 0.5:
            continue
        cob = r["cobertura_pct"] / 100
        err = 1 - r["acuracia_no_aceito_pct"] / 100
        hl = horas_totais * cob - volume * cob * err * min_retrabalho / 60
        linhas.append({"limiar": r["limiar_confianca"],
                       "cobertura_%": r["cobertura_pct"],
                       "acuracia_%": r["acuracia_no_aceito_pct"],
                       "horas_liquidas_ano": round(hl),
                       "economia_R$_ano": round(hl * custo_hora)})
    df = pd.DataFrame(linhas)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.line_chart(df.set_index("limiar")["economia_R$_ano"])
