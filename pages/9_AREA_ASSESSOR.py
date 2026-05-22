from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# MIOS V19.7.6 - ÁREA DO ASSESSOR
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

ACTIONS_PATH = DATA_DIR / "action_tracking_v19_7_3.csv"
GOALS_PATH = DATA_DIR / "goal_evolution_v19_7_3.csv"
INSIGHTS_PATH = DATA_DIR / "ai_insights_v19_7_3.csv"
TIMELINE_PATH = DATA_DIR / "cliente_timeline_v19_7_3.csv"
EVENTS_PATH = DATA_DIR / "consultive_events_v19_7_3.csv"


st.set_page_config(
    page_title="MIOS | Área do Assessor",
    page_icon="🧑‍💼",
    layout="wide"
)


@st.cache_data
def carregar_csv(path):
    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path, sep=";", low_memory=False)
    except Exception:
        return pd.read_csv(path, low_memory=False)


def garantir_coluna(df, coluna, valor_padrao):
    if df.empty:
        df[coluna] = []
        return df

    if coluna not in df.columns:
        df[coluna] = valor_padrao

    df[coluna] = df[coluna].fillna(valor_padrao).astype(str).str.strip()
    return df


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


def moeda(valor):
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


actions = carregar_csv(ACTIONS_PATH)
goals = carregar_csv(GOALS_PATH)
insights = carregar_csv(INSIGHTS_PATH)
timeline = carregar_csv(TIMELINE_PATH)
events = carregar_csv(EVENTS_PATH)

st.title("🧑‍💼 Área do Assessor")
st.caption("Visão individual da carteira consultiva.")

if actions.empty:
    st.error("Arquivo action_tracking_v19_7_3.csv não encontrado ou vazio.")
    st.stop()


# =====================================================
# NORMALIZAÇÃO
# =====================================================

actions = garantir_coluna(actions, "cliente", "LEKE MEIAS")
actions = garantir_coluna(actions, "assessor", "JOYCE")
actions = garantir_coluna(actions, "categoria", "Não informado")
actions = garantir_coluna(actions, "prioridade", "Média")
actions = garantir_coluna(actions, "acao", "Não informado")
actions = garantir_coluna(actions, "prazo", "Não informado")
actions = garantir_coluna(actions, "periodo", "Não informado")
actions = garantir_coluna(actions, "objetivo", "Não informado")
actions = garantir_coluna(actions, "status_execucao", "PENDENTE")
actions = garantir_coluna(actions, "percentual_conclusao", "0")
actions = garantir_coluna(actions, "impacto_esperado", "Não informado")

actions["percentual_conclusao_num"] = pd.to_numeric(
    actions["percentual_conclusao"],
    errors="coerce"
).fillna(0)

goals = garantir_coluna(goals, "cliente", "LEKE MEIAS")
goals = garantir_coluna(goals, "assessor", "JOYCE")
goals = garantir_coluna(goals, "mes", "Não informado")
goals = garantir_coluna(goals, "meta_planejada", "0")

goals["meta_planejada_num"] = pd.to_numeric(
    goals["meta_planejada"],
    errors="coerce"
).fillna(0)

insights = garantir_coluna(insights, "cliente", "LEKE MEIAS")
insights = garantir_coluna(insights, "assessor", "JOYCE")
insights = garantir_coluna(insights, "tipo_insight", "Insight")
insights = garantir_coluna(insights, "insight", "Não informado")
insights = garantir_coluna(insights, "acao_recomendada", "Não informado")

timeline = garantir_coluna(timeline, "cliente", "LEKE MEIAS")
timeline = garantir_coluna(timeline, "assessor", "JOYCE")
timeline = garantir_coluna(timeline, "tipo_evento", "CONSULTIVO")
timeline = garantir_coluna(timeline, "titulo", "Evento")
timeline = garantir_coluna(timeline, "descricao", "")
timeline = garantir_coluna(timeline, "data_evento", "")
timeline = garantir_coluna(timeline, "criticidade", "INFORMATIVO")

events = garantir_coluna(events, "cliente", "LEKE MEIAS")
events = garantir_coluna(events, "assessor", "JOYCE")
events = garantir_coluna(events, "evento", "Evento")
events = garantir_coluna(events, "tipo", "CONSULTIVO")
events = garantir_coluna(events, "criticidade", "INFORMATIVO")
events = garantir_coluna(events, "acao_sugerida", "Não informado")


# =====================================================
# SELETOR ASSESSOR
# =====================================================

assessores = sorted(actions["assessor"].dropna().astype(str).unique())

assessor = st.sidebar.selectbox(
    "Assessor",
    assessores,
    index=0
)

base = actions[actions["assessor"] == assessor].copy()
goals_base = goals[goals["assessor"] == assessor].copy()
insights_base = insights[insights["assessor"] == assessor].copy()
timeline_base = timeline[timeline["assessor"] == assessor].copy()
events_base = events[events["assessor"] == assessor].copy()

clientes = sorted(base["cliente"].dropna().astype(str).unique())

cliente_filtro = st.sidebar.multiselect(
    "Clientes",
    clientes,
    default=clientes
)

prioridades = sorted(base["prioridade"].dropna().astype(str).unique())

prioridade_filtro = st.sidebar.multiselect(
    "Prioridade",
    prioridades,
    default=prioridades
)

status_opcoes = sorted(base["status_execucao"].dropna().astype(str).unique())

status_filtro = st.sidebar.multiselect(
    "Status",
    status_opcoes,
    default=status_opcoes
)

base = base[
    base["cliente"].isin(cliente_filtro)
    & base["prioridade"].isin(prioridade_filtro)
    & base["status_execucao"].isin(status_filtro)
].copy()

