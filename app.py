from pathlib import Path
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

APP_DIR = Path(__file__).parent
PROJECT_DIR = APP_DIR.parent
LOCAL_RAW_DIR = PROJECT_DIR / "data" / "raw"
LOCAL_CONFIG_DIR = PROJECT_DIR / "config"
CLOUD_DATA_DIR = APP_DIR / "data"
LOGO_PATH = APP_DIR / "logo.png"

def escolher_arquivo(nome, tipo="data"):
    local = (LOCAL_CONFIG_DIR / nome) if tipo == "config" else (LOCAL_RAW_DIR / nome)
    cloud = CLOUD_DATA_DIR / nome
    if local.exists():
        return local
    if cloud.exists():
        return cloud
    return local

CLIENTES_PATH = escolher_arquivo("clientes.csv", tipo="config")
PEDIDOS_PATH = escolher_arquivo("pedidos_historico.csv", tipo="data")
ITENS_PATH = escolher_arquivo("itens_pedido_historico.csv", tipo="data")

st.set_page_config(page_title="E-Factor BI", page_icon="📊", layout="wide")

st.markdown('''
<style>
.block-container{padding-top:1rem;}
.big-title{font-size:38px;font-weight:800;}
.sub-title{font-size:18px;color:#9CA3AF;margin-top:-10px;}
.pill{display:inline-block;padding:8px 16px;border-radius:22px;border:1px solid rgba(255,255,255,0.15);margin-right:10px;}
</style>
''', unsafe_allow_html=True)

def moeda_para_float(valor):
    if pd.isna(valor):
        return 0.0
    valor = str(valor).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(valor)
    except Exception:
        return 0.0

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

def normalizar_empresa(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).upper().strip()
    for antigo, novo in {
        "Á":"A","À":"A","Â":"A","Ã":"A",
        "É":"E","Ê":"E","Í":"I",
        "Ó":"O","Ô":"O","Õ":"O",
        "Ú":"U","Ç":"C"
    }.items():
        texto = texto.replace(antigo, novo)
    return " ".join(texto.split())

@st.cache_data
def ler_csv(caminho, sep=","):
    return pd.read_csv(caminho, sep=sep)

def validar_arquivos():
    faltantes = []
    for nome, caminho in {
        "clientes.csv": CLIENTES_PATH,
        "pedidos_historico.csv": PEDIDOS_PATH,
        "itens_pedido_historico.csv": ITENS_PATH,
    }.items():
        if not caminho.exists():
            faltantes.append(f"{nome} -> {caminho}")
    if faltantes:
        st.error("Arquivos obrigatórios não encontrados.")
        for item in faltantes:
            st.code(item)
        st.stop()

def preparar_clientes(df):
    df = df.copy()
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=["EMPRESA"])
    df["EMPRESA"] = df["EMPRESA"].astype(str).str.strip()
    df["ASSESSOR"] = df["ASSESSOR"].astype(str).str.strip().str.upper()
    df["STATUS"] = df["STATUS"].astype(str).str.strip().str.upper()
    df["empresa_normalizada"] = df["EMPRESA"].apply(normalizar_empresa)

    df["contrato"] = df["CONTRATO"].apply(moeda_para_float) if "CONTRATO" in df.columns else 0.0
    df["comissao"] = df["COMISSÃO"].apply(moeda_para_float) if "COMISSÃO" in df.columns else 0.0

    meses = {
        1:"JANEIRO", 2:"FEVEREIRO", 3:"MARÇO", 4:"ABRIL",
        5:"MAIO", 6:"JUNHO", 7:"JULHO", 8:"AGOSTO",
        9:"SETEMBRO", 10:"OUTUBRO", 11:"NOVEMBRO", 12:"DEZEMBRO"
    }
    for mes_num, mes_nome in meses.items():
        df[f"meta_{mes_num}"] = df[mes_nome].apply(moeda_para_float) if mes_nome in df.columns else 0.0
    return df

