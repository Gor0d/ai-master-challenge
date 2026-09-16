"""
Mesa de Triagem — protótipo funcional
=====================================
Demonstra o fluxo proposto no item 2 do relatório, rodando sobre o modelo
real treinado nos 47.837 tickets do Dataset 2.

Três telas:
  1. Triagem      — cola o texto do ticket, recebe categoria + confiança +
                    decisão de roteamento (automático ou humano)
  2. Lote         — roda sobre uma amostra real do dataset, não sobre
                    exemplos escolhidos a dedo
  3. Calculadora  — o Diretor ajusta as premissas e vê o ROI recalcular

Convenção: identificadores em Python seguem sem acento (padrão da
linguagem); todo texto destinado a leitura humana é escrito em português
correto.

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
# submissions/<nome>/solution/app/app.py -> parents[4] é a raiz do repo,
# o mesmo índice usado pelos scripts. Manter alinhado: é daqui que sai o
# caminho dos CSVs usados pela aba de lote e pelos exemplos reais.
RAIZ_REPO = AQUI.parents[4]
DADOS = RAIZ_REPO / "datasets" / "raw"

st.set_page_config(page_title="Mesa de Triagem", page_icon=":material/inbox:",
                   layout="wide")


def num_br(v, casas=0):
    """Formata número no padrão brasileiro: 1.234,56.

    Troca os separadores de uma vez, em vez de aplicar .replace() sobre a
    frase inteira — que trocaria também as vírgulas do texto por pontos.
    """
    s = f"{v:,.{casas}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


# ----------------------------------------------------------------- dados

@st.cache_resource
def carregar_modelo():
    """Devolve (modelo, erro).

    O modelo treinado vem versionado no repositório para que o avaliador
    rode o app sem treinar nada. Mas o joblib não garante compatibilidade
    entre versões do scikit-learn: num ambiente diferente o pickle pode
    falhar. Nesse caso a tela tem de dizer o que fazer, não mostrar
    traceback.
    """
    caminho = SAIDA / "modelo_triagem.joblib"
    if not caminho.exists():
        return None, "arquivo não encontrado"
    try:
        return load(caminho), None
    except Exception as e:
        return None, f"falha ao desserializar ({type(e).__name__})"


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


modelo, erro_modelo = carregar_modelo()
metricas = carregar_metricas()

if modelo is None or metricas is None:
    st.error(
        f"Modelo indisponível: {erro_modelo or 'métricas ausentes'}.\n\n"
        "O modelo treinado e as métricas vêm versionados em "
        "`solution/outputs/`. Se faltarem, ou se a versão do "
        "scikit-learn deste ambiente for incompatível com a do pickle, "
        "regenere com:\n\n"
        "`python scripts/03_classificador.py`\n\n"
        f"Procurado em: `{SAIDA}`")
    st.stop()

CLASSES = list(modelo.named_steps["clf"].classes_)
CURVA = metricas["curva_cobertura_x_acuracia"]
POR_CLASSE = metricas["desempenho_por_classe"]

# Categorias que nunca são roteadas sozinhas, independentemente da
# confiança. Justificativa no item 2 do relatório: envolvem concessão de
# privilégio, decisão de gasto ou dado pessoal — onde o custo de errar é
# assimétrico.
SEMPRE_HUMANO = {"Administrative rights", "Purchase"}

AUTOMATICO = "AUTOMÁTICO"
HUMANO = "HUMANO"


def classificar(texto, limiar):
    proba = modelo.predict_proba([texto])[0]
    ordem = np.argsort(proba)[::-1]
    topo = CLASSES[ordem[0]]
    conf = float(proba[ordem[0]])

    if topo in SEMPRE_HUMANO:
        decisao = HUMANO
        motivo = f"categoria '{topo}' é de decisão sensível"
    elif conf < limiar:
        decisao = HUMANO
        motivo = f"confiança {conf:.0%} abaixo do limiar {limiar:.0%}"
    else:
        decisao = AUTOMATICO
        motivo = f"confiança {conf:.0%} acima do limiar"

    return {
        "categoria": topo, "confianca": conf, "decisao": decisao,
        "motivo": motivo,
        "alternativas": [(CLASSES[i], float(proba[i])) for i in ordem[1:4]],
    }


@st.cache_data
def exemplos_reais():
    """Um ticket real de cada categoria, com o rótulo verdadeiro à vista.

    Preferir tickets reais a exemplos escritos para a demo: exemplo escrito
    à mão tende a conter as palavras que o autor acha que definem a classe,
    o que inflaciona artificialmente a confiança do modelo.
    """
    d = carregar_amostra(3000)
    if d is None:
        return {"(escrever manualmente)": ""}
    escolhidos = {"(escrever manualmente)": ""}
    for cat in sorted(d["Topic_group"].unique()):
        linha = d[d["Topic_group"] == cat].iloc[0]
        escolhidos[f"{cat} (rótulo real)"] = linha["Document"]
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

st.title("Mesa de Triagem")
st.caption(
    "Classificação e roteamento automático de tickets · modelo treinado em "
    f"{num_br(metricas['configuracao']['n_treino'])} tickets reais · "
    f"acurácia {num_br(metricas['desempenho_global']['acuracia_pct'], 2)}%.")

with st.sidebar:
    st.header("Configuração")
    limiar = st.slider("Limiar de confiança para roteamento automático",
                       0.50, 0.99, 0.80, 0.01,
                       help="Abaixo deste valor, o ticket vai para um humano.")

    ponto = min(CURVA, key=lambda r: abs(r["limiar_confianca"] - limiar))
    st.metric("Cobertura automática",
              f"{num_br(ponto['cobertura_pct'], 1)}%")
    st.metric("Acurácia no automatizado",
              f"{num_br(ponto['acuracia_no_aceito_pct'], 2)}%")
    st.caption(f"A cada 1.000 tickets, ~{int(ponto['cobertura_pct'] * 10)} "
               "são roteados sozinhos e "
               f"~{round(ponto['cobertura_pct'] * 10 * (1 - ponto['acuracia_no_aceito_pct'] / 100))}"
               " deles vão para a fila errada.")
    st.divider()
    st.caption("**Sempre humano**, qualquer confiança:\n\n"
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
            help="Tickets sorteados do conjunto real, com o rótulo verdadeiro "
                 "entre parênteses. Não são exemplos escritos para a demo.")
        texto = st.text_area("Texto do ticket", value=exemplos[escolha],
                             height=180,
                             placeholder="Cole aqui o texto do chamado...")
        analisar = st.button("Classificar", type="primary")

    with col_b:
        if analisar and texto.strip():
            r = classificar(texto, limiar)
            if r["decisao"] == AUTOMATICO:
                st.success(f"**{r['decisao']}** → fila *{r['categoria']}*")
            else:
                st.warning(f"**{r['decisao']}** → revisão manual")
            st.caption(f"Motivo: {r['motivo']}")
            st.metric("Categoria prevista", r["categoria"],
                      f"{r['confianca']:.1%} de confiança")

            st.write("**Outras hipóteses**")
            for cat, p in r["alternativas"]:
                st.write(f"- {cat} · {p:.1%}")

            st.write("**Por que esta categoria**")
            for termo, peso in termos_decisivos(texto, r["categoria"]):
                if peso > 0:
                    st.write(f"- `{termo}` (+{num_br(peso, 3)})")

            qualidade = POR_CLASSE.get(r["categoria"], {})
            if qualidade:
                st.caption(
                    "Histórico desta categoria no teste: precisão "
                    f"{qualidade['precision']:.1%} · recall "
                    f"{qualidade['recall']:.1%}.")
        elif analisar:
            st.info("Cole o texto de um ticket.")

# ---------------------------------------------------------------- aba 2
with aba2:
    st.subheader("Simulação sobre amostra real do dataset")
    st.caption("Amostra aleatória (semente fixa) dos tickets reais — não são "
               "exemplos escolhidos a dedo. O rótulo verdadeiro está na "
               "coluna final para conferência.")

    amostra = carregar_amostra()
    if amostra is None:
        st.error(
            "Dataset 2 não encontrado. Esta aba roda sobre os tickets reais "
            "do dataset, não sobre exemplos embutidos — por isso depende do "
            "CSV.\n\n"
            f"Procurado em: `{DADOS / 'all_tickets_processed_improved_v3.csv'}`"
            "\n\nVer `docs/SETUP.md` para obter os dados.")
    else:
        if st.button("Rodar triagem no lote", type="primary"):
            proba = modelo.predict_proba(amostra["Document"])
            previsto = np.array(CLASSES)[proba.argmax(axis=1)]
            conf = proba.max(axis=1)
            sensivel = np.isin(previsto, list(SEMPRE_HUMANO))
            auto = (conf >= limiar) & ~sensivel

            # Motivo explícito da decisão: a regra de negócio fica visível
            # na tela, não escondida na lógica do código.
            motivo = np.where(
                sensivel, "categoria sensível (sempre humano)",
                np.where(auto, "confiança suficiente",
                         "confiança baixa (< limiar)"))

            tabela = pd.DataFrame({
                "ticket": amostra["Document"].str.slice(0, 90) + "...",
                "previsto": previsto,
                "confiança": conf.round(3),
                "decisão": np.where(auto, AUTOMATICO, HUMANO),
                "motivo": motivo,
                "rótulo real": amostra["Topic_group"],
                "acertou": previsto == amostra["Topic_group"],
            })

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tickets", len(tabela))
            c2.metric("Roteados sozinhos", f"{auto.mean():.1%}")
            acc_auto = tabela.loc[auto, "acertou"].mean() if auto.any() else 0
            c3.metric("Acurácia no automático", f"{acc_auto:.1%}")
            c4.metric("Para humano", int((~auto).sum()))
            st.caption(
                f"Dos {int((~auto).sum())} tickets para humano: "
                f"{int(sensivel.sum())} por categoria sensível "
                "(Administrative rights/Purchase, qualquer confiança) e "
                f"{int((~auto & ~sensivel).sum())} por confiança abaixo "
                "do limiar.")

            st.dataframe(tabela, use_container_width=True, height=420)

            st.write("**Distribuição por fila**")
            st.bar_chart(tabela["previsto"].value_counts())

# ---------------------------------------------------------------- aba 3
with aba3:
    st.subheader("Quanto isso economiza")
    st.caption("Todas as premissas são editáveis. Discorde de qualquer uma "
               "e o número recalcula.")

    c1, c2, c3 = st.columns(3)
    volume = c1.number_input("Tickets por ano", 1_000, 500_000, 30_000, 1_000)
    custo_hora = c2.number_input("Custo/hora do agente (R$)", 10.0, 500.0,
                                 45.0, 5.0)
    min_triagem = c3.number_input("Minutos de triagem manual por ticket",
                                  0.5, 30.0, 4.0, 0.5)
    min_retrabalho = c1.number_input("Minutos de retrabalho por erro",
                                     1.0, 120.0, 12.0, 1.0)
    jornada = c2.number_input("Horas/mês por FTE", 100, 220, 168, 4)
    min_sugestao = c3.number_input(
        "Min. economizados por sugestão (ticket manual)", 0.0, 10.0, 1.5, 0.5,
        help="Tempo poupado no ticket que vai para humano mas chega com "
             "categoria sugerida e termos-chave, em vez de partir do zero.")

    ponto = min(CURVA, key=lambda r: abs(r["limiar_confianca"] - limiar))
    cobertura = ponto["cobertura_pct"] / 100
    taxa_erro = 1 - ponto["acuracia_no_aceito_pct"] / 100

    horas_totais = volume * min_triagem / 60
    horas_brutas = horas_totais * cobertura
    horas_retrab = volume * cobertura * taxa_erro * min_retrabalho / 60
    horas_assistidas = volume * (1 - cobertura) * min_sugestao / 60
    horas_liq = horas_brutas - horas_retrab + horas_assistidas

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Custo atual da triagem",
              f"R$ {num_br(horas_totais * custo_hora)}/ano")
    m2.metric("Horas líquidas liberadas",
              f"{num_br(horas_liq)}/ano",
              f"−{num_br(horas_retrab)}h de retrabalho "
              f"+{num_br(horas_assistidas)}h assistidas")
    m3.metric("Economia líquida",
              f"R$ {num_br(horas_liq * custo_hora)}/ano")
    m4.metric("Equivalente", f"{num_br(horas_liq / 12 / jornada, 2)} FTE")

    st.write("**Sensibilidade ao limiar** — mais automação não é linearmente "
             "melhor: acima de certo ponto, o erro consome o ganho.")
    linhas = []
    for r in CURVA:
        if r["limiar_confianca"] < 0.5:
            continue
        cob = r["cobertura_pct"] / 100
        err = 1 - r["acuracia_no_aceito_pct"] / 100
        hl = (horas_totais * cob - volume * cob * err * min_retrabalho / 60
              + volume * (1 - cob) * min_sugestao / 60)
        linhas.append({"limiar": r["limiar_confianca"],
                       "cobertura %": r["cobertura_pct"],
                       "acurácia %": r["acuracia_no_aceito_pct"],
                       "horas líquidas/ano": round(hl),
                       "economia R$/ano": round(hl * custo_hora)})
    df = pd.DataFrame(linhas)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.line_chart(df.set_index("limiar")["economia R$/ano"])
