from pathlib import Path
from datetime import datetime
import unicodedata

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
LOCAL_RAW_DIR = ROOT_DIR / "data" / "raw"
LOCAL_CONFIG_DIR = ROOT_DIR / "config"
LOGO_PATH = BASE_DIR / "logo.png"


st.set_page_config(
    page_title="E-Factor BI",
    page_icon="📊",
    layout="wide"
)


st.markdown("""
<style>
.block-container { padding-top: 1rem; }
.big-title { font-size: 38px; font-weight: 800; }
.sub-title { font-size: 18px; color: #9CA3AF; margin-top: -10px; }
.pill {
    display:inline-block;
    padding:8px 16px;
    border-radius:22px;
    border:1px solid rgba(255,255,255,0.15);
    margin-right:10px;
}
</style>
""", unsafe_allow_html=True)


def caminho_arquivo(nome):
    for caminho in [
        LOCAL_RAW_DIR / nome,
        LOCAL_CONFIG_DIR / nome,
        DATA_DIR / nome,
    ]:
        if caminho.exists():
            return caminho
    return DATA_DIR / nome


def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).upper().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return " ".join(texto.split())


def moeda_para_float(valor):
    if pd.isna(valor):
        return 0.0
    valor = str(valor).replace("R$", "").replace(" ", "").strip()
    if "," in valor:
        valor = valor.replace(".", "").replace(",", ".")
    try:
        return float(valor)
    except Exception:
        return 0.0


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


@st.cache_data
def carregar_pedidos():
    df = pd.read_csv(caminho_arquivo("pedidos_historico.csv"), low_memory=False)

    df["empresa_normalizada"] = df["empresa"].apply(normalizar)

    df["data_pedido_dt"] = pd.to_datetime(
        df["data_pedido"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    df["ano"] = df["data_pedido_dt"].dt.year
    df["mes"] = df["data_pedido_dt"].dt.month

    df["total_pedido"] = pd.to_numeric(
        df["total_pedido"],
        errors="coerce"
    ).fillna(0)

    if "tipo_venda" not in df.columns:
        df["tipo_venda"] = "DIGITAL"

    if "canal_padronizado" not in df.columns:
        df["canal_padronizado"] = "Marketplace Não Identificado"

    df["tipo_venda"] = df["tipo_venda"].astype(str).str.upper().str.strip()
    df["canal_padronizado"] = df["canal_padronizado"].fillna("Marketplace Não Identificado")

    # Regra oficial MIOS: operação analisada = venda digital
    df = df[df["tipo_venda"] == "DIGITAL"].copy()

    return df


@st.cache_data
def carregar_clientes():
    df = pd.read_csv(caminho_arquivo("clientes.csv"), sep=";", low_memory=False)

    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["EMPRESA"]).copy()

    df["EMPRESA"] = df["EMPRESA"].astype(str).str.strip()
    df["ASSESSOR"] = df["ASSESSOR"].astype(str).str.strip().str.upper()
    df["STATUS"] = df["STATUS"].astype(str).str.strip().str.upper()
    df["empresa_normalizada"] = df["EMPRESA"].apply(normalizar)

    for col in ["CONTRATO", "COMISSÃO"]:
        if col in df.columns:
            df[col] = df[col].apply(moeda_para_float)
        else:
            df[col] = 0.0

    meses = {
        1: "JANEIRO",
        2: "FEVEREIRO",
        3: "MARÇO",
        4: "ABRIL",
        5: "MAIO",
        6: "JUNHO",
        7: "JULHO",
        8: "AGOSTO",
        9: "SETEMBRO",
        10: "OUTUBRO",
        11: "NOVEMBRO",
        12: "DEZEMBRO",
    }

    for mes_num, mes_nome in meses.items():
        if mes_nome in df.columns:
            df[f"meta_{mes_num}"] = df[mes_nome].apply(moeda_para_float)
        else:
            df[f"meta_{mes_num}"] = 0.0

    return df


pedidos = carregar_pedidos()
clientes = carregar_clientes()


# =========================
# CABEÇALHO
# =========================

col_logo, col_titulo = st.columns([1, 5])

with col_logo:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=120)