def preparar_pedidos(df):
    df = df.copy()
    df["empresa"] = df["empresa"].astype(str).str.strip()
    df["empresa_normalizada"] = df["empresa"].apply(normalizar_empresa)
    df["data_pedido_dt"] = pd.to_datetime(df["data_pedido"], format="%d/%m/%Y", errors="coerce")
    df["ano"] = df["data_pedido_dt"].dt.year
    df["mes"] = df["data_pedido_dt"].dt.month
    df["total_pedido"] = pd.to_numeric(df["total_pedido"], errors="coerce").fillna(0)
    return df

def preparar_itens(df):
    df = df.copy()
    df["valor_total_item"] = pd.to_numeric(df["valor_total_item"], errors="coerce").fillna(0)
    df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0)
    return df

def status_meta(valor):
    if valor >= 1:
        return "🟢 SAUDÁVEL"
    if valor >= 0.85:
        return "🟡 ATENÇÃO"
    return "🔴 RISCO"

validar_arquivos()

try:
    clientes_raw = ler_csv(CLIENTES_PATH, sep=";")
except Exception:
    clientes_raw = pd.read_csv(CLIENTES_PATH, sep=None, engine="python")

pedidos_raw = ler_csv(PEDIDOS_PATH)
itens_raw = ler_csv(ITENS_PATH)

clientes = preparar_clientes(clientes_raw)
pedidos = preparar_pedidos(pedidos_raw)
itens = preparar_itens(itens_raw)

base_completa = pedidos.merge(clientes, on="empresa_normalizada", how="left", suffixes=("", "_cadastro"))

col1, col2 = st.columns([1, 5])
with col1:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), width=120)
with col2:
    st.markdown('<div class="big-title">e-Factor Consultoria e Assessoria</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Painel Executivo MIOS</div>', unsafe_allow_html=True)

st.caption("Inteligência comercial multiempresa integrada ao Tiny ERP")

st.sidebar.title("Filtros")

anos = sorted(base_completa["ano"].dropna().unique())
if not anos:
    st.error("Nenhum pedido com data válida encontrado.")
    st.stop()

ano_filtro = st.sidebar.selectbox("Ano", anos, index=len(anos) - 1)

meses = sorted(base_completa[base_completa["ano"] == ano_filtro]["mes"].dropna().unique())
mes_filtro = st.sidebar.selectbox("Mês", meses, index=len(meses) - 1)

base_pre = base_completa[(base_completa["ano"] == ano_filtro) & (base_completa["mes"] == mes_filtro)].copy()

assessores = sorted(base_pre["ASSESSOR"].dropna().unique())
status_cliente = sorted(base_pre["STATUS"].dropna().unique())
empresas = sorted(base_pre["EMPRESA"].dropna().unique())

assessores_filtro = st.sidebar.multiselect("Assessores", assessores, default=assessores)
status_filtro = st.sidebar.multiselect("Status cliente", status_cliente, default=status_cliente)
empresas_filtro = st.sidebar.multiselect("Empresas", empresas, default=empresas)

canais = sorted(base_pre["canal"].dropna().unique()) if "canal" in base_pre.columns else []
ufs = sorted(base_pre["uf"].dropna().unique()) if "uf" in base_pre.columns else []

canais_filtro = st.sidebar.multiselect("Canais", canais, default=canais)
ufs_filtro = st.sidebar.multiselect("UF", ufs, default=ufs)

base = base_pre[
    base_pre["ASSESSOR"].isin(assessores_filtro)
    & base_pre["STATUS"].isin(status_filtro)
    & base_pre["EMPRESA"].isin(empresas_filtro)
].copy()

if canais:
    base = base[base["canal"].isin(canais_filtro)]
if ufs:
    base = base[base["uf"].isin(ufs_filtro)]

ids_pedidos = base["id_pedido"].astype(str).unique()
itens_filtrados = itens[itens["id_pedido"].astype(str).isin(ids_pedidos)].copy()

