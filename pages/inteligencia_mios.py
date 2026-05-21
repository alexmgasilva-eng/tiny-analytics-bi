from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

st.set_page_config(
    page_title="Inteligência MIOS",
    page_icon="🧠",
    layout="wide"
)

def moeda(valor):
    return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def percentual(valor):
    return f"{float(valor) * 100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data
def carregar():
    return pd.read_csv(DATA_DIR / "inteligencia_clientes_v18.csv")

df = carregar()

st.title("🧠 Inteligência MIOS")
st.caption("Prioridade consultiva, risco da carteira e recomendações automáticas")

assessores = sorted(df["ASSESSOR"].dropna().unique())
status = sorted(df["status_saude"].dropna().unique())

assessor_filtro = st.sidebar.multiselect("Assessor", assessores, default=assessores)
status_filtro = st.sidebar.multiselect("Status saúde", status, default=status)

base = df[
    df["ASSESSOR"].isin(assessor_filtro)
    & df["status_saude"].isin(status_filtro)
].copy()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Clientes analisados", len(base))
c2.metric("Críticos", len(base[base["status_saude"].astype(str).str.contains("CRÍTICO")]))
c3.metric("Saudáveis", len(base[base["status_saude"].astype(str).str.contains("SAUDÁVEL")]))
c4.metric("Onboarding", len(base[base["status_saude"].astype(str).str.contains("ONBOARDING")]))

st.divider()

fig = px.bar(
    base.sort_values("score_prioridade", ascending=False).head(20),
    x="score_prioridade",
    y="EMPRESA",
    color="status_saude",
    orientation="h",
    title="Ranking de prioridade consultiva"
)

fig.update_layout(yaxis={"categoryorder": "total ascending"})
st.plotly_chart(fig, width="stretch")

st.subheader("Plano de ação recomendado")

tabela = base.sort_values("score_prioridade", ascending=False)[[
    "ASSESSOR",
    "STATUS",
    "EMPRESA",
    "status_saude",
    "score_prioridade",
    "meta_mes",
    "realizado_mes",
    "percentual_meta",
    "projecao_mes",
    "percentual_projetado",
    "gap_projetado",
    "ritmo_diario_necessario",
    "crescimento_vs_mes_anterior",
    "dias_sem_venda",
    "recomendacao"
]].copy()

for col in ["meta_mes", "realizado_mes", "projecao_mes", "gap_projetado", "ritmo_diario_necessario"]:
    tabela[col] = tabela[col].apply(moeda)

for col in ["percentual_meta", "percentual_projetado", "crescimento_vs_mes_anterior"]:
    tabela[col] = tabela[col].apply(percentual)

st.dataframe(tabela, width="stretch")

st.subheader("Resumo por assessor")

resumo = (
    base
    .groupby("ASSESSOR", as_index=False)
    .agg(
        clientes=("EMPRESA", "count"),
        criticos=("status_saude", lambda x: x.astype(str).str.contains("CRÍTICO").sum()),
        saudaveis=("status_saude", lambda x: x.astype(str).str.contains("SAUDÁVEL").sum()),
        meta=("meta_mes", "sum"),
        realizado=("realizado_mes", "sum"),
        projecao=("projecao_mes", "sum"),
        score_medio=("score_prioridade", "mean")
    )
)

resumo["percentual_meta"] = resumo["realizado"] / resumo["meta"]

for col in ["meta", "realizado", "projecao"]:
    resumo[col] = resumo[col].apply(moeda)

resumo["percentual_meta"] = resumo["percentual_meta"].apply(percentual)

st.dataframe(resumo, width="stretch")