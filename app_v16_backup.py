from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGO_PATH = BASE_DIR / "logo.png"

st.set_page_config(
    page_title="E-Factor BI",
    page_icon=str(LOGO_PATH) if LOGO_PATH.exists() else "📊",
    layout="wide"
)

st.markdown("""
<style>
.block-container { padding-top: 1.4rem; }
.big-title { font-size: 34px; font-weight: 800; line-height: 1.1; }
.sub-title { color: #8A94A6; font-size: 18px; margin-top: 6px; }
.pill {
    display: inline-block;
    padding: 8px 14px;
    border: 1px solid #E5E7EB;
    border-radius: 22px;
    margin-right: 8px;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)


def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def numero(valor):
    try:
        return f"{float(valor):,.0f}".replace(",", ".")
    except Exception:
        return "0"


def percentual(valor):
    try:
        return f"{float(valor) * 100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "0,00%"


def formatar_tabela(df):
    df = df.copy()

    for col in df.columns:
        col_lower = col.lower()

        if any(x in col_lower for x in ["faturamento", "ticket", "valor", "total", "meta", "realizado", "projecao", "gap", "ritmo"]):
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].apply(moeda)

        if any(x in col_lower for x in ["participacao", "percentual", "share", "crescimento"]):
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].apply(percentual)

    return df


@st.cache_data
def carregar_csv(nome):
    caminho = DATA_DIR / nome
    if caminho.exists():
        return pd.read_csv(caminho)
    return pd.DataFrame()


pedidos = carregar_csv("pedidos.csv")
itens = carregar_csv("itens_pedido.csv")
metas = carregar_csv("metas_inteligentes.csv")

if "assessor" not in pedidos.columns:
    pedidos["assessor"] = "SEM ASSESSOR"

if "assessor" not in itens.columns:
    itens["assessor"] = "SEM ASSESSOR"

if not metas.empty and "assessor" not in metas.columns:
    metas["assessor"] = "SEM ASSESSOR"

pedidos["total_pedido"] = pd.to_numeric(pedidos["total_pedido"], errors="coerce").fillna(0)
itens["valor_total_item"] = pd.to_numeric(itens["valor_total_item"], errors="coerce").fillna(0)
itens["quantidade"] = pd.to_numeric(itens["quantidade"], errors="coerce").fillna(0)

pedidos["data_pedido_dt"] = pd.to_datetime(
    pedidos["data_pedido"],
    format="%d/%m/%Y",
    errors="coerce"
)

if not metas.empty:
    for col in [
        "meta",
        "realizado",
        "percentual_realizado",
        "meta_proporcional_hoje",
        "diferenca_vs_meta_proporcional",
        "media_diaria_realizada",
        "projecao_mes",
        "percentual_projetado",
        "gap_projetado",
        "valor_faltante_meta",
        "ritmo_diario_necessario"
    ]:
        if col in metas.columns:
            metas[col] = pd.to_numeric(metas[col], errors="coerce").fillna(0)

# =========================
# CABEÇALHO
# =========================

col_logo, col_titulo = st.columns([1, 6])

with col_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=120)
    else:
        st.markdown("## 📊")

with col_titulo:
    st.markdown(
        '<div class="big-title">e-Factor Consultoria e Assessoria</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sub-title">Painel de Controle</div>',
        unsafe_allow_html=True
    )

st.caption("Inteligência comercial multiempresa integrada ao Tiny ERP")

# =========================
# FILTROS
# =========================

st.sidebar.title("Filtros")

assessores = sorted(pedidos["assessor"].dropna().unique())
assessores_filtro = st.sidebar.multiselect("Assessor", assessores, default=assessores)

empresas_disponiveis = sorted(
    pedidos[pedidos["assessor"].isin(assessores_filtro)]["empresa"].dropna().unique()
)

empresas_filtro = st.sidebar.multiselect("Empresas", empresas_disponiveis, default=empresas_disponiveis)

canais = sorted(pedidos["canal"].dropna().unique())
ufs = sorted(pedidos["uf"].dropna().unique())

canais_filtro = st.sidebar.multiselect("Canais", canais, default=canais)
ufs_filtro = st.sidebar.multiselect("UF", ufs, default=ufs)

base_pedidos = pedidos[
    pedidos["assessor"].isin(assessores_filtro)
    & pedidos["empresa"].isin(empresas_filtro)
    & pedidos["canal"].isin(canais_filtro)
    & pedidos["uf"].isin(ufs_filtro)
].copy()

ids_pedidos = base_pedidos["id_pedido"].astype(str).unique()
base_itens = itens[itens["id_pedido"].astype(str).isin(ids_pedidos)].copy()

if not metas.empty:
    base_metas = metas[
        metas["assessor"].isin(assessores_filtro)
        & metas["empresa"].isin(empresas_filtro)
    ].copy()
else:
    base_metas = pd.DataFrame()

# =========================
# TOP BAR
# =========================

st.markdown(
    '<span class="pill">📅 mês atual</span>'
    '<span class="pill">🔎 filtros ativos</span>'
    '<span class="pill">↻ atualizado agora</span>',
    unsafe_allow_html=True
)

st.divider()

# =========================
# KPIs
# =========================

faturamento = base_pedidos["total_pedido"].sum()
qtd_pedidos = base_pedidos["id_pedido"].nunique()
ticket_medio = base_pedidos["total_pedido"].mean() if qtd_pedidos else 0
clientes = base_pedidos["cpf_cnpj_cliente"].nunique()
itens_vendidos = base_itens["quantidade"].sum()

meta_total = base_metas["meta"].sum() if not base_metas.empty and "meta" in base_metas.columns else 0
realizado_meta = base_metas["realizado"].sum() if not base_metas.empty and "realizado" in base_metas.columns else faturamento
projecao_total = base_metas["projecao_mes"].sum() if not base_metas.empty and "projecao_mes" in base_metas.columns else 0
perc_meta = realizado_meta / meta_total if meta_total else 0

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Faturamento", moeda(faturamento))
k2.metric("Meta mensal", moeda(meta_total))
k3.metric("% meta", percentual(perc_meta))
k4.metric("Projeção", moeda(projecao_total))
k5.metric("Pedidos", numero(qtd_pedidos))

st.caption(f"Última atualização visual: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# =========================
# ABAS
# =========================

aba_vendas, aba_metas, aba_assessor, aba_empresas, aba_produtos, aba_clientes, aba_alertas, aba_dados = st.tabs([
    "📌 Vendas",
    "🎯 Metas",
    "🧑‍💼 Assessores",
    "🏢 Empresas",
    "📦 Produtos",
    "👥 Clientes",
    "🚨 Alertas",
    "🧾 Dados"
])
# =========================
# VENDAS
# =========================

with aba_vendas:

    vendas_dia = (
        base_pedidos
        .dropna(subset=["data_pedido_dt"])
        .groupby("data_pedido_dt", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique")
        )
        .sort_values("data_pedido_dt")
    )

    fig_vendas = px.area(
        vendas_dia,
        x="data_pedido_dt",
        y="faturamento",
        title="Evolução diária do faturamento"
    )

    st.plotly_chart(fig_vendas, width="stretch")

    col1, col2 = st.columns(2)

    resumo_canal = (
        base_pedidos
        .groupby("canal", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig_canal = px.pie(
        resumo_canal,
        names="canal",
        values="faturamento",
        title="Share por canal"
    )

    col1.plotly_chart(fig_canal, width="stretch")
    col1.dataframe(formatar_tabela(resumo_canal), width="stretch")

    resumo_uf = (
        base_pedidos
        .groupby("uf", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig_uf = px.bar(
        resumo_uf.head(15),
        x="uf",
        y="faturamento",
        title="Top UFs"
    )

    col2.plotly_chart(fig_uf, width="stretch")
    col2.dataframe(formatar_tabela(resumo_uf), width="stretch")

# =========================
# METAS
# =========================

with aba_metas:

    st.subheader("Meta Inteligente")

    if base_metas.empty:
        st.warning("Nenhuma meta encontrada.")
    else:

        col1, col2, col3, col4 = st.columns(4)

        empresas_risco = len(
            base_metas[
                base_metas["status_meta"].astype(str).str.contains("RISCO")
            ]
        )

        empresas_atencao = len(
            base_metas[
                base_metas["status_meta"].astype(str).str.contains("ATEN")
            ]
        )

        empresas_saudavel = len(
            base_metas[
                base_metas["status_meta"].astype(str).str.contains("SAUD")
            ]
        )

        col1.metric("🔴 Risco", numero(empresas_risco))
        col2.metric("🟡 Atenção", numero(empresas_atencao))
        col3.metric("🟢 Saudável", numero(empresas_saudavel))
        col4.metric("Meta total", moeda(meta_total))

        ranking_meta = (
            base_metas
            .sort_values("percentual_projetado", ascending=True)
        )

        fig_meta = px.bar(
            ranking_meta,
            x="empresa",
            y="percentual_projetado",
            color="status_meta",
            title="Projeção de atingimento da meta",
            text_auto=".0%"
        )

        st.plotly_chart(fig_meta, width="stretch")

        metas_view = ranking_meta[[
            "assessor",
            "empresa",
            "meta",
            "realizado",
            "percentual_realizado",
            "projecao_mes",
            "percentual_projetado",
            "gap_projetado",
            "ritmo_diario_necessario",
            "status_meta"
        ]].copy()

        st.dataframe(
            formatar_tabela(metas_view),
            width="stretch"
        )

# =========================
# ASSESSORES
# =========================

with aba_assessor:

    ranking_assessor = (
        base_pedidos
        .groupby("assessor", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique"),
            clientes=("cpf_cnpj_cliente", "nunique"),
            ticket_medio=("total_pedido", "mean")
        )
        .sort_values("faturamento", ascending=False)
    )

    total_assessor = ranking_assessor["faturamento"].sum()

    ranking_assessor["participacao"] = (
        ranking_assessor["faturamento"] / total_assessor
        if total_assessor else 0
    )

    fig_assessor = px.bar(
        ranking_assessor,
        x="assessor",
        y="faturamento",
        title="Ranking de assessores",
        text_auto=".2s"
    )

    st.plotly_chart(fig_assessor, width="stretch")
    st.dataframe(formatar_tabela(ranking_assessor), width="stretch")

# =========================
# EMPRESAS
# =========================

with aba_empresas:

    ranking_empresas = (
        base_pedidos
        .groupby(["assessor", "empresa"], as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique"),
            clientes=("cpf_cnpj_cliente", "nunique"),
            ticket_medio=("total_pedido", "mean")
        )
        .sort_values("faturamento", ascending=False)
    )

    total_empresas = ranking_empresas["faturamento"].sum()

    ranking_empresas["participacao"] = (
        ranking_empresas["faturamento"] / total_empresas
        if total_empresas else 0
    )

    fig_empresas = px.bar(
        ranking_empresas,
        x="empresa",
        y="faturamento",
        color="assessor",
        title="Ranking de empresas",
        text_auto=".2s"
    )

    st.plotly_chart(fig_empresas, width="stretch")
    st.dataframe(formatar_tabela(ranking_empresas), width="stretch")

# =========================
# PRODUTOS
# =========================

with aba_produtos:

    top_produtos = (
        base_itens
        .groupby(["codigo_produto", "descricao_produto"], as_index=False)
        .agg(
            faturamento=("valor_total_item", "sum"),
            quantidade=("quantidade", "sum")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig_prod = px.bar(
        top_produtos.head(20),
        x="faturamento",
        y="descricao_produto",
        orientation="h",
        title="Top produtos"
    )

    fig_prod.update_layout(
        yaxis={"categoryorder": "total ascending"}
    )

    st.plotly_chart(fig_prod, width="stretch")
    st.dataframe(formatar_tabela(top_produtos), width="stretch")

# =========================
# CLIENTES
# =========================

with aba_clientes:

    top_clientes = (
        base_pedidos
        .groupby(
            ["assessor", "cliente", "cpf_cnpj_cliente"],
            as_index=False
        )
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique"),
            ticket_medio=("total_pedido", "mean")
        )
        .sort_values("faturamento", ascending=False)
    )

    recorrentes = top_clientes[
        top_clientes["pedidos"] >= 2
    ]

    col1, col2 = st.columns(2)

    col1.metric(
        "Clientes recorrentes",
        numero(len(recorrentes))
    )

    perc_recorrentes = (
        len(recorrentes) / len(top_clientes)
        if len(top_clientes)
        else 0
    )

    col2.metric(
        "% recorrentes",
        percentual(perc_recorrentes)
    )

    st.dataframe(
        formatar_tabela(top_clientes.head(200)),
        width="stretch"
    )

# =========================
# ALERTAS
# =========================

with aba_alertas:

    alertas = []

    if not base_metas.empty:

        risco = base_metas[
            base_metas["status_meta"]
            .astype(str)
            .str.contains("RISCO")
        ]

        for _, row in risco.iterrows():
            alertas.append(
                f"🔴 {row['empresa']} está em risco. "
                f"Projetado: {percentual(row['percentual_projetado'])}"
            )

    if alertas:
        for alerta in alertas:
            st.warning(alerta)
    else:
        st.success("Nenhum alerta crítico encontrado.")

# =========================
# DADOS
# =========================

with aba_dados:

    st.subheader("Pedidos")
    st.dataframe(
        formatar_tabela(base_pedidos.head(1000)),
        width="stretch"
    )

    st.subheader("Itens")
    st.dataframe(
        formatar_tabela(base_itens.head(1000)),
        width="stretch"
    )

    if not base_metas.empty:
        st.subheader("Metas")
        st.dataframe(
            formatar_tabela(base_metas),
            width="stretch"
        )