meta_coluna = f"meta_{int(mes_filtro)}"

clientes_mes = clientes.copy()
clientes_mes["meta_mes"] = clientes_mes[meta_coluna] if meta_coluna in clientes_mes.columns else 0.0
clientes_mes = clientes_mes[
    clientes_mes["ASSESSOR"].isin(assessores_filtro)
    & clientes_mes["STATUS"].isin(status_filtro)
    & clientes_mes["EMPRESA"].isin(empresas_filtro)
].copy()

faturamento = base["total_pedido"].sum()
pedidos_total = base["id_pedido"].nunique()
meta_total = clientes_mes["meta_mes"].sum()
contrato_total = clientes_mes["contrato"].sum()
comissao_total = clientes_mes["comissao"].sum()
percentual_meta = faturamento / meta_total if meta_total > 0 else 0

st.markdown(
    '<span class="pill">📅 histórico desde janeiro</span>'
    '<span class="pill">🔎 filtros ativos</span>'
    '<span class="pill">↻ arquitetura MIOS</span>',
    unsafe_allow_html=True
)

st.divider()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Faturamento", moeda(faturamento))
k2.metric("Meta", moeda(meta_total))
k3.metric("% Meta", percentual(percentual_meta))
k4.metric("Contrato Escritório", moeda(contrato_total))
k5.metric("Comissão", moeda(comissao_total))

st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

aba_vendas, aba_metas, aba_temporal, aba_assessores, aba_clientes, aba_dados = st.tabs([
    "📈 Vendas",
    "🎯 Metas",
    "📅 Temporal",
    "🧑‍💼 Assessores",
    "🏢 Clientes",
    "🧾 Dados"
])

with aba_vendas:
    vendas_dia = (
        base.groupby("data_pedido_dt", as_index=False)
        .agg(faturamento=("total_pedido", "sum"))
        .sort_values("data_pedido_dt")
    )
    fig = px.area(vendas_dia, x="data_pedido_dt", y="faturamento", title="Faturamento Diário")
    st.plotly_chart(fig, width="stretch")

    col_a, col_b = st.columns(2)
    resumo_empresa = (
        base.groupby("EMPRESA", as_index=False)
        .agg(faturamento=("total_pedido", "sum"), pedidos=("id_pedido", "nunique"))
        .sort_values("faturamento", ascending=False)
    )
    fig_empresa = px.bar(resumo_empresa.head(20), x="EMPRESA", y="faturamento", title="Top Empresas")
    col_a.plotly_chart(fig_empresa, width="stretch")

    if "canal" in base.columns:
        resumo_canal = (
            base.groupby("canal", as_index=False)
            .agg(faturamento=("total_pedido", "sum"))
            .sort_values("faturamento", ascending=False)
        )
        fig_canal = px.pie(resumo_canal, names="canal", values="faturamento", title="Share por Canal")
        col_b.plotly_chart(fig_canal, width="stretch")

