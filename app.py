from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

st.set_page_config(
    page_title="Tiny Analytics BI Cloud",
    layout="wide"
)

st.title("Tiny Analytics BI Cloud 🚀")
st.caption("Dashboard corporativo publicado online")

@st.cache_data
def carregar_csv(nome):
    caminho = DATA_DIR / nome
    return pd.read_csv(caminho)

pedidos = carregar_csv("pedidos.csv")
itens = carregar_csv("itens_pedido.csv")

pedidos["total_pedido"] = pd.to_numeric(
    pedidos["total_pedido"],
    errors="coerce"
).fillna(0)

itens["valor_total_item"] = pd.to_numeric(
    itens["valor_total_item"],
    errors="coerce"
).fillna(0)

itens["quantidade"] = pd.to_numeric(
    itens["quantidade"],
    errors="coerce"
).fillna(0)

pedidos["data_pedido_dt"] = pd.to_datetime(
    pedidos["data_pedido"],
    format="%d/%m/%Y",
    errors="coerce"
)

st.sidebar.header("Filtros")

empresas = sorted(pedidos["empresa"].dropna().unique())
canais = sorted(pedidos["canal"].dropna().unique())
ufs = sorted(pedidos["uf"].dropna().unique())

empresas_filtro = st.sidebar.multiselect(
    "Empresas",
    empresas,
    default=empresas
)

canais_filtro = st.sidebar.multiselect(
    "Canais",
    canais,
    default=canais
)

ufs_filtro = st.sidebar.multiselect(
    "UF",
    ufs,
    default=ufs
)

base_pedidos = pedidos[
    pedidos["empresa"].isin(empresas_filtro)
    & pedidos["canal"].isin(canais_filtro)
    & pedidos["uf"].isin(ufs_filtro)
].copy()

ids_pedidos = base_pedidos["id_pedido"].astype(str).unique()

base_itens = itens[
    itens["id_pedido"].astype(str).isin(ids_pedidos)
].copy()

faturamento = base_pedidos["total_pedido"].sum()
qtd_pedidos = base_pedidos["id_pedido"].nunique()
ticket_medio = base_pedidos["total_pedido"].mean()
clientes = base_pedidos["cpf_cnpj_cliente"].nunique()
itens_vendidos = base_itens["quantidade"].sum()

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric("Faturamento", f"R$ {faturamento:,.2f}")
c2.metric("Pedidos", f"{qtd_pedidos:,}")
c3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
c4.metric("Clientes", f"{clientes:,}")
c5.metric("Itens Vendidos", f"{itens_vendidos:,.0f}")

st.divider()

aba1, aba2, aba3, aba4 = st.tabs([
    "Executivo",
    "Produtos",
    "Clientes",
    "Dados"
])

with aba1:

    vendas_dia = (
        base_pedidos
        .dropna(subset=["data_pedido_dt"])
        .groupby("data_pedido_dt", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum")
        )
        .sort_values("data_pedido_dt")
    )

    fig = px.line(
        vendas_dia,
        x="data_pedido_dt",
        y="faturamento",
        title="Faturamento Diário"
    )

    st.plotly_chart(fig, width="stretch")

    resumo_empresa = (
        base_pedidos
        .groupby("empresa", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig2 = px.bar(
        resumo_empresa,
        x="empresa",
        y="faturamento",
        title="Faturamento por Empresa",
        text_auto=".2s"
    )

    st.plotly_chart(fig2, width="stretch")

    resumo_canal = (
        base_pedidos
        .groupby("canal", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum")
        )
    )

    fig3 = px.pie(
        resumo_canal,
        names="canal",
        values="faturamento",
        title="Share por Canal"
    )

    st.plotly_chart(fig3, width="stretch")

with aba2:

    top_produtos = (
        base_itens
        .groupby(
            ["codigo_produto", "descricao_produto"],
            as_index=False
        )
        .agg(
            faturamento=("valor_total_item", "sum"),
            quantidade=("quantidade", "sum")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig4 = px.bar(
        top_produtos.head(20),
        x="faturamento",
        y="descricao_produto",
        orientation="h",
        title="Top Produtos"
    )

    fig4.update_layout(
        yaxis={"categoryorder": "total ascending"}
    )

    st.plotly_chart(fig4, width="stretch")

    st.dataframe(
        top_produtos.head(100),
        width="stretch"
    )

with aba3:

    top_clientes = (
        base_pedidos
        .groupby(
            ["cliente", "cpf_cnpj_cliente"],
            as_index=False
        )
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    st.dataframe(
        top_clientes.head(100),
        width="stretch"
    )

with aba4:

    st.subheader("Pedidos")
    st.dataframe(
        base_pedidos.head(1000),
        width="stretch"
    )

    st.subheader("Itens")
    st.dataframe(
        base_itens.head(1000),
        width="stretch"
    )