with col_titulo:
    st.markdown(
        '<div class="big-title">e-Factor Consultoria e Assessoria</div>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<div class="sub-title">Painel Executivo MIOS — Operação Digital</div>',
        unsafe_allow_html=True
    )

st.caption("Inteligência comercial multiempresa integrada ao Tiny ERP")


# =========================
# FILTROS
# =========================

st.sidebar.title("Filtros")

anos = sorted(pedidos["ano"].dropna().astype(int).unique())

if not anos:
    st.error("Nenhum pedido digital encontrado na base.")
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

assessores = sorted(clientes["ASSESSOR"].dropna().unique())

assessores_filtro = st.sidebar.multiselect(
    "Assessores",
    assessores,
    default=assessores
)

status_clientes = sorted(clientes["STATUS"].dropna().unique())

status_filtro = st.sidebar.multiselect(
    "Status cliente",
    status_clientes,
    default=status_clientes
)

canais = sorted(pedidos["canal_padronizado"].dropna().unique())

canais_filtro = st.sidebar.multiselect(
    "Canal digital",
    canais,
    default=canais
)

clientes_filtrados = clientes[
    clientes["ASSESSOR"].isin(assessores_filtro)
    & clientes["STATUS"].isin(status_filtro)
].copy()

empresas_disponiveis = sorted(clientes_filtrados["EMPRESA"].dropna().unique())

empresas_filtro = st.sidebar.multiselect(
    "Empresas",
    empresas_disponiveis,
    default=empresas_disponiveis
)

empresas_norm_filtro = clientes_filtrados[
    clientes_filtrados["EMPRESA"].isin(empresas_filtro)
]["empresa_normalizada"].unique()


# =========================
# BASE FILTRADA
# =========================

base = pedidos[pedidos["ano"] == ano_filtro].copy()

if mes_filtro != "Todos":
    base = base[base["mes"] == int(mes_filtro)].copy()

base = base[
    base["empresa_normalizada"].isin(empresas_norm_filtro)
    & base["canal_padronizado"].isin(canais_filtro)
].copy()

base = base.merge(
    clientes[[
        "empresa_normalizada",
        "EMPRESA",
        "ASSESSOR",
        "STATUS",
        "CONTRATO",
        "COMISSÃO",
        "meta_1",
        "meta_2",
        "meta_3",
        "meta_4",
        "meta_5",
        "meta_6",
        "meta_7",
        "meta_8",
        "meta_9",
        "meta_10",
        "meta_11",
        "meta_12",
    ]],
    on="empresa_normalizada",
    how="left"
)

if mes_filtro == "Todos":
    metas_ref = clientes_filtrados[
        clientes_filtrados["EMPRESA"].isin(empresas_filtro)
    ].copy()

    colunas_meta = [f"meta_{m}" for m in meses_disponiveis]
    metas_ref["meta_periodo"] = metas_ref[colunas_meta].sum(axis=1)

else:
    metas_ref = clientes_filtrados[
        clientes_filtrados["EMPRESA"].isin(empresas_filtro)
    ].copy()

    metas_ref["meta_periodo"] = metas_ref[f"meta_{int(mes_filtro)}"]


# =========================
# TOP BAR
# =========================

st.markdown(
    '<span class="pill">🛒 operação digital</span>'
    '<span class="pill">📅 período filtrado</span>'
    '<span class="pill">🔎 filtros ativos</span>'
    '<span class="pill">↻ atualizado agora</span>',
    unsafe_allow_html=True
)

st.divider()


# =========================
# KPIS
# =========================

faturamento = base["total_pedido"].sum()
pedidos_qtd = base["id_pedido"].nunique()
clientes_qtd = base["cpf_cnpj_cliente"].nunique() if "cpf_cnpj_cliente" in base.columns else 0

meta_total = metas_ref["meta_periodo"].sum()
contrato_total = metas_ref["CONTRATO"].sum()
comissao_total = metas_ref["COMISSÃO"].sum()

percentual_meta = faturamento / meta_total if meta_total > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Faturamento Digital", moeda(faturamento))
k2.metric("Meta Digital", moeda(meta_total))
k3.metric("% Meta", percentual(percentual_meta))
k4.metric("Pedidos Digitais", numero(pedidos_qtd))
k5.metric("Clientes", numero(clientes_qtd))

