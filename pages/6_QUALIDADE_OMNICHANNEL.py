from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# MIOS V19.6.6.1 - DASHBOARD QUALIDADE OMNICHANNEL
# COM FILTRO MENSAL
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

PEDIDOS_PATH = DATA_DIR / "pedidos_historico.csv"


st.set_page_config(
    page_title="MIOS | Qualidade Omnichannel",
    page_icon="🧭",
    layout="wide"
)


def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def percentual(valor):
    try:
        return f"{float(valor) * 100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00%"


def numero(valor):
    try:
        return f"{float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "0"


def classificar_qualidade(score):
    if score >= 80:
        return "🟢 BOA"
    if score >= 60:
        return "🟡 ATENÇÃO"
    return "🔴 CRÍTICA"


def origem_tipo(origem):
    origem = str(origem).lower()

    if origem == "canal":
        return "CANAL_OFICIAL"

    if "heuristica" in origem:
        return "HEURISTICA"

    if "prefixo" in origem:
        return "PREFIXO"

    if "intermediador" in origem:
        return "INTERMEDIADOR"

    if "fallback" in origem:
        return "FALLBACK"

    return "OUTROS"


@st.cache_data
def carregar_pedidos():
    if not PEDIDOS_PATH.exists():
        return pd.DataFrame()

    df = pd.read_csv(PEDIDOS_PATH, low_memory=False)

    if "data_pedido" in df.columns:
        df["data_pedido_dt"] = pd.to_datetime(
            df["data_pedido"],
            format="%d/%m/%Y",
            errors="coerce"
        )
    else:
        df["data_pedido_dt"] = pd.NaT

    df["ano"] = df["data_pedido_dt"].dt.year
    df["mes"] = df["data_pedido_dt"].dt.month

    if "total_pedido" in df.columns:
        df["total_pedido"] = pd.to_numeric(df["total_pedido"], errors="coerce").fillna(0)
    else:
        df["total_pedido"] = 0

    if "origem_classificacao_canal" not in df.columns:
        df["origem_classificacao_canal"] = "fallback"

    if "canal_estrategico" not in df.columns:
        df["canal_estrategico"] = "Marketplace Não Identificado"

    if "empresa" not in df.columns:
        df["empresa"] = "Não identificado"

    df["origem_tipo"] = df["origem_classificacao_canal"].apply(origem_tipo)
    df["classificado"] = df["canal_estrategico"].astype(str).str.lower() != "marketplace não identificado"
    df["fallback"] = df["origem_tipo"] == "FALLBACK"
    df["canal_oficial"] = df["origem_tipo"] == "CANAL_OFICIAL"
    df["heuristica"] = df["origem_tipo"].isin(["HEURISTICA", "PREFIXO", "INTERMEDIADOR"])

    return df


def gerar_kpis(base):
    total_pedidos = base["id_pedido"].nunique() if "id_pedido" in base.columns else len(base)
    total_faturamento = base["total_pedido"].sum()

    pedidos_classificados = base[base["classificado"]]["id_pedido"].nunique() if "id_pedido" in base.columns else base["classificado"].sum()
    pedidos_fallback = base[base["fallback"]]["id_pedido"].nunique() if "id_pedido" in base.columns else base["fallback"].sum()
    pedidos_canal_oficial = base[base["canal_oficial"]]["id_pedido"].nunique() if "id_pedido" in base.columns else base["canal_oficial"].sum()
    pedidos_heuristica = base[base["heuristica"]]["id_pedido"].nunique() if "id_pedido" in base.columns else base["heuristica"].sum()

    pct_classificado = pedidos_classificados / total_pedidos if total_pedidos else 0
    pct_fallback = pedidos_fallback / total_pedidos if total_pedidos else 0
    pct_canal_oficial = pedidos_canal_oficial / total_pedidos if total_pedidos else 0
    pct_heuristica = pedidos_heuristica / total_pedidos if total_pedidos else 0

    score = round(
        (pct_classificado * 60)
        + (pct_canal_oficial * 25)
        + (pct_heuristica * 15),
        2
    )

    return {
        "total_pedidos": total_pedidos,
        "faturamento_total": total_faturamento,
        "pct_classificado": pct_classificado,
        "pct_fallback": pct_fallback,
        "pct_canal_oficial": pct_canal_oficial,
        "pct_heuristica": pct_heuristica,
        "score": score,
        "status": classificar_qualidade(score),
    }


