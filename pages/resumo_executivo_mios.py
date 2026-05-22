from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

st.set_page_config(
    page_title="Resumo Executivo MIOS",
    page_icon="📌",
    layout="wide"
)

def moeda(v):
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def percentual(v):
    return f"{float(v) * 100:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data
def carregar():
    return pd.read_csv(DATA_DIR / "inteligencia_clientes_v18.csv")

df = carregar()

st.title("📌 Resumo Executivo MIOS")
st.caption("Visão rápida para tomada de decisão da consultoria digital")

assessores = sorted(df["ASSESSOR"].dropna().unique())
assessor_filtro = st.sidebar.multiselect("Assessor", assessores, default=assessores)

base = df[df["ASSESSOR"].isin(assessor_filtro)].copy()

criticos = base[base["status_saude"].astype(str).str.contains("CRÍTICO")]
saudaveis = base[base["status_saude"].astype(str).str.contains("SAUDÁVEL")]
onboarding = base[base["status_saude"].astype(str).str.contains("ONBOARDING")]

meta = base["meta_mes"].sum()
realizado = base["realizado_mes"].sum()
projecao = base["projecao_mes"].sum()
gap = projecao - meta
perc_meta = realizado / meta if meta else 0
perc_proj = projecao / meta if meta else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Meta digital", moeda(meta))
c2.metric("Realizado digital", moeda(realizado))
c3.metric("% Realizado", percentual(perc_meta))
c4.metric("Projeção", moeda(projecao))
c5.metric("Gap Projetado", moeda(gap))

st.divider()

st.subheader("Diagnóstico da carteira digital")

st.write(f"""
A carteira filtrada possui **{len(base)} clientes analisados**.

- 🔴 **{len(criticos)} clientes críticos**
- 🟢 **{len(saudaveis)} clientes saudáveis**
- ⚪ **{len(onboarding)} clientes em onboarding**
- Projeção atual: **{percentual(perc_proj)} da meta digital**
""")

if gap < 0:
    st.error(f"A carteira digital está projetando fechar abaixo da meta em {moeda(abs(gap))}.")
else:
    st.success(f"A carteira digital está projetando superar a meta em {moeda(gap)}.")

st.subheader("Top prioridades")

prioridades = base.sort_values("score_prioridade", ascending=False).head(10)

for _, row in prioridades.iterrows():
    canal = row.get("canal_principal", "Sem canal")
    st.warning(
        f"{row['EMPRESA']} | {row['ASSESSOR']} | "
        f"{row['status_saude']} | Canal principal: {canal} | "
        f"Score {row['score_prioridade']} | "
        f"{row['recomendacao']}"
    )

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

resumo["% realizado"] = resumo["realizado"] / resumo["meta"]

for col in ["meta", "realizado", "projecao"]:
    resumo[col] = resumo[col].apply(moeda)

resumo["% realizado"] = resumo["% realizado"].apply(percentual)

st.dataframe(resumo, width="stretch")

st.caption("Dados sensíveis protegidos. CNPJ e chave API não são exibidos nesta página.")