st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# =========================
# ABAS
# =========================

aba_vendas, aba_metas, aba_canais, aba_temporal, aba_assessores, aba_clientes, aba_financeiro, aba_dados = st.tabs([
    "📈 Vendas",
    "🎯 Metas",
    "🛒 Canais",
    "📅 Temporal",
    "🧑‍💼 Assessores",
    "🏢 Clientes",
    "💰 Financeiro",
    "🧾 Dados"
])


# =========================
# VENDAS
# =========================

with aba_vendas:
    vendas_dia = (
        base.dropna(subset=["data_pedido_dt"])
        .groupby("data_pedido_dt", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique")
        )
        .sort_values("data_pedido_dt")
    )

    fig = px.area(
        vendas_dia,
        x="data_pedido_dt",
        y="faturamento",
        title="Faturamento digital diário"
    )

    st.plotly_chart(fig, width="stretch")

    col1, col2 = st.columns(2)

    resumo_canal = (
        base.groupby("canal_padronizado", as_index=False)
        .agg(faturamento=("total_pedido", "sum"))
        .sort_values("faturamento", ascending=False)
    )

    fig_canal = px.pie(
        resumo_canal,
        names="canal_padronizado",
        values="faturamento",
        title="Share por canal digital"
    )

    col1.plotly_chart(fig_canal, width="stretch")

    if "uf" in base.columns:
        resumo_uf = (
            base.groupby("uf", as_index=False)
            .agg(faturamento=("total_pedido", "sum"))
            .sort_values("faturamento", ascending=False)
        )

        fig_uf = px.bar(
            resumo_uf.head(15),
            x="uf",
            y="faturamento",
            title="Top UFs — digital"
        )

        col2.plotly_chart(fig_uf, width="stretch")


# =========================
# METAS
# =========================