with aba_metas:
    realizado_empresa = (
        base.groupby("empresa_normalizada", as_index=False)
        .agg(realizado=("total_pedido", "sum"), pedidos=("id_pedido", "nunique"))
    )

    metas = clientes_mes.merge(realizado_empresa, on="empresa_normalizada", how="left")
    metas["realizado"] = metas["realizado"].fillna(0)
    metas["pedidos"] = metas["pedidos"].fillna(0)

    metas["percentual_realizado"] = metas.apply(
        lambda x: x["realizado"] / x["meta_mes"] if x["meta_mes"] > 0 else 0,
        axis=1
    )

    hoje = datetime.now()
    if int(ano_filtro) == hoje.year and int(mes_filtro) == hoje.month:
        dia_atual = hoje.day
        dias_mes = pd.Period(f"{int(ano_filtro)}-{int(mes_filtro):02d}").days_in_month
        fator = dias_mes / dia_atual if dia_atual else 1
    else:
        fator = 1

    metas["projecao"] = metas["realizado"] * fator
    metas["percentual_projetado"] = metas.apply(
        lambda x: x["projecao"] / x["meta_mes"] if x["meta_mes"] > 0 else 0,
        axis=1
    )
    metas["gap"] = metas["projecao"] - metas["meta_mes"]
    metas["status_meta"] = metas["percentual_projetado"].apply(status_meta)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 Risco", numero(metas["status_meta"].str.contains("RISCO").sum()))
    c2.metric("🟡 Atenção", numero(metas["status_meta"].str.contains("ATEN").sum()))
    c3.metric("🟢 Saudável", numero(metas["status_meta"].str.contains("SAUD").sum()))
    c4.metric("Meta Total", moeda(metas["meta_mes"].sum()))

    fig = px.bar(
        metas.sort_values("percentual_projetado"),
        x="EMPRESA",
        y="percentual_projetado",
        color="status_meta",
        title="Projeção de Atingimento de Meta",
        text_auto=".0%"
    )
    st.plotly_chart(fig, width="stretch")

    metas_view = metas[[
        "ASSESSOR", "STATUS", "EMPRESA", "meta_mes", "realizado",
        "percentual_realizado", "projecao", "percentual_projetado",
        "gap", "pedidos", "status_meta"
    ]].copy()

    for col in ["meta_mes", "realizado", "projecao", "gap"]:
        metas_view[col] = metas_view[col].apply(moeda)
    for col in ["percentual_realizado", "percentual_projetado"]:
        metas_view[col] = metas_view[col].apply(percentual)

    st.dataframe(metas_view, width="stretch")

with aba_temporal:
    temporal = (
        base_completa.groupby(["ano", "mes"], as_index=False)
        .agg(faturamento=("total_pedido", "sum"))
        .sort_values(["ano", "mes"])
    )
    temporal["mes_ano"] = temporal["mes"].astype(int).astype(str).str.zfill(2) + "/" + temporal["ano"].astype(int).astype(str)
    temporal["crescimento"] = temporal["faturamento"].pct_change().fillna(0)

    fig = px.line(temporal, x="mes_ano", y="faturamento", markers=True, title="Evolução Mensal")
    st.plotly_chart(fig, width="stretch")

    temporal_view = temporal.copy()
    temporal_view["faturamento"] = temporal_view["faturamento"].apply(moeda)
    temporal_view["crescimento"] = temporal_view["crescimento"].apply(percentual)
    st.dataframe(temporal_view, width="stretch")

with aba_assessores:
    ranking = (
        base.groupby("ASSESSOR", as_index=False)
        .agg(faturamento=("total_pedido", "sum"), empresas=("EMPRESA", "nunique"), pedidos=("id_pedido", "nunique"))
        .sort_values("faturamento", ascending=False)
    )
    fig = px.bar(ranking, x="ASSESSOR", y="faturamento", title="Faturamento por Assessor")
    st.plotly_chart(fig, width="stretch")

    ranking_view = ranking.copy()
    ranking_view["faturamento"] = ranking_view["faturamento"].apply(moeda)
    st.dataframe(ranking_view, width="stretch")

with aba_clientes:
    clientes_view = (
        base.groupby(["ASSESSOR", "STATUS", "EMPRESA", "contrato", "comissao"], as_index=False)
        .agg(faturamento=("total_pedido", "sum"), pedidos=("id_pedido", "nunique"))
        .sort_values("faturamento", ascending=False)
    )
    for col in ["faturamento", "contrato", "comissao"]:
        clientes_view[col] = clientes_view[col].apply(moeda)
    st.dataframe(clientes_view, width="stretch")

with aba_dados:
    st.subheader("Arquivos carregados")
    st.code(f"Clientes: {CLIENTES_PATH}")
    st.code(f"Pedidos histórico: {PEDIDOS_PATH}")
    st.code(f"Itens histórico: {ITENS_PATH}")

    st.subheader("Base filtrada")
    st.dataframe(base.head(1000), width="stretch")