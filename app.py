from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# =====================================================
# CONFIG
# =====================================================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGO_PATH = BASE_DIR / "logo.png"

st.set_page_config(
    page_title="E-Factor BI",
    page_icon="📊",
    layout="wide"
)

# =====================================================
# CSS
# =====================================================

st.markdown("""
<style>

.block-container{
    padding-top:1rem;
    padding-bottom:2rem;
}

.big-title{
    font-size:40px;
    font-weight:800;
    margin-bottom:0;
}

.sub-title{
    font-size:20px;
    color:#9CA3AF;
    margin-top:-8px;
}

.pill{
    display:inline-block;
    padding:10px 18px;
    border-radius:25px;
    border:1px solid rgba(255,255,255,0.15);
    margin-right:10px;
    font-size:18px;
}

.kpi-card{
    border-radius:18px;
    padding:24px;
    background:rgba(255,255,255,0.03);
    border:1px solid rgba(255,255,255,0.06);
}

.kpi-title{
    font-size:18px;
    color:#9CA3AF;
}

.kpi-value{
    font-size:42px;
    font-weight:700;
}

.status-green{
    color:#00C853;
    font-weight:700;
}

.status-yellow{
    color:#FFD600;
    font-weight:700;
}

.status-red{
    color:#FF5252;
    font-weight:700;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# FUNÇÕES
# =====================================================

def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def numero(valor):
    try:
        return f"{float(valor):,.0f}".replace(",", ".")
    except:
        return "0"

def percentual(valor):
    try:
        return f"{float(valor)*100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,00%"

def carregar_csv(nome):
    caminho = DATA_DIR / nome

    if caminho.exists():
        return pd.read_csv(caminho)

    return pd.DataFrame()

def formatar_dataframe(df):

    df = df.copy()

    for col in df.columns:

        col_lower = col.lower()

        if any(x in col_lower for x in [
            "faturamento",
            "valor",
            "ticket",
            "meta",
            "realizado",
            "projecao",
            "gap",
            "ritmo"
        ]):

            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].apply(moeda)

        if any(x in col_lower for x in [
            "percentual",
            "participacao",
            "share"
        ]):

            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].apply(percentual)

    return df

# =====================================================
# LEITURA
# =====================================================

pedidos = carregar_csv("pedidos.csv")
itens = carregar_csv("itens_pedido.csv")
metas = carregar_csv("metas_inteligentes.csv")

# =====================================================
# TRATAMENTO
# =====================================================

if "assessor" not in pedidos.columns:
    pedidos["assessor"] = "SEM ASSESSOR"

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

# =====================================================
# CABEÇALHO
# =====================================================

logo_col, title_col = st.columns([1,5])

with logo_col:

    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=130)

with title_col:

    st.markdown(
        '<div class="big-title">e-Factor Consultoria e Assessoria</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Painel Executivo MIOS</div>',
        unsafe_allow_html=True
    )

st.caption("Inteligência comercial multiempresa integrada ao Tiny ERP")

# =====================================================
# FILTROS
# =====================================================

st.sidebar.title("Filtros")

assessores = sorted(
    pedidos["assessor"].dropna().unique()
)

assessores_filtro = st.sidebar.multiselect(
    "Assessores",
    assessores,
    default=assessores
)

empresas = sorted(
    pedidos[
        pedidos["assessor"].isin(assessores_filtro)
    ]["empresa"].dropna().unique()
)

empresas_filtro = st.sidebar.multiselect(
    "Empresas",
    empresas,
    default=empresas
)

base_pedidos = pedidos[
    pedidos["assessor"].isin(assessores_filtro)
    &
    pedidos["empresa"].isin(empresas_filtro)
].copy()

ids = base_pedidos["id_pedido"].astype(str).unique()

base_itens = itens[
    itens["id_pedido"].astype(str).isin(ids)
].copy()

if not metas.empty:

    base_metas = metas[
        metas["assessor"].isin(assessores_filtro)
        &
        metas["empresa"].isin(empresas_filtro)
    ].copy()

else:

    base_metas = pd.DataFrame()

# =====================================================
# TOP BAR
# =====================================================

st.markdown(
    """
    <span class="pill">📅 mês atual</span>
    <span class="pill">🔎 filtros ativos</span>
    <span class="pill">↻ atualizado agora</span>
    """,
    unsafe_allow_html=True
)

st.divider()

# =====================================================
# KPIs
# =====================================================

faturamento = base_pedidos["total_pedido"].sum()

pedidos_total = base_pedidos["id_pedido"].nunique()

ticket_medio = base_pedidos["total_pedido"].mean()

clientes = base_pedidos["cpf_cnpj_cliente"].nunique()

itens_total = base_itens["quantidade"].sum()

meta_total = 0
realizado_total = 0
projecao_total = 0
percentual_meta = 0

if not base_metas.empty:

    meta_total = base_metas["meta"].sum()

    realizado_total = base_metas["realizado"].sum()

    projecao_total = base_metas["projecao_mes"].sum()

    percentual_meta = (
        realizado_total / meta_total
        if meta_total > 0
        else 0
    )

k1,k2,k3,k4,k5 = st.columns(5)

k1.metric(
    "Faturamento",
    moeda(faturamento)
)

k2.metric(
    "Meta mensal",
    moeda(meta_total)
)

k3.metric(
    "% meta",
    percentual(percentual_meta)
)

k4.metric(
    "Projeção",
    moeda(projecao_total)
)

k5.metric(
    "Pedidos",
    numero(pedidos_total)
)

st.caption(
    f"Última atualização visual: "
    f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
)

# =====================================================
# ABAS
# =====================================================

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

# =====================================================
# VENDAS
# =====================================================

with aba_vendas:

    vendas_dia = (
        base_pedidos
        .dropna(subset=["data_pedido_dt"])
        .groupby("data_pedido_dt", as_index=False)
        .agg(
            faturamento=("total_pedido","sum")
        )
        .sort_values("data_pedido_dt")
    )

    fig = px.area(
        vendas_dia,
        x="data_pedido_dt",
        y="faturamento",
        title="Faturamento Diário"
    )

    st.plotly_chart(fig, use_container_width=True)

    col1,col2 = st.columns(2)

    resumo_empresa = (
        base_pedidos
        .groupby("empresa", as_index=False)
        .agg(
            faturamento=("total_pedido","sum")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig_empresas = px.bar(
        resumo_empresa.head(15),
        x="empresa",
        y="faturamento",
        title="Top Empresas"
    )

    col1.plotly_chart(
        fig_empresas,
        use_container_width=True
    )

    resumo_canal = (
        base_pedidos
        .groupby("canal", as_index=False)
        .agg(
            faturamento=("total_pedido","sum")
        )
    )

    fig_canal = px.pie(
        resumo_canal,
        names="canal",
        values="faturamento",
        title="Share por Canal"
    )

    col2.plotly_chart(
        fig_canal,
        use_container_width=True
    )

# =====================================================
# METAS
# =====================================================

with aba_metas:

    st.subheader("Meta Inteligente")

    if base_metas.empty:

        st.warning("Nenhuma meta encontrada.")

    else:

        risco = len(
            base_metas[
                base_metas["status_meta"]
                .astype(str)
                .str.contains("RISCO")
            ]
        )

        atencao = len(
            base_metas[
                base_metas["status_meta"]
                .astype(str)
                .str.contains("ATEN")
            ]
        )

        saudavel = len(
            base_metas[
                base_metas["status_meta"]
                .astype(str)
                .str.contains("SAUD")
            ]
        )

        c1,c2,c3,c4 = st.columns(4)

        c1.metric("🔴 Risco", numero(risco))
        c2.metric("🟡 Atenção", numero(atencao))
        c3.metric("🟢 Saudável", numero(saudavel))
        c4.metric("Meta Total", moeda(meta_total))

        ranking = (
            base_metas
            .sort_values(
                "percentual_projetado",
                ascending=True
            )
        )

        fig_meta = px.bar(
            ranking,
            x="empresa",
            y="percentual_projetado",
            color="status_meta",
            title="Projeção de Atingimento"
        )

        st.plotly_chart(
            fig_meta,
            use_container_width=True
        )

        tabela = ranking[[
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
        ]]

        st.dataframe(
            formatar_dataframe(tabela),
            use_container_width=True
        )

# =====================================================
# ASSESSORES
# =====================================================

with aba_assessor:

    ranking = (
        base_pedidos
        .groupby("assessor", as_index=False)
        .agg(
            faturamento=("total_pedido","sum"),
            pedidos=("id_pedido","nunique"),
            clientes=("cpf_cnpj_cliente","nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig = px.bar(
        ranking,
        x="assessor",
        y="faturamento",
        title="Faturamento por Assessor"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        formatar_dataframe(ranking),
        use_container_width=True
    )

# =====================================================
# EMPRESAS
# =====================================================

with aba_empresas:

    ranking = (
        base_pedidos
        .groupby(["assessor","empresa"], as_index=False)
        .agg(
            faturamento=("total_pedido","sum"),
            pedidos=("id_pedido","nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig = px.bar(
        ranking.head(20),
        x="empresa",
        y="faturamento",
        color="assessor",
        title="Ranking Empresas"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        formatar_dataframe(ranking),
        use_container_width=True
    )

# =====================================================
# PRODUTOS
# =====================================================

with aba_produtos:

    ranking = (
        base_itens
        .groupby(
            ["codigo_produto","descricao_produto"],
            as_index=False
        )
        .agg(
            faturamento=("valor_total_item","sum"),
            quantidade=("quantidade","sum")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig = px.bar(
        ranking.head(20),
        x="faturamento",
        y="descricao_produto",
        orientation="h",
        title="Top Produtos"
    )

    fig.update_layout(
        yaxis={"categoryorder":"total ascending"}
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.dataframe(
        formatar_dataframe(ranking),
        use_container_width=True
    )

# =====================================================
# CLIENTES
# =====================================================

with aba_clientes:

    ranking = (
        base_pedidos
        .groupby(
            ["cliente","cpf_cnpj_cliente"],
            as_index=False
        )
        .agg(
            faturamento=("total_pedido","sum"),
            pedidos=("id_pedido","nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    st.dataframe(
        formatar_dataframe(ranking),
        use_container_width=True
    )

# =====================================================
# ALERTAS
# =====================================================

with aba_alertas:

    if not base_metas.empty:

        risco = base_metas[
            base_metas["status_meta"]
            .astype(str)
            .str.contains("RISCO")
        ]

        if len(risco):

            for _,row in risco.iterrows():

                st.warning(
                    f"{row['empresa']} "
                    f"está em risco. "
                    f"Projetado: "
                    f"{percentual(row['percentual_projetado'])}"
                )

        else:

            st.success(
                "Nenhuma empresa em risco."
            )

# =====================================================
# DADOS
# =====================================================

with aba_dados:

    st.subheader("Pedidos")

    st.dataframe(
        formatar_dataframe(base_pedidos.head(1000)),
        use_container_width=True
    )

    st.subheader("Itens")

    st.dataframe(
        formatar_dataframe(base_itens.head(1000)),
        use_container_width=True
    )

    if not base_metas.empty:

        st.subheader("Metas")

        st.dataframe(
            formatar_dataframe(base_metas),
            use_container_width=True
        )