with aba_metas:
    realizado = (
        base.groupby("empresa_normalizada", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique")
        )
    )

    metas_view = metas_ref.merge(
        realizado,
        on="empresa_normalizada",
        how="left"
    )

    metas_view["faturamento"] = metas_view["faturamento"].fillna(0)
    metas_view["pedidos"] = metas_view["pedidos"].fillna(0)

    metas_view["percentual_meta"] = metas_view.apply(
        lambda x: x["faturamento"] / x["meta_periodo"] if x["meta_periodo"] > 0 else 0,
        axis=1
    )

    metas_view["gap"] = metas_view["faturamento"] - metas_view["meta_periodo"]

    metas_view["status_meta"] = metas_view["percentual_meta"].apply(
        lambda x: "🟢 Saudável" if x >= 1 else ("🟡 Atenção" if x >= 0.85 else "🔴 Risco")
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("🔴 Risco", numero((metas_view["status_meta"] == "🔴 Risco").sum()))
    col2.metric("🟡 Atenção", numero((metas_view["status_meta"] == "🟡 Atenção").sum()))
    col3.metric("🟢 Saudável", numero((metas_view["status_meta"] == "🟢 Saudável").sum()))

    fig_meta = px.bar(
        metas_view.sort_values("percentual_meta", ascending=False),
        x="EMPRESA",
        y="percentual_meta",
        color="ASSESSOR",
        title="Atingimento de meta digital"
    )

    st.plotly_chart(fig_meta, width="stretch")

    tabela = metas_view[[
        "ASSESSOR",
        "STATUS",
        "EMPRESA",
        "meta_periodo",
        "faturamento",
        "percentual_meta",
        "gap",
        "pedidos",
        "status_meta"
    ]].copy()

    tabela["meta_periodo"] = tabela["meta_periodo"].apply(moeda)
    tabela["faturamento"] = tabela["faturamento"].apply(moeda)
    tabela["percentual_meta"] = tabela["percentual_meta"].apply(percentual)
    tabela["gap"] = tabela["gap"].apply(moeda)

    st.dataframe(tabela, width="stretch")


# =========================
# CANAIS
# =========================

with aba_canais:
    st.subheader("Performance por canal digital")

    canais_view = (
        base.groupby("canal_padronizado", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique"),
            clientes=("cpf_cnpj_cliente", "nunique") if "cpf_cnpj_cliente" in base.columns else ("id_pedido", "nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    total_canais = canais_view["faturamento"].sum()
    canais_view["participacao"] = canais_view["faturamento"] / total_canais if total_canais else 0

    fig_canais = px.bar(
        canais_view,
        x="canal_padronizado",
        y="faturamento",
        title="Ranking de canais digitais",
        text_auto=".2s"
    )

    st.plotly_chart(fig_canais, width="stretch")

    tabela_canais = canais_view.copy()
    tabela_canais["faturamento"] = tabela_canais["faturamento"].apply(moeda)
    tabela_canais["participacao"] = tabela_canais["participacao"].apply(percentual)

    st.dataframe(tabela_canais, width="stretch")


# =========================
# TEMPORAL
# =========================

with aba_temporal:
    temporal = pedidos.merge(
        clientes[["empresa_normalizada", "ASSESSOR", "STATUS", "EMPRESA"]],
        on="empresa_normalizada",
        how="left"
    )

    temporal = temporal[
        temporal["ASSESSOR"].isin(assessores_filtro)
        & temporal["STATUS"].isin(status_filtro)
        & temporal["empresa_normalizada"].isin(empresas_norm_filtro)
        & temporal["canal_padronizado"].isin(canais_filtro)
    ].copy()

    resumo = (
        temporal.groupby(["ano", "mes"], as_index=False)
        .agg(faturamento=("total_pedido", "sum"))
        .sort_values(["ano", "mes"])
    )

    resumo["mes_ano"] = (
        resumo["mes"].astype(int).astype(str).str.zfill(2)
        + "/"
        + resumo["ano"].astype(int).astype(str)
    )

    fig_temporal = px.line(
        resumo,
        x="mes_ano",
        y="faturamento",
        markers=True,
        title="Evolução mensal digital"
    )

    st.plotly_chart(fig_temporal, width="stretch")

    resumo["faturamento"] = resumo["faturamento"].apply(moeda)
    st.dataframe(resumo, width="stretch")


# =========================
# ASSESSORES
# =========================

with aba_assessores:
    ranking = (
        base.groupby("ASSESSOR", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique"),
            empresas=("EMPRESA", "nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig_assessor = px.bar(
        ranking,
        x="ASSESSOR",
        y="faturamento",
        title="Faturamento digital por assessor"
    )

    st.plotly_chart(fig_assessor, width="stretch")

    ranking["faturamento"] = ranking["faturamento"].apply(moeda)
    st.dataframe(ranking, width="stretch")


# =========================
# CLIENTES
# =========================

with aba_clientes:
    clientes_view = (
        base.groupby(["ASSESSOR", "STATUS", "EMPRESA"], as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique"),
            clientes=("cpf_cnpj_cliente", "nunique") if "cpf_cnpj_cliente" in base.columns else ("id_pedido", "nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    clientes_view["faturamento"] = clientes_view["faturamento"].apply(moeda)
    st.dataframe(clientes_view, width="stretch")


# =========================
# FINANCEIRO
# =========================

with aba_financeiro:
    col1, col2, col3 = st.columns(3)

    col1.metric("Contrato escritório", moeda(contrato_total))
    col2.metric("Comissão clientes", moeda(comissao_total))
    col3.metric("Clientes na carteira", numero(len(metas_ref)))

    financeiro = metas_ref[[
        "ASSESSOR",
        "STATUS",
        "EMPRESA",
        "CONTRATO",
        "COMISSÃO"
    ]].copy()

    financeiro["CONTRATO"] = financeiro["CONTRATO"].apply(moeda)
    financeiro["COMISSÃO"] = financeiro["COMISSÃO"].apply(moeda)

    st.dataframe(financeiro, width="stretch")


# =========================
# DADOS
# =========================

with aba_dados:
    st.subheader("Pedidos digitais filtrados")
    st.dataframe(base.head(1000), width="stretch")

    st.subheader("Cadastro de clientes")

    clientes_view = clientes.drop(
        columns=["CNPJ", "CHAVE API TINY"],
        errors="ignore"
    )

    st.dataframe(clientes_view, width="stretch")