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
.block-container { padding-top: 1.5rem; }
.big-title { font-size: 34px; font-weight: 800; line-height: 1.1; }
.sub-title { color: #9CA3AF; font-size: 18px; margin-top: 6px; }
</style>
""", unsafe_allow_html=True)

def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def numero(valor):
    return f"{valor:,.0f}".replace(",", ".")

@st.cache_data
def carregar_csv(nome):
    return pd.read_csv(DATA_DIR / nome)

pedidos = carregar_csv("pedidos.csv")
itens = carregar_csv("itens_pedido.csv")

if "assessor" not in pedidos.columns:
    pedidos["assessor"] = "SEM ASSESSOR"

if "assessor" not in itens.columns:
    itens["assessor"] = "SEM ASSESSOR"

pedidos["total_pedido"] = pd.to_numeric(pedidos["total_pedido"], errors="coerce").fillna(0)
itens["valor_total_item"] = pd.to_numeric(itens["valor_total_item"], errors="coerce").fillna(0)
itens["quantidade"] = pd.to_numeric(itens["quantidade"], errors="coerce").fillna(0)

pedidos["data_pedido_dt"] = pd.to_datetime(
    pedidos["data_pedido"],
    format="%d/%m/%Y",
    errors="coerce"
)

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

st.sidebar.title("Filtros")

assessores = sorted(pedidos["assessor"].dropna().unique())
empresas = sorted(pedidos["empresa"].dropna().unique())
canais = sorted(pedidos["canal"].dropna().unique())
ufs = sorted(pedidos["uf"].dropna().unique())

assessores_filtro = st.sidebar.multiselect(
    "Assessor",
    assessores,
    default=assessores
)

empresas_filtradas_por_assessor = sorted(
    pedidos[pedidos["assessor"].isin(assessores_filtro)]["empresa"].dropna().unique()
)

empresas_filtro = st.sidebar.multiselect(
    "Empresas",
    empresas_filtradas_por_assessor,
    default=empresas_filtradas_por_assessor
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
    pedidos["assessor"].isin(assessores_filtro)
    & pedidos["empresa"].isin(empresas_filtro)
    & pedidos["canal"].isin(canais_filtro)
    & pedidos["uf"].isin(ufs_filtro)
].copy()

ids_pedidos = base_pedidos["id_pedido"].astype(str).unique()

base_itens = itens[
    itens["id_pedido"].astype(str).isin(ids_pedidos)
].copy()

faturamento = base_pedidos["total_pedido"].sum()
qtd_pedidos = base_pedidos["id_pedido"].nunique()
ticket_medio = base_pedidos["total_pedido"].mean() if qtd_pedidos else 0
clientes = base_pedidos["cpf_cnpj_cliente"].nunique()
itens_vendidos = base_itens["quantidade"].sum()

st.divider()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Faturamento", moeda(faturamento))
c2.metric("Pedidos", numero(qtd_pedidos))
c3.metric("Ticket médio", moeda(ticket_medio))
c4.metric("Clientes", numero(clientes))
c5.metric("Itens vendidos", numero(itens_vendidos))

st.caption(f"Última atualização visual: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

aba_exec, aba_assessor, aba_emp, aba_prod, aba_cli, aba_alertas, aba_dados = st.tabs([
    "📌 Executivo",
    "🧑‍💼 Assessores",
    "🏢 Empresas",
    "📦 Produtos",
    "👥 Clientes",
    "🚨 Alertas",
    "🧾 Dados"
])

with aba_exec:
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

    fig_dia = px.line(
        vendas_dia,
        x="data_pedido_dt",
        y="faturamento",
        markers=True,
        title="Evolução diária do faturamento"
    )

    st.plotly_chart(fig_dia, width="stretch")

    col1, col2 = st.columns(2)

    resumo_canal = (
        base_pedidos
        .groupby("canal", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig_canal = px.pie(
        resumo_canal,
        names="canal",
        values="faturamento",
        title="Share de faturamento por canal"
    )

    col1.plotly_chart(fig_canal, width="stretch")

    resumo_uf = (
        base_pedidos
        .groupby("uf", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig_uf = px.bar(
        resumo_uf.head(15),
        x="uf",
        y="faturamento",
        title="Top UFs por faturamento",
        text_auto=".2s"
    )

    col2.plotly_chart(fig_uf, width="stretch")

with aba_assessor:
    st.subheader("Desempenho por Assessor")

    ranking_assessor = (
        base_pedidos
        .groupby("assessor", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique"),
            clientes=("cpf_cnpj_cliente", "nunique"),
            empresas=("empresa", "nunique"),
            ticket_medio=("total_pedido", "mean")
        )
        .sort_values("faturamento", ascending=False)
    )

    total_assessor = ranking_assessor["faturamento"].sum()

    if total_assessor:
        ranking_assessor["participacao"] = ranking_assessor["faturamento"] / total_assessor
    else:
        ranking_assessor["participacao"] = 0

    fig_assessor = px.bar(
        ranking_assessor,
        x="assessor",
        y="faturamento",
        title="Faturamento por Assessor",
        text_auto=".2s"
    )

    st.plotly_chart(fig_assessor, width="stretch")
    st.dataframe(ranking_assessor, width="stretch")

    st.subheader("Carteira por Assessor")

    carteira = (
        pedidos
        .groupby(["assessor", "empresa"], as_index=False)
        .agg(
            pedidos=("id_pedido", "nunique"),
            faturamento=("total_pedido", "sum")
        )
        .sort_values(["assessor", "faturamento"], ascending=[True, False])
    )

    st.dataframe(carteira, width="stretch")

with aba_emp:
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

    if total_empresas:
        ranking_empresas["participacao"] = ranking_empresas["faturamento"] / total_empresas
    else:
        ranking_empresas["participacao"] = 0

    fig_emp = px.bar(
        ranking_empresas,
        x="empresa",
        y="faturamento",
        color="assessor",
        title="Ranking de empresas por faturamento",
        text_auto=".2s"
    )

    st.plotly_chart(fig_emp, width="stretch")
    st.dataframe(ranking_empresas, width="stretch")

with aba_prod:
    top_produtos = (
        base_itens
        .groupby(["codigo_produto", "descricao_produto"], as_index=False)
        .agg(
            faturamento=("valor_total_item", "sum"),
            quantidade=("quantidade", "sum"),
            pedidos=("id_pedido", "nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    col1, col2 = st.columns(2)

    fig_prod_fat = px.bar(
        top_produtos.head(20),
        x="faturamento",
        y="descricao_produto",
        orientation="h",
        title="Top 20 produtos por faturamento"
    )
    fig_prod_fat.update_layout(yaxis={"categoryorder": "total ascending"})
    col1.plotly_chart(fig_prod_fat, width="stretch")

    fig_prod_qtd = px.bar(
        top_produtos.sort_values("quantidade", ascending=False).head(20),
        x="quantidade",
        y="descricao_produto",
        orientation="h",
        title="Top 20 produtos por quantidade"
    )
    fig_prod_qtd.update_layout(yaxis={"categoryorder": "total ascending"})
    col2.plotly_chart(fig_prod_qtd, width="stretch")

    abc = top_produtos.copy()
    total_abc = abc["faturamento"].sum()

    if total_abc > 0:
        abc["percentual"] = abc["faturamento"] / total_abc
        abc["percentual_acumulado"] = abc["percentual"].cumsum()

        def classe_abc(valor):
            if valor <= 0.80:
                return "A"
            if valor <= 0.95:
                return "B"
            return "C"

        abc["classe_abc"] = abc["percentual_acumulado"].apply(classe_abc)

        resumo_abc = (
            abc
            .groupby("classe_abc", as_index=False)
            .agg(
                produtos=("codigo_produto", "count"),
                faturamento=("faturamento", "sum")
            )
        )

        fig_abc = px.pie(
            resumo_abc,
            names="classe_abc",
            values="faturamento",
            title="Curva ABC por faturamento"
        )

        st.plotly_chart(fig_abc, width="stretch")
        st.dataframe(abc, width="stretch")
    else:
        st.info("Sem dados suficientes para Curva ABC.")

with aba_cli:
    top_clientes = (
        base_pedidos
        .groupby(["assessor", "cliente", "cpf_cnpj_cliente", "cidade", "uf"], as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique"),
            ticket_medio=("total_pedido", "mean")
        )
        .sort_values("faturamento", ascending=False)
    )

    recorrentes = top_clientes[top_clientes["pedidos"] >= 2].copy()

    col1, col2 = st.columns(2)

    col1.metric("Clientes recorrentes", numero(len(recorrentes)))

    percentual_recorrentes = (
        len(recorrentes) / len(top_clientes) * 100
        if len(top_clientes)
        else 0
    )

    col2.metric("% recorrentes", f"{percentual_recorrentes:.2f}%")

    st.subheader("Top clientes")
    st.dataframe(top_clientes.head(200), width="stretch")

    st.subheader("Clientes recorrentes")
    st.dataframe(recorrentes, width="stretch")

with aba_alertas:
    st.subheader("Alertas inteligentes")

    alertas = []

    if "Não identificado" in base_pedidos["canal"].astype(str).unique():
        alertas.append("⚠️ Existem pedidos com canal não identificado.")

    if "SEM ASSESSOR" in base_pedidos["assessor"].astype(str).unique():
        alertas.append("⚠️ Existem pedidos sem assessor vinculado.")

    sem_cliente = base_pedidos[
        base_pedidos["cliente"].isna()
        | (base_pedidos["cliente"].astype(str).str.strip() == "")
    ]

    if len(sem_cliente) > 0:
        alertas.append(f"⚠️ Existem {len(sem_cliente)} pedidos sem cliente.")

    sem_uf = base_pedidos[
        base_pedidos["uf"].isna()
        | (base_pedidos["uf"].astype(str).str.strip() == "")
    ]

    if len(sem_uf) > 0:
        alertas.append(f"⚠️ Existem {len(sem_uf)} pedidos sem UF.")

    if ticket_medio > 0:
        baixo_ticket = base_pedidos[
            base_pedidos["total_pedido"] < ticket_medio * 0.3
        ]

        if len(baixo_ticket) > 0:
            alertas.append(
                f"ℹ️ {len(baixo_ticket)} pedidos estão muito abaixo do ticket médio."
            )

    baixo_giro = (
        base_itens
        .groupby(["codigo_produto", "descricao_produto"], as_index=False)
        .agg(
            quantidade=("quantidade", "sum"),
            faturamento=("valor_total_item", "sum")
        )
    )

    baixo_giro = baixo_giro[
        (baixo_giro["quantidade"] <= 1)
        & (baixo_giro["faturamento"] > 0)
    ]

    if len(baixo_giro) > 0:
        alertas.append(
            f"ℹ️ {len(baixo_giro)} produtos tiveram venda de apenas 1 unidade."
        )

    if alertas:
        for alerta in alertas:
            st.warning(alerta)
    else:
        st.success("Nenhum alerta crítico encontrado nos filtros atuais.")

with aba_dados:
    st.subheader("Base de pedidos")
    st.dataframe(base_pedidos.head(1000), width="stretch")

    st.subheader("Base de itens")
    st.dataframe(base_itens.head(1000), width="stretch")