goals_base = goals_base[goals_base["cliente"].isin(cliente_filtro)].copy()
insights_base = insights_base[insights_base["cliente"].isin(cliente_filtro)].copy()
timeline_base = timeline_base[timeline_base["cliente"].isin(cliente_filtro)].copy()
events_base = events_base[events_base["cliente"].isin(cliente_filtro)].copy()

if base.empty:
    st.warning("Nenhuma ação encontrada para os filtros selecionados.")
    st.stop()


# =====================================================
# KPIS
# =====================================================

clientes_carteira = base["cliente"].nunique()
acoes_total = len(base)
acoes_pendentes = base["status_execucao"].str.contains("PENDENTE", case=False, na=False).sum()
acoes_alta = base["prioridade"].str.contains("ALTA", case=False, na=False).sum()
conclusao_media = base["percentual_conclusao_num"].mean() / 100 if len(base) else 0
insights_total = len(insights_base)
eventos_criticos = events_base["criticidade"].str.contains("ALTA", case=False, na=False).sum() if not events_base.empty else 0

st.subheader(f"Carteira consultiva de {assessor}")

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Clientes", numero(clientes_carteira))
c2.metric("Ações", numero(acoes_total))
c3.metric("Pendentes", numero(acoes_pendentes))
c4.metric("Alta prioridade", numero(acoes_alta))
c5.metric("Conclusão média", percentual(conclusao_media))
c6.metric("Eventos críticos", numero(eventos_criticos))

st.divider()


# =====================================================
# PRIORIDADES DA SEMANA
# =====================================================

st.subheader("🔥 Prioridades da carteira")

prioridades_df = base[
    base["prioridade"].str.contains("ALTA", case=False, na=False)
].copy()

if prioridades_df.empty:
    st.success("Nenhuma ação alta prioridade nos filtros atuais.")
else:
    st.dataframe(
        prioridades_df[[
            "cliente",
            "periodo",
            "categoria",
            "acao",
            "prazo",
            "status_execucao",
            "impacto_esperado",
        ]],
        width="stretch"
    )


# =====================================================
# CLIENTES COM PENDÊNCIAS
# =====================================================

st.subheader("🏢 Clientes com ações pendentes")

pendencias = (
    base[base["status_execucao"].str.contains("PENDENTE", case=False, na=False)]
    .groupby("cliente", as_index=False)
    .agg(
        acoes_pendentes=("acao", "count"),
        alta_prioridade=("prioridade", lambda x: x.astype(str).str.contains("ALTA", case=False, na=False).sum()),
        conclusao_media=("percentual_conclusao_num", "mean")
    )
    .sort_values(["alta_prioridade", "acoes_pendentes"], ascending=False)
)

fig_pend = px.bar(
    pendencias,
    x="cliente",
    y="acoes_pendentes",
    color="alta_prioridade",
    title="Pendências por cliente"
)

st.plotly_chart(fig_pend, width="stretch")

st.dataframe(pendencias, width="stretch")


# =====================================================
# PLANO DE AÇÃO
# =====================================================

st.subheader("📋 Plano de ação do assessor")

st.dataframe(
    base[[
        "cliente",
        "periodo",
        "objetivo",
        "categoria",
        "prioridade",
        "acao",
        "prazo",
        "status_execucao",
        "percentual_conclusao",
        "impacto_esperado",
    ]].sort_values(["cliente", "prioridade", "periodo"]),
    width="stretch"
)


# =====================================================
# METAS DA CARTEIRA
# =====================================================

st.subheader("🎯 Metas da carteira")

if goals_base.empty:
    st.info("Nenhuma meta encontrada para a carteira.")
else:
    ordem_meses = [
        "Janeiro", "Fevereiro", "Março", "Abril",
        "Maio", "Junho", "Julho", "Agosto",
        "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    goals_base["mes_ordem"] = goals_base["mes"].apply(
        lambda x: ordem_meses.index(x) + 1 if x in ordem_meses else 99
    )

    goals_plot = goals_base.sort_values(["cliente", "mes_ordem"])

    fig_goals = px.line(
        goals_plot,
        x="mes",
        y="meta_planejada_num",
        color="cliente",
        markers=True,
        title="Rampa de metas por cliente"
    )

    st.plotly_chart(fig_goals, width="stretch")

    goals_view = goals_plot.copy()
    goals_view["meta_planejada_num"] = goals_view["meta_planejada_num"].apply(moeda)

    st.dataframe(
        goals_view.drop(columns=["mes_ordem"], errors="ignore"),
        width="stretch"
    )


# =====================================================
# INSIGHTS
# =====================================================

st.subheader("🤖 Insights da carteira")

if insights_base.empty:
    st.info("Nenhum insight encontrado para a carteira.")
else:
    for _, row in insights_base.iterrows():
        st.markdown(
            f"""
### {row.get('tipo_insight', '')} — {row.get('cliente', '')}

**Insight:** {row.get('insight', '')}

**Ação recomendada:** {row.get('acao_recomendada', '')}

---
"""
        )


# =====================================================
# TIMELINE
# =====================================================

st.subheader("🕒 Timeline consultiva da carteira")

if timeline_base.empty:
    st.info("Nenhum evento na timeline.")
else:
    st.dataframe(
        timeline_base.sort_values("data_evento", ascending=False),
        width="stretch"
    )


# =====================================================
# EVENTOS
# =====================================================

st.subheader("🚨 Eventos críticos")

if events_base.empty:
    st.info("Nenhum evento encontrado.")
else:
    st.dataframe(events_base, width="stretch")


with st.expander("🔧 Auditoria técnica"):
    st.write("Arquivo actions:", str(ACTIONS_PATH))
    st.write("Assessor selecionado:", assessor)
    st.write("Colunas:", actions.columns.tolist())
    st.write("Linhas totais:", len(actions))
