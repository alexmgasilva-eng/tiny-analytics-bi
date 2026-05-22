from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# MIOS V19.7.5 - CENTRAL DE AÇÕES CONSULTIVAS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

ACTIONS_PATH = DATA_DIR / "action_tracking_v19_7_3.csv"
GOALS_PATH = DATA_DIR / "goal_evolution_v19_7_3.csv"
INSIGHTS_PATH = DATA_DIR / "ai_insights_v19_7_3.csv"


st.set_page_config(
    page_title="MIOS | Central de Ações",
    page_icon="✅",
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


actions = carregar_csv(ACTIONS_PATH)
goals = carregar_csv(GOALS_PATH)
insights = carregar_csv(INSIGHTS_PATH)


st.title("✅ Central de Ações Consultivas")
st.caption("Gestão operacional dos planos de ação da carteira consultiva.")

if actions.empty:
    st.error("Arquivo action_tracking_v19_7_3.csv não encontrado ou vazio.")
    st.stop()


# =====================================================
# NORMALIZAÇÃO DEFENSIVA
# =====================================================

actions = garantir_coluna(actions, "id_acao", "")
actions = garantir_coluna(actions, "cliente", "LEKE MEIAS")
actions = garantir_coluna(actions, "assessor", "JOYCE")
actions = garantir_coluna(actions, "diretoria", "Rosieli")
actions = garantir_coluna(actions, "periodo", "Não informado")
actions = garantir_coluna(actions, "objetivo", "Não informado")
actions = garantir_coluna(actions, "categoria", "Não informado")
actions = garantir_coluna(actions, "prioridade", "Média")
actions = garantir_coluna(actions, "acao", "Não informado")
actions = garantir_coluna(actions, "prazo", "Não informado")
actions = garantir_coluna(actions, "status_execucao", "PENDENTE")
actions = garantir_coluna(actions, "percentual_conclusao", "0")
actions = garantir_coluna(actions, "impacto_esperado", "Não informado")
actions = garantir_coluna(actions, "observacoes", "")
actions = garantir_coluna(actions, "ultima_atualizacao", "")

actions["percentual_conclusao_num"] = pd.to_numeric(
    actions["percentual_conclusao"],
    errors="coerce"
).fillna(0)

goals = garantir_coluna(goals, "cliente", "LEKE MEIAS")
goals = garantir_coluna(goals, "assessor", "JOYCE")
goals = garantir_coluna(goals, "mes", "Não informado")
goals = garantir_coluna(goals, "meta_planejada", "0")

insights = garantir_coluna(insights, "cliente", "LEKE MEIAS")
insights = garantir_coluna(insights, "assessor", "JOYCE")
insights = garantir_coluna(insights, "tipo_insight", "Insight")
insights = garantir_coluna(insights, "insight", "Não informado")
insights = garantir_coluna(insights, "acao_recomendada", "Não informado")


# =====================================================
# FILTROS
# =====================================================

st.sidebar.title("Filtros")

assessores = sorted(actions["assessor"].dropna().astype(str).unique())
clientes = sorted(actions["cliente"].dropna().astype(str).unique())
prioridades = sorted(actions["prioridade"].dropna().astype(str).unique())
status_opcoes = sorted(actions["status_execucao"].dropna().astype(str).unique())
categorias = sorted(actions["categoria"].dropna().astype(str).unique())
periodos = sorted(actions["periodo"].dropna().astype(str).unique())

assessor_filtro = st.sidebar.multiselect("Assessor", assessores, default=assessores)
cliente_filtro = st.sidebar.multiselect("Cliente", clientes, default=clientes)
prioridade_filtro = st.sidebar.multiselect("Prioridade", prioridades, default=prioridades)
status_filtro = st.sidebar.multiselect("Status", status_opcoes, default=status_opcoes)
categoria_filtro = st.sidebar.multiselect("Categoria", categorias, default=categorias)
periodo_filtro = st.sidebar.multiselect("Período", periodos, default=periodos)

base = actions[
    actions["assessor"].isin(assessor_filtro)
    & actions["cliente"].isin(cliente_filtro)
    & actions["prioridade"].isin(prioridade_filtro)
    & actions["status_execucao"].isin(status_filtro)
    & actions["categoria"].isin(categoria_filtro)
    & actions["periodo"].isin(periodo_filtro)
].copy()

if base.empty:
    st.warning("Nenhuma ação encontrada para os filtros selecionados.")
    st.stop()


# =====================================================
# KPIS
# =====================================================

total_acoes = len(base)

pendentes = base["status_execucao"].str.contains("PENDENTE", case=False, na=False).sum()
concluidas = base["status_execucao"].str.contains("CONCLU", case=False, na=False).sum()
alta_prioridade = base["prioridade"].str.contains("ALTA", case=False, na=False).sum()
clientes_ativos = base["cliente"].nunique()
conclusao_media = base["percentual_conclusao_num"].mean() / 100 if total_acoes else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Ações", numero(total_acoes))
c2.metric("Pendentes", numero(pendentes))
c3.metric("Concluídas", numero(concluidas))
c4.metric("Alta prioridade", numero(alta_prioridade))
c5.metric("Clientes", numero(clientes_ativos))
c6.metric("Conclusão média", percentual(conclusao_media))

st.divider()


# =====================================================
# KANBAN RESUMIDO
# =====================================================

st.subheader("📌 Kanban resumido por status")

kanban = (
    base.groupby(["status_execucao", "prioridade"], as_index=False)
    .agg(acoes=("id_acao", "count"))
    .sort_values("acoes", ascending=False)
)

fig_kanban = px.bar(
    kanban,
    x="status_execucao",
    y="acoes",
    color="prioridade",
    title="Ações por status e prioridade",
    text_auto=True
)

st.plotly_chart(fig_kanban, width="stretch")


# =====================================================
# PRIORIDADES
# =====================================================

st.subheader("🔥 Ações críticas e alta prioridade")

criticas = base[
    base["prioridade"].str.contains("ALTA", case=False, na=False)
].copy()

if criticas.empty:
    st.success("Nenhuma ação de alta prioridade nos filtros atuais.")
else:
    st.dataframe(
        criticas[[
            "id_acao",
            "cliente",
            "assessor",
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
# TABELA OPERACIONAL
# =====================================================

st.subheader("📋 Tabela operacional de ações")

colunas = [
    "id_acao",
    "cliente",
    "assessor",
    "diretoria",
    "periodo",
    "objetivo",
    "categoria",
    "prioridade",
    "acao",
    "prazo",
    "status_execucao",
    "percentual_conclusao",
    "impacto_esperado",
    "observacoes",
    "ultima_atualizacao",
]

colunas = [c for c in colunas if c in base.columns]

st.dataframe(
    base[colunas].sort_values(["prioridade", "cliente", "periodo"]),
    width="stretch"
)


# =====================================================
# RELAÇÃO COM METAS
# =====================================================

st.subheader("🎯 Relação com metas consultivas")

goals_filtrado = goals[
    goals["cliente"].isin(cliente_filtro)
    & goals["assessor"].isin(assessor_filtro)
].copy()

if goals_filtrado.empty:
    st.info("Nenhuma meta consultiva relacionada encontrada.")
else:
    goals_filtrado["meta_planejada_num"] = pd.to_numeric(
        goals_filtrado["meta_planejada"],
        errors="coerce"
    ).fillna(0)

    fig_goal = px.line(
        goals_filtrado,
        x="mes",
        y="meta_planejada_num",
        color="cliente",
        markers=True,
        title="Rampa de metas dos clientes filtrados"
    )

    st.plotly_chart(fig_goal, width="stretch")


# =====================================================
# INSIGHTS RELACIONADOS
# =====================================================

st.subheader("🤖 Insights relacionados")

insights_filtrado = insights[
    insights["cliente"].isin(cliente_filtro)
    & insights["assessor"].isin(assessor_filtro)
].copy()

if insights_filtrado.empty:
    st.info("Nenhum insight relacionado encontrado.")
else:
    st.dataframe(
        insights_filtrado[[
            "cliente",
            "assessor",
            "tipo_insight",
            "insight",
            "acao_recomendada",
        ]],
        width="stretch"
    )


# =====================================================
# AUDITORIA
# =====================================================

with st.expander("🔧 Auditoria técnica"):
    st.write("Arquivo actions:", str(ACTIONS_PATH))
    st.write("Colunas:", actions.columns.tolist())
    st.write("Linhas totais:", len(actions))