def gerar_ranking(base):
    linhas = []

    for empresa, df in base.groupby("empresa"):
        total = df["id_pedido"].nunique() if "id_pedido" in df.columns else len(df)
        faturamento = df["total_pedido"].sum()

        classificados = df[df["classificado"]]["id_pedido"].nunique() if "id_pedido" in df.columns else df["classificado"].sum()
        fallback = df[df["fallback"]]["id_pedido"].nunique() if "id_pedido" in df.columns else df["fallback"].sum()
        canal_oficial = df[df["canal_oficial"]]["id_pedido"].nunique() if "id_pedido" in df.columns else df["canal_oficial"].sum()
        heuristica = df[df["heuristica"]]["id_pedido"].nunique() if "id_pedido" in df.columns else df["heuristica"].sum()

        pct_class = classificados / total if total else 0
        pct_fall = fallback / total if total else 0
        pct_oficial = canal_oficial / total if total else 0
        pct_heu = heuristica / total if total else 0

        score = round(
            (pct_class * 60)
            + (pct_oficial * 25)
            + (pct_heu * 15),
            2
        )

        linhas.append({
            "empresa": empresa,
            "pedidos": total,
            "faturamento": round(faturamento, 2),
            "pct_classificado": round(pct_class, 4),
            "pct_fallback": round(pct_fall, 4),
            "pct_canal_oficial": round(pct_oficial, 4),
            "pct_heuristica": round(pct_heu, 4),
            "quantidade_canais": df["canal_estrategico"].nunique(),
            "score_qualidade_canais": score,
            "status_qualidade": classificar_qualidade(score),
        })

    return pd.DataFrame(linhas).sort_values(
        ["score_qualidade_canais", "faturamento"],
        ascending=[True, False]
    )


pedidos = carregar_pedidos()

st.title("🧭 Qualidade Omnichannel MIOS")
st.caption("Governança mensal da classificação de canais, fallback e heurísticas marketplace.")

if pedidos.empty:
    st.error("Arquivo pedidos_historico.csv não encontrado.")
    st.stop()


# =====================================================
# FILTROS
# =====================================================

st.sidebar.title("Filtros")

anos = sorted(pedidos["ano"].dropna().astype(int).unique())

if not anos:
    st.error("Nenhuma data válida encontrada em pedidos_historico.csv.")
    st.stop()

ano_filtro = st.sidebar.selectbox("Ano", anos, index=len(anos) - 1)

meses_disponiveis = sorted(
    pedidos[pedidos["ano"] == ano_filtro]["mes"].dropna().astype(int).unique()
)

opcoes_meses = ["Todos"] + meses_disponiveis

mes_filtro = st.sidebar.selectbox(
    "Mês",
    opcoes_meses,
    index=len(opcoes_meses) - 1
)

tipo_opcoes = ["Todos"] + sorted(pedidos["tipo_venda"].dropna().astype(str).unique()) if "tipo_venda" in pedidos.columns else ["Todos"]

tipo_filtro = st.sidebar.selectbox(
    "Tipo de venda",
    tipo_opcoes,
    index=tipo_opcoes.index("DIGITAL") if "DIGITAL" in tipo_opcoes else 0
)


base = pedidos[pedidos["ano"] == ano_filtro].copy()

if mes_filtro != "Todos":
    base = base[base["mes"] == int(mes_filtro)].copy()

if tipo_filtro != "Todos" and "tipo_venda" in base.columns:
    base = base[base["tipo_venda"].astype(str) == tipo_filtro].copy()

empresas_opcoes = sorted(base["empresa"].dropna().unique())

empresas_filtro = st.sidebar.multiselect(
    "Empresas",
    empresas_opcoes,
    default=empresas_opcoes
)

base = base[base["empresa"].isin(empresas_filtro)].copy()

if base.empty:
    st.warning("Nenhum pedido encontrado para os filtros selecionados.")
    st.stop()


ranking = gerar_ranking(base)
kpi = gerar_kpis(base)

status_opcoes = sorted(ranking["status_qualidade"].dropna().unique())

status_filtro = st.sidebar.multiselect(
    "Status qualidade",
    status_opcoes,
    default=status_opcoes
)

ranking_filtrado = ranking[
    ranking["status_qualidade"].isin(status_filtro)
].copy()


