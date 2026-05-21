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
}

.big-title{
    font-size:38px;
    font-weight:800;
}

.sub-title{
    font-size:18px;
    color:#9CA3AF;
    margin-top:-10px;
}

.pill{
    display:inline-block;
    padding:8px 16px;
    border-radius:22px;
    border:1px solid rgba(255,255,255,0.15);
    margin-right:10px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# FUNÇÕES
# =====================================================

def moeda_para_float(valor):

    if pd.isna(valor):
        return 0

    valor = str(valor)

    valor = (
        valor
        .replace("R$", "")
        .replace(".", "")
        .replace(",", ".")
        .strip()
    )

    try:
        return float(valor)
    except:
        return 0

def moeda(valor):

    try:

        return (
            f"R$ {float(valor):,.2f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except:

        return "R$ 0,00"

def percentual(valor):

    try:

        return (
            f"{float(valor)*100:,.2f}%"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    except:

        return "0,00%"

def numero(valor):

    try:

        return (
            f"{float(valor):,.0f}"
            .replace(",", ".")
        )

    except:

        return "0"

def normalizar_empresa(texto):

    if pd.isna(texto):
        return ""

    texto = str(texto).upper().strip()

    texto = (
        texto
        .replace("Ã", "A")
        .replace("Á", "A")
        .replace("À", "A")
        .replace("É", "E")
        .replace("Ê", "E")
        .replace("Í", "I")
        .replace("Ó", "O")
        .replace("Õ", "O")
        .replace("Ú", "U")
        .replace("Ç", "C")
    )

    texto = " ".join(texto.split())

    return texto

def carregar_csv(nome, sep=","):

    caminho = DATA_DIR / nome

    if caminho.exists():

        return pd.read_csv(
            caminho,
            sep=sep
        )

    return pd.DataFrame()

# =====================================================
# LEITURA
# =====================================================

pedidos = carregar_csv("pedidos_historico.csv")

itens = carregar_csv("itens_pedido_historico.csv")

clientes = carregar_csv(
    "clientes.csv",
    sep=";"
)

# =====================================================
# LIMPEZA
# =====================================================

clientes.columns = (
    clientes.columns
    .str.strip()
)

clientes = clientes.dropna(
    subset=["EMPRESA"]
)

# =====================================================
# NORMALIZAÇÃO
# =====================================================

pedidos["empresa_normalizada"] = (
    pedidos["empresa"]
    .apply(normalizar_empresa)
)

clientes["empresa_normalizada"] = (
    clientes["EMPRESA"]
    .apply(normalizar_empresa)
)

# =====================================================
# DATAS
# =====================================================

pedidos["data_pedido_dt"] = pd.to_datetime(
    pedidos["data_pedido"],
    format="%d/%m/%Y",
    errors="coerce"
)

pedidos["ano"] = (
    pedidos["data_pedido_dt"]
    .dt.year
)

pedidos["mes"] = (
    pedidos["data_pedido_dt"]
    .dt.month
)

# =====================================================
# VALORES
# =====================================================

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

# =====================================================
# META MAIO
# =====================================================

clientes["meta"] = (
    clientes["MAIO"]
    .apply(moeda_para_float)
)

clientes["contrato"] = (
    clientes["CONTRATO"]
    .apply(moeda_para_float)
)

clientes["comissao"] = (
    clientes["COMISSÃO"]
    .apply(moeda_para_float)
)

# =====================================================
# MERGE
# =====================================================

base = pedidos.merge(
    clientes,
    on="empresa_normalizada",
    how="left"
)

# =====================================================
# CABEÇALHO
# =====================================================

col1,col2 = st.columns([1,5])

with col1:

    if LOGO_PATH.exists():

        st.image(
            str(LOGO_PATH),
            width=120
        )

with col2:

    st.markdown(
        '<div class="big-title">e-Factor Consultoria e Assessoria</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Painel Executivo MIOS</div>',
        unsafe_allow_html=True
    )

st.caption(
    "Inteligência comercial multiempresa integrada ao Tiny ERP"
)

# =====================================================
# FILTROS
# =====================================================

st.sidebar.title("Filtros")

anos = sorted(
    base["ano"]
    .dropna()
    .unique()
)

ano_filtro = st.sidebar.selectbox(
    "Ano",
    anos,
    index=len(anos)-1
)

meses = sorted(
    base[
        base["ano"] == ano_filtro
    ]["mes"].dropna().unique()
)

mes_filtro = st.sidebar.selectbox(
    "Mês",
    meses,
    index=len(meses)-1
)

assessores = sorted(
    base["ASSESSOR"]
    .dropna()
    .unique()
)

assessores_filtro = st.sidebar.multiselect(
    "Assessores",
    assessores,
    default=assessores
)

status_cliente = sorted(
    base["STATUS"]
    .dropna()
    .unique()
)

status_filtro = st.sidebar.multiselect(
    "Status",
    status_cliente,
    default=status_cliente
)

empresas = sorted(
    base["EMPRESA"]
    .dropna()
    .unique()
)

empresas_filtro = st.sidebar.multiselect(
    "Empresas",
    empresas,
    default=empresas
)

# =====================================================
# FILTRO BASE
# =====================================================

base = base[
    (base["ano"] == ano_filtro)
    &
    (base["mes"] == mes_filtro)
    &
    (base["ASSESSOR"].isin(assessores_filtro))
    &
    (base["STATUS"].isin(status_filtro))
    &
    (base["EMPRESA"].isin(empresas_filtro))
].copy()

# =====================================================
# KPIS
# =====================================================

faturamento = (
    base["total_pedido"]
    .sum()
)

meta_total = (
    base["meta"]
    .drop_duplicates()
    .sum()
)

contrato_total = (
    base["contrato"]
    .drop_duplicates()
    .sum()
)

comissao_total = (
    base["comissao"]
    .drop_duplicates()
    .sum()
)

clientes_total = (
    base["EMPRESA"]
    .nunique()
)

percentual_meta = (
    faturamento / meta_total
    if meta_total > 0
    else 0
)

k1,k2,k3,k4,k5 = st.columns(5)

k1.metric(
    "Faturamento",
    moeda(faturamento)
)

k2.metric(
    "Meta",
    moeda(meta_total)
)

k3.metric(
    "% Meta",
    percentual(percentual_meta)
)

k4.metric(
    "Contrato Escritório",
    moeda(contrato_total)
)

k5.metric(
    "Comissão",
    moeda(comissao_total)
)

st.caption(
    f"Atualizado em "
    f"{datetime.now().strftime('%d/%m/%Y %H:%M')}"
)

# =====================================================
# ABAS
# =====================================================

aba_vendas, aba_metas, aba_temporal, aba_assessores, aba_clientes = st.tabs([
    "📈 Vendas",
    "🎯 Metas",
    "📅 Temporal",
    "🧑‍💼 Assessores",
    "🏢 Clientes"
])

# =====================================================
# VENDAS
# =====================================================

with aba_vendas:

    vendas_dia = (
        base
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

    st.plotly_chart(
        fig,
        width="stretch"
    )

# =====================================================
# METAS
# =====================================================

with aba_metas:

    metas = (
        base
        .groupby(
            [
                "ASSESSOR",
                "EMPRESA",
                "meta"
            ],
            as_index=False
        )
        .agg(
            faturamento=("total_pedido","sum")
        )
    )

    metas["percentual_meta"] = (
        metas["faturamento"]
        /
        metas["meta"]
    )

    metas["gap"] = (
        metas["faturamento"]
        -
        metas["meta"]
    )

    fig = px.bar(
        metas.sort_values(
            "percentual_meta",
            ascending=False
        ),
        x="EMPRESA",
        y="percentual_meta",
        color="ASSESSOR",
        title="Atingimento de Meta"
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    metas_view = metas.copy()

    metas_view["faturamento"] = (
        metas_view["faturamento"]
        .apply(moeda)
    )

    metas_view["meta"] = (
        metas_view["meta"]
        .apply(moeda)
    )

    metas_view["percentual_meta"] = (
        metas_view["percentual_meta"]
        .apply(percentual)
    )

    metas_view["gap"] = (
        metas_view["gap"]
        .apply(moeda)
    )

    st.dataframe(
        metas_view,
        width="stretch"
    )

# =====================================================
# TEMPORAL
# =====================================================

with aba_temporal:

    temporal = (
        pedidos
        .groupby(
            ["ano","mes"],
            as_index=False
        )
        .agg(
            faturamento=("total_pedido","sum")
        )
        .sort_values(
            ["ano","mes"]
        )
    )

    temporal["mes_ano"] = (
        temporal["mes"]
        .astype(str)
        .str.zfill(2)
        +
        "/"
        +
        temporal["ano"]
        .astype(str)
    )

    fig = px.line(
        temporal,
        x="mes_ano",
        y="faturamento",
        markers=True,
        title="Evolução Mensal"
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

# =====================================================
# ASSESSORES
# =====================================================

with aba_assessores:

    ranking = (
        base
        .groupby("ASSESSOR", as_index=False)
        .agg(
            faturamento=("total_pedido","sum"),
            empresas=("EMPRESA","nunique")
        )
        .sort_values(
            "faturamento",
            ascending=False
        )
    )

    fig = px.bar(
        ranking,
        x="ASSESSOR",
        y="faturamento",
        title="Faturamento por Assessor"
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

    ranking["faturamento"] = (
        ranking["faturamento"]
        .apply(moeda)
    )

    st.dataframe(
        ranking,
        width="stretch"
    )

# =====================================================
# CLIENTES
# =====================================================

with aba_clientes:

    clientes_view = (
        base
        .groupby(
            [
                "ASSESSOR",
                "STATUS",
                "EMPRESA",
                "meta",
                "contrato",
                "comissao"
            ],
            as_index=False
        )
        .agg(
            faturamento=("total_pedido","sum"),
            pedidos=("id_pedido","nunique")
        )
    )

    clientes_view["faturamento"] = (
        clientes_view["faturamento"]
        .apply(moeda)
    )

    clientes_view["meta"] = (
        clientes_view["meta"]
        .apply(moeda)
    )

    clientes_view["contrato"] = (
        clientes_view["contrato"]
        .apply(moeda)
    )

    clientes_view["comissao"] = (
        clientes_view["comissao"]
        .apply(moeda)
    )

    st.dataframe(
        clientes_view,
        width="stretch"
    )