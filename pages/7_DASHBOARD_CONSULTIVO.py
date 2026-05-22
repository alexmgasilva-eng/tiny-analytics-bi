from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# MIOS V19.7.4 - DASHBOARD CONSULTIVO
# SCRIPT COMPLETO CORRIGIDO
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

ACTIONS_PATH = DATA_DIR / "action_tracking_v19_7_3.csv"
GOALS_PATH = DATA_DIR / "goal_evolution_v19_7_3.csv"
INSIGHTS_PATH = DATA_DIR / "ai_insights_v19_7_3.csv"
TIMELINE_PATH = DATA_DIR / "cliente_timeline_v19_7_3.csv"
EVENTS_PATH = DATA_DIR / "consultive_events_v19_7_3.csv"


st.set_page_config(
    page_title="MIOS | Dashboard Consultivo",
    page_icon="🧠",
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


actions = carregar_csv(ACTIONS_PATH)
goals = carregar_csv(GOALS_PATH)
insights = carregar_csv(INSIGHTS_PATH)
timeline = carregar_csv(TIMELINE_PATH)
events = carregar_csv(EVENTS_PATH)

st.title("🧠 Dashboard Consultivo MIOS")
st.caption("Central consultiva viva da operação.")

if actions.empty:
    st.error("Arquivo action_tracking_v19_7_3.csv não encontrado ou vazio.")
    st.stop()


# =====================================================
# NORMALIZAÇÃO DEFENSIVA
# =====================================================

actions = garantir_coluna(actions, "cliente", "LEKE MEIAS")
actions = garantir_coluna(actions, "assessor", "JOYCE")
actions = garantir_coluna(actions, "categoria", "Não informado")
actions = garantir_coluna(actions, "prioridade", "Média")
actions = garantir_coluna(actions, "acao", "Não informado")
actions = garantir_coluna(actions, "prazo", "Não informado")
actions = garantir_coluna(actions, "status_execucao", "PENDENTE")
actions = garantir_coluna(actions, "percentual_conclusao", "0")
actions = garantir_coluna(actions, "periodo", "Não informado")
actions = garantir_coluna(actions, "objetivo", "Não informado")

goals = garantir_coluna(goals, "cliente", "LEKE MEIAS")
goals = garantir_coluna(goals, "assessor", "JOYCE")
goals = garantir_coluna(goals, "mes", "Não informado")
goals = garantir_coluna(goals, "ano", "2026")
goals = garantir_coluna(goals, "meta_planejada", "0")
goals = garantir_coluna(goals, "tipo_meta", "FATURAMENTO_MENSAL")
goals = garantir_coluna(goals, "status_meta", "Planejada")

insights = garantir_coluna(insights, "cliente", "LEKE MEIAS")
insights = garantir_coluna(insights, "assessor", "JOYCE")
insights = garantir_coluna(insights, "tipo_insight", "Insight")
insights = garantir_coluna(insights, "insight", "Não informado")
insights = garantir_coluna(insights, "acao_recomendada", "Não informado")
insights = garantir_coluna(insights, "origem", "MIOS")

timeline = garantir_coluna(timeline, "cliente", "LEKE MEIAS")
timeline = garantir_coluna(timeline, "assessor", "JOYCE")
timeline = garantir_coluna(timeline, "tipo_evento", "CONSULTIVO")
timeline = garantir_coluna(timeline, "titulo", "Evento consultivo")
timeline = garantir_coluna(timeline, "descricao", "")
timeline = garantir_coluna(timeline, "data_evento", "")
timeline = garantir_coluna(timeline, "origem", "MIOS")
timeline = garantir_coluna(timeline, "criticidade", "INFORMATIVO")

events = garantir_coluna(events, "cliente", "LEKE MEIAS")
events = garantir_coluna(events, "assessor", "JOYCE")
events = garantir_coluna(events, "evento", "Evento")
events = garantir_coluna(events, "tipo", "CONSULTIVO")
events = garantir_coluna(events, "criticidade", "INFORMATIVO")
events = garantir_coluna(events, "acao_sugerida", "Não informado")
events = garantir_coluna(events, "origem", "MIOS")

goals["meta_planejada"] = pd.to_numeric(goals["meta_planejada"], errors="coerce").fillna(0)
actions["percentual_conclusao"] = pd.to_numeric(actions["percentual_conclusao"], errors="coerce").fillna(0)


# =====================================================
# FILTROS
# =====================================================

st.sidebar.title("Filtros")

assessores = sorted(actions["assessor"].dropna().astype(str).unique())

assessor_filtro = st.sidebar.multiselect(
    "Assessores",
    assessores,
    default=assessores
)

clientes = sorted(actions["cliente"].dropna().astype(str).unique())

cliente_filtro = st.sidebar.multiselect(
    "Clientes",
    clientes,
    default=clientes
)

prioridades = sorted(actions["prioridade"].dropna().astype(str).unique())

prioridade_filtro = st.sidebar.multiselect(
    "Prioridade",
    prioridades,
    default=prioridades
)

status_opcoes = sorted(actions["status_execucao"].dropna().astype(str).unique())

status_filtro = st.sidebar.multiselect(
    "Status execução",
    status_opcoes,
    default=status_opcoes
)

actions_filtrado = actions[
    actions["assessor"].astype(str).isin(assessor_filtro)
    & actions["cliente"].astype(str).isin(cliente_filtro)
    & actions["prioridade"].astype(str).isin(prioridade_filtro)
    & actions["status_execucao"].astype(str).isin(status_filtro)
].copy()

goals_filtrado = goals[
    goals["cliente"].astype(str).isin(cliente_filtro)
].copy()

timeline_filtrado = timeline[
    timeline["cliente"].astype(str).isin(cliente_filtro)
].copy()

insights_filtrado = insights[
    insights["cliente"].astype(str).isin(cliente_filtro)
].copy()

events_filtrado = events[
    events["cliente"].astype(str).isin(cliente_filtro)
].copy()


# =====================================================
# KPIS
# =====================================================

acoes_total = len(actions_filtrado)

acoes_pendentes = (
    actions_filtrado["status_execucao"]
    .astype(str)
    .str.contains("PENDENTE", case=False, na=False)
    .sum()
)

acoes_concluidas = (
    actions_filtrado["status_execucao"]
    .astype(str)
    .str.contains("CONCLU", case=False, na=False)
    .sum()
)

clientes_ativos = actions_filtrado["cliente"].nunique()

insights_total = len(insights_filtrado)

eventos_total = len(events_filtrado)

score_consultivo = round(
    (
        (acoes_total * 1.2)
        + (insights_total * 2)
        + (clientes_ativos * 5)
        + (eventos_total * 1.5)
    ),
    2
)

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Ações", numero(acoes_total))
c2.metric("Pendentes", numero(acoes_pendentes))
c3.metric("Concluídas", numero(acoes_concluidas))
c4.metric("Clientes", numero(clientes_ativos))
c5.metric("Insights IA", numero(insights_total))
c6.metric("Score consultivo", score_consultivo)

st.divider()


# =====================================================
# PLANO DE AÇÃO
# =====================================================

st.subheader("📋 Plano de ação consultivo")

cols_action = [
    "cliente",
    "assessor",
    "periodo",
    "objetivo",
    "categoria",
    "prioridade",
    "acao",
    "prazo",
    "status_execucao",
    "percentual_conclusao",
]

cols_action = [c for c in cols_action if c in actions_filtrado.columns]

st.dataframe(
    actions_filtrado[cols_action].sort_values(
        ["prioridade", "prazo"],
        ascending=[True, True]
    ),
    width="stretch"
)


# =====================================================
# GOALS
# =====================================================

st.subheader("🎯 Evolução metas estratégicas")

if goals_filtrado.empty:
    st.info("Nenhuma meta consultiva encontrada.")
else:
    ordem_meses = [
        "Janeiro", "Fevereiro", "Março", "Abril",
        "Maio", "Junho", "Julho", "Agosto",
        "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    goals_filtrado["mes_ordem"] = goals_filtrado["mes"].apply(
        lambda x: ordem_meses.index(x) + 1 if x in ordem_meses else 99
    )

    goals_plot = goals_filtrado.sort_values(["cliente", "ano", "mes_ordem"])

    fig_goal = px.line(
        goals_plot,
        x="mes",
        y="meta_planejada",
        color="cliente",
        markers=True,
        title="Rampa consultiva de metas"
    )

    st.plotly_chart(fig_goal, width="stretch")

    goals_view = goals_plot.copy()
    goals_view["meta_planejada"] = goals_view["meta_planejada"].apply(moeda)

    st.dataframe(
        goals_view.drop(columns=["mes_ordem"], errors="ignore"),
        width="stretch"
    )


# =====================================================
# INSIGHTS IA
# =====================================================

st.subheader("🤖 Insights IA")

if insights_filtrado.empty:
    st.info("Nenhum insight encontrado.")
else:
    for _, row in insights_filtrado.iterrows():
        st.markdown(
            f"""
### {row.get('tipo_insight', '')}

**Cliente:** {row.get('cliente', '')}

**Insight:** {row.get('insight', '')}

**Ação recomendada:** {row.get('acao_recomendada', '')}

**Origem:** {row.get('origem', '')}

---
"""
        )


# =====================================================
# EVENTOS CRÍTICOS
# =====================================================

st.subheader("🚨 Eventos consultivos")

if events_filtrado.empty:
    st.info("Nenhum evento consultivo encontrado.")
else:
    st.dataframe(events_filtrado, width="stretch")


# =====================================================
# TIMELINE
# =====================================================

st.subheader("🕒 Timeline consultiva")

if timeline_filtrado.empty:
    st.info("Nenhuma timeline encontrada.")
else:
    st.dataframe(
        timeline_filtrado.sort_values(
            "data_evento",
            ascending=False
        ),
        width="stretch"
    )


# =====================================================
# RADAR OPERACIONAL
# =====================================================

st.subheader("📡 Radar operacional")

radar = pd.DataFrame([
    {"Indicador": "Ações pendentes", "Valor": acoes_pendentes},
    {"Indicador": "Ações concluídas", "Valor": acoes_concluidas},
    {"Indicador": "Clientes ativos", "Valor": clientes_ativos},
    {"Indicador": "Insights IA", "Valor": insights_total},
    {"Indicador": "Eventos críticos", "Valor": eventos_total},
])

fig_radar = px.bar(
    radar,
    x="Indicador",
    y="Valor",
    title="Radar consultivo operacional"
)

st.plotly_chart(fig_radar, width="stretch")


# =====================================================
# DEBUG CONTROLADO
# =====================================================

with st.expander("🔧 Auditoria técnica da página"):
    st.write("Arquivo actions:", str(ACTIONS_PATH))
    st.write("Colunas action_tracking:", actions.columns.tolist())
    st.write("Linhas action_tracking:", len(actions))