# =====================================================
# KPIS
# =====================================================

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Score qualidade", f"{kpi['score']:.2f}")
c2.metric("Status", kpi["status"])
c3.metric("% classificado", percentual(kpi["pct_classificado"]))
c4.metric("% fallback", percentual(kpi["pct_fallback"]))
c5.metric("% canal oficial", percentual(kpi["pct_canal_oficial"]))
c6.metric("% heurística", percentual(kpi["pct_heuristica"]))

st.caption(
    f"Período: {mes_filtro}/{ano_filtro} | Tipo: {tipo_filtro} | "
    f"Pedidos: {numero(kpi['total_pedidos'])} | Faturamento: {moeda(kpi['faturamento_total'])}"
)

st.divider()


# =====================================================
# VISÃO EXECUTIVA
# =====================================================

st.subheader("📌 Visão executiva da qualidade")

col_a, col_b, col_c = st.columns(3)

col_a.metric(
    "Empresas críticas",
    numero(ranking_filtrado["status_qualidade"].astype(str).str.contains("CRÍTICA", na=False).sum())
)

col_b.metric(
    "Empresas atenção",
    numero(ranking_filtrado["status_qualidade"].astype(str).str.contains("ATENÇÃO", na=False).sum())
)

col_c.metric(
    "Empresas boas",
    numero(ranking_filtrado["status_qualidade"].astype(str).str.contains("BOA", na=False).sum())
)


# =====================================================
# RANKING
# =====================================================

st.subheader("🏢 Ranking mensal de qualidade por empresa")

ranking_plot = ranking_filtrado.sort_values("score_qualidade_canais", ascending=True).head(25)

fig_ranking = px.bar(
    ranking_plot,
    x="score_qualidade_canais",
    y="empresa",
    color="status_qualidade",
    orientation="h",
    title="Piores empresas por score de qualidade no período",
)

fig_ranking.update_layout(yaxis={"categoryorder": "total ascending"})

st.plotly_chart(fig_ranking, width="stretch")


ranking_tabela = ranking_filtrado.copy()

ranking_tabela["faturamento"] = ranking_tabela["faturamento"].apply(moeda)

for col in ["pct_classificado", "pct_fallback", "pct_canal_oficial", "pct_heuristica"]:
    ranking_tabela[col] = ranking_tabela[col].apply(percentual)

st.dataframe(
    ranking_tabela.sort_values("score_qualidade_canais"),
    width="stretch"
)


# =====================================================
# AUDITORIA
# =====================================================

st.subheader("🔎 Auditoria por origem de classificação")

auditoria = (
    base.groupby(["origem_tipo", "canal_estrategico"], as_index=False)
    .agg(
        pedidos=("id_pedido", "nunique"),
        faturamento=("total_pedido", "sum")
    )
    .sort_values("faturamento", ascending=False)
)

fig_origem = px.bar(
    auditoria,
    x="origem_tipo",
    y="faturamento",
    color="canal_estrategico",
    title="Faturamento por origem de classificação no período",
    text_auto=".2s"
)

st.plotly_chart(fig_origem, width="stretch")

auditoria_tabela = auditoria.copy()
auditoria_tabela["faturamento"] = auditoria_tabela["faturamento"].apply(moeda)

st.dataframe(auditoria_tabela, width="stretch")


# =====================================================
# PLANO DE AÇÃO
# =====================================================

st.subheader("🛠️ Plano de ação sugerido")

criticas = ranking_filtrado[
    ranking_filtrado["status_qualidade"].astype(str).str.contains("CRÍTICA", na=False)
].copy()

if criticas.empty:
    st.success("Nenhuma empresa crítica nos filtros atuais.")
else:
    plano = criticas.copy()

    plano["acao_sugerida"] = plano.apply(
        lambda x: (
            "Revisar canal/intermediador no Tiny para o período filtrado"
            if x["pct_fallback"] >= 0.5
            else "Complementar heurísticas e validar aliases"
        ),
        axis=1
    )

    plano["faturamento"] = plano["faturamento"].apply(moeda)
    plano["pct_fallback"] = plano["pct_fallback"].apply(percentual)
    plano["pct_canal_oficial"] = plano["pct_canal_oficial"].apply(percentual)
    plano["pct_heuristica"] = plano["pct_heuristica"].apply(percentual)

    st.dataframe(
        plano[[
            "empresa",
            "score_qualidade_canais",
            "status_qualidade",
            "pedidos",
            "faturamento",
            "pct_fallback",
            "pct_canal_oficial",
            "pct_heuristica",
            "acao_sugerida",
        ]].sort_values("score_qualidade_canais"),
        width="stretch"
    )
