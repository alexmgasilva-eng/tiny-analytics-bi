from pathlib import Path
import shutil
import unicodedata
import pandas as pd
import plotly.express as px
import streamlit as st


# =====================================================
# MIOS V19.7.8.4 - ÁREA DO CLIENTE
# MATCHING ROBUSTO CLIENTE + DADOS OPERACIONAIS
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RELATORIOS_DIR = DATA_DIR / "relatorios"
ROOT_DIR = BASE_DIR.parent

PDF_ORIGEM = ROOT_DIR / "data" / "consultivo" / "entrada" / "RELATORIO_EFACTOR_PROFISSIONAL.pdf"
PDF_PUBLICADO = RELATORIOS_DIR / "LEKE_MEIAS_RELATORIO_DIRETORIA.pdf"

PEDIDOS_PATH = DATA_DIR / "pedidos_historico.csv"
ACTIONS_PATH = DATA_DIR / "action_tracking_v19_7_3.csv"
GOALS_PATH = DATA_DIR / "goal_evolution_v19_7_3.csv"
INSIGHTS_PATH = DATA_DIR / "ai_insights_v19_7_3.csv"
TIMELINE_PATH = DATA_DIR / "cliente_timeline_v19_7_3.csv"
EVENTS_PATH = DATA_DIR / "consultive_events_v19_7_3.csv"


st.set_page_config(
    page_title="MIOS | Área do Cliente",
    page_icon="🏢",
    layout="wide"
)


def normalizar_nome(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = " ".join(texto.split())

    return texto


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


def preparar_relatorio_pdf():
    RELATORIOS_DIR.mkdir(parents=True, exist_ok=True)

    if PDF_ORIGEM.exists() and not PDF_PUBLICADO.exists():
        shutil.copy2(PDF_ORIGEM, PDF_PUBLICADO)

    return PDF_PUBLICADO if PDF_PUBLICADO.exists() else None


def normalizar_pedidos(df):
    if df.empty:
        return df

    df = garantir_coluna(df, "empresa", "Não identificado")
    df = garantir_coluna(df, "canal_estrategico", "Não identificado")
    df = garantir_coluna(df, "tipo_venda", "DIGITAL")

    df["empresa_norm"] = df["empresa"].apply(normalizar_nome)

    if "data_pedido" in df.columns:
        df["data_pedido_dt"] = pd.to_datetime(
            df["data_pedido"],
            format="%d/%m/%Y",
            errors="coerce"
        )
    else:
        df["data_pedido_dt"] = pd.NaT

    if "ano" in df.columns:
        df["ano"] = pd.to_numeric(df["ano"], errors="coerce")
    else:
        df["ano"] = df["data_pedido_dt"].dt.year

    if "mes" in df.columns:
        df["mes"] = pd.to_numeric(df["mes"], errors="coerce")
    else:
        df["mes"] = df["data_pedido_dt"].dt.month

    if "total_pedido" in df.columns:
        df["total_pedido"] = pd.to_numeric(df["total_pedido"], errors="coerce").fillna(0)
    else:
        df["total_pedido"] = 0

    if "id_pedido" not in df.columns:
        df["id_pedido"] = range(1, len(df) + 1)

    return df


def mes_anterior(ano, mes):
    if ano is None or mes is None:
        return None, None

    if int(mes) == 1:
        return int(ano) - 1, 12

    return int(ano), int(mes) - 1


def nome_mes(mes):
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril",
        "Maio", "Junho", "Julho", "Agosto",
        "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    try:
        mes = int(mes)
        if 1 <= mes <= 12:
            return meses[mes - 1]
    except Exception:
        pass

    return "Sem período"


def filtrar_cliente_robusto(df, coluna, cliente):
    if df.empty or coluna not in df.columns:
        return pd.DataFrame()

    alvo = normalizar_nome(cliente)

    base = df.copy()
    base["_cliente_norm_tmp"] = base[coluna].apply(normalizar_nome)

    filtro_exato = base["_cliente_norm_tmp"] == alvo

    if filtro_exato.any():
        return base[filtro_exato].drop(columns=["_cliente_norm_tmp"], errors="ignore").copy()

    # fallback por primeira palavra relevante
    palavras = [p for p in alvo.split() if len(p) >= 3]

    if palavras:
        primeira = palavras[0]
        filtro_contains = base["_cliente_norm_tmp"].str.contains(primeira, na=False)

        if filtro_contains.any():
            return base[filtro_contains].drop(columns=["_cliente_norm_tmp"], errors="ignore").copy()

    # fallback específico LEKE
    if "LEKE" in alvo:
        filtro_leke = base["_cliente_norm_tmp"].str.contains("LEKE", na=False)

        if filtro_leke.any():
            return base[filtro_leke].drop(columns=["_cliente_norm_tmp"], errors="ignore").copy()

    return pd.DataFrame()


def ultimo_periodo_com_venda(df):
    if df.empty:
        return None, None

    base = df[
        df["ano"].notna()
        & df["mes"].notna()
        & (df["total_pedido"] > 0)
    ].copy()

    if base.empty:
        return None, None

    resumo = (
        base.groupby(["ano", "mes"], as_index=False)
        .agg(faturamento=("total_pedido", "sum"))
        .sort_values(["ano", "mes"])
    )

    ultimo = resumo.iloc[-1]

    return int(ultimo["ano"]), int(ultimo["mes"])


# =====================================================
# TOPO
# =====================================================

st.title("🏢 Área do Cliente MIOS")
st.caption("Visão operacional e consultiva da sua operação.")

if st.sidebar.button("🔄 Recarregar dados"):
    st.cache_data.clear()
    st.rerun()


# =====================================================
# CARREGAMENTO
# =====================================================

pedidos = normalizar_pedidos(carregar_csv(PEDIDOS_PATH))
actions = carregar_csv(ACTIONS_PATH)
goals = carregar_csv(GOALS_PATH)
insights = carregar_csv(INSIGHTS_PATH)
timeline = carregar_csv(TIMELINE_PATH)
events = carregar_csv(EVENTS_PATH)

if actions.empty:
    st.error("Arquivo action_tracking_v19_7_3.csv não encontrado ou vazio.")
    st.stop()

if pedidos.empty:
    st.error("Arquivo pedidos_historico.csv não encontrado ou vazio.")
    st.stop()


# =====================================================
# NORMALIZAÇÃO CONSULTIVA
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

actions["cliente_norm"] = actions["cliente"].apply(normalizar_nome)
actions["percentual_conclusao_num"] = pd.to_numeric(actions["percentual_conclusao"], errors="coerce").fillna(0)

goals = garantir_coluna(goals, "cliente", "LEKE MEIAS")
goals = garantir_coluna(goals, "mes", "Não informado")
goals = garantir_coluna(goals, "ano", "2026")
goals = garantir_coluna(goals, "meta_planejada", "0")
goals["cliente_norm"] = goals["cliente"].apply(normalizar_nome)
goals["meta_planejada_num"] = pd.to_numeric(goals["meta_planejada"], errors="coerce").fillna(0)

insights = garantir_coluna(insights, "cliente", "LEKE MEIAS")
insights = garantir_coluna(insights, "tipo_insight", "Insight")
insights = garantir_coluna(insights, "insight", "Não informado")
insights = garantir_coluna(insights, "acao_recomendada", "Não informado")
insights["cliente_norm"] = insights["cliente"].apply(normalizar_nome)

timeline = garantir_coluna(timeline, "cliente", "LEKE MEIAS")
timeline = garantir_coluna(timeline, "tipo_evento", "CONSULTIVO")
timeline = garantir_coluna(timeline, "titulo", "Evento")
timeline = garantir_coluna(timeline, "descricao", "")
timeline = garantir_coluna(timeline, "data_evento", "")
timeline = garantir_coluna(timeline, "criticidade", "INFORMATIVO")
timeline["cliente_norm"] = timeline["cliente"].apply(normalizar_nome)

events = garantir_coluna(events, "cliente", "LEKE MEIAS")
events = garantir_coluna(events, "evento", "Evento")
events = garantir_coluna(events, "criticidade", "INFORMATIVO")
events = garantir_coluna(events, "acao_sugerida", "Não informado")
events["cliente_norm"] = events["cliente"].apply(normalizar_nome)


# =====================================================
# FILTROS
# =====================================================

clientes_actions = set(actions["cliente"].dropna().astype(str).unique())
clientes_pedidos = set(pedidos["empresa"].dropna().astype(str).unique())

# prioriza clientes consultivos no topo, mas mantém todos
clientes = sorted(clientes_actions.union(clientes_pedidos))

cliente_default = clientes.index("LEKE MEIAS") if "LEKE MEIAS" in clientes else 0

cliente = st.sidebar.selectbox(
    "Cliente",
    clientes,
    index=cliente_default
)

cliente_norm = normalizar_nome(cliente)

pedidos_cliente = filtrar_cliente_robusto(pedidos, "empresa", cliente)

ano_auto, mes_auto = ultimo_periodo_com_venda(pedidos_cliente)

ano_filtro = None
mes_filtro = None

if pedidos_cliente.empty:
    st.warning("Não há pedidos encontrados para este cliente no histórico.")
else:
    anos = sorted(pedidos_cliente["ano"].dropna().astype(int).unique())

    ano_index = anos.index(ano_auto) if ano_auto in anos else len(anos) - 1

    ano_filtro = st.sidebar.selectbox(
        "Ano",
        anos,
        index=ano_index
    )

    meses = sorted(
        pedidos_cliente[pedidos_cliente["ano"] == ano_filtro]["mes"]
        .dropna()
        .astype(int)
        .unique()
    )

    mes_index = meses.index(mes_auto) if ano_filtro == ano_auto and mes_auto in meses else len(meses) - 1

    mes_filtro = st.sidebar.selectbox(
        "Mês",
        meses,
        index=mes_index
    )


# =====================================================
# BASES FILTRADAS
# =====================================================

if ano_filtro is not None and mes_filtro is not None:
    base_mes = pedidos_cliente[
        (pedidos_cliente["ano"] == ano_filtro)
        & (pedidos_cliente["mes"] == mes_filtro)
    ].copy()

    ano_ant, mes_ant = mes_anterior(ano_filtro, mes_filtro)

    base_mes_ant = pedidos_cliente[
        (pedidos_cliente["ano"] == ano_ant)
        & (pedidos_cliente["mes"] == mes_ant)
    ].copy()
else:
    base_mes = pd.DataFrame()
    base_mes_ant = pd.DataFrame()
    ano_ant = None
    mes_ant = None

actions_base = filtrar_cliente_robusto(actions, "cliente", cliente)
goals_base = filtrar_cliente_robusto(goals, "cliente", cliente)
insights_base = filtrar_cliente_robusto(insights, "cliente", cliente)
timeline_base = filtrar_cliente_robusto(timeline, "cliente", cliente)
events_base = filtrar_cliente_robusto(events, "cliente", cliente)


# =====================================================
# AUDITORIA VISÍVEL
# =====================================================

with st.expander("🔎 Auditoria rápida de dados", expanded=True):
    st.write("Cliente selecionado:", cliente)
    st.write("Cliente normalizado:", cliente_norm)
    st.write("Linhas pedidos cliente:", len(pedidos_cliente))
    st.write("Ano automático:", ano_auto)
    st.write("Mês automático:", mes_auto)
    st.write("Ano filtro:", ano_filtro)
    st.write("Mês filtro:", mes_filtro)
    st.write("Linhas base mês:", len(base_mes))

    st.write("Primeiros clientes com LEKE no histórico:")
    clientes_leke = sorted(
        pedidos[pedidos["empresa_norm"].str.contains("LEKE", na=False)]["empresa"].dropna().astype(str).unique()
    )
    st.write(clientes_leke)

    if not pedidos_cliente.empty:
        resumo = (
            pedidos_cliente.groupby(["ano", "mes"], as_index=False)
            .agg(
                pedidos=("id_pedido", "nunique"),
                faturamento=("total_pedido", "sum")
            )
            .sort_values(["ano", "mes"])
        )
        st.dataframe(resumo, width="stretch")


# =====================================================
# RELATÓRIO DIRETORIA
# =====================================================

st.subheader("📄 Relatório da Diretoria")

pdf_path = preparar_relatorio_pdf()

if pdf_path and pdf_path.exists():
    with open(pdf_path, "rb") as f:
        st.download_button(
            label="⬇️ Baixar relatório da diretoria",
            data=f,
            file_name=pdf_path.name,
            mime="application/pdf",
        )
else:
    st.warning("Relatório da diretoria não encontrado para download.")


# =====================================================
# KPIS OPERACIONAIS
# =====================================================

st.subheader(f"📊 Indicadores operacionais — {cliente}")

faturamento_mes = base_mes["total_pedido"].sum() if not base_mes.empty else 0
faturamento_ant = base_mes_ant["total_pedido"].sum() if not base_mes_ant.empty else 0

variacao = (faturamento_mes - faturamento_ant) / faturamento_ant if faturamento_ant > 0 else 0

pedidos_mes = base_mes["id_pedido"].nunique() if not base_mes.empty else 0
ticket_medio = faturamento_mes / pedidos_mes if pedidos_mes > 0 else 0

mes_nome = nome_mes(mes_filtro)

meta_mes = 0

if not goals_base.empty and ano_filtro is not None:
    meta_ref = goals_base[
        (goals_base["mes"].astype(str) == mes_nome)
        & (goals_base["ano"].astype(str) == str(ano_filtro))
    ].copy()

    if not meta_ref.empty:
        meta_mes = meta_ref["meta_planejada_num"].sum()

atingimento = faturamento_mes / meta_mes if meta_mes > 0 else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("Faturamento mês", moeda(faturamento_mes))
c2.metric("Mês anterior", moeda(faturamento_ant))
c3.metric("Variação", percentual(variacao))
c4.metric("Pedidos", numero(pedidos_mes))
c5.metric("Ticket médio", moeda(ticket_medio))
c6.metric("% Meta", percentual(atingimento))

if ano_filtro is not None and mes_filtro is not None:
    st.caption(f"Período analisado: {mes_nome}/{ano_filtro}")
else:
    st.caption("Sem período operacional disponível para este cliente.")


# =====================================================
# EVOLUÇÃO DIÁRIA
# =====================================================

if not base_mes.empty:
    st.subheader("📈 Evolução diária de vendas")

    diario = (
        base_mes.groupby("data_pedido_dt", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique")
        )
        .sort_values("data_pedido_dt")
    )

    fig_diario = px.line(
        diario,
        x="data_pedido_dt",
        y="faturamento",
        markers=True,
        title="Faturamento diário"
    )

    st.plotly_chart(fig_diario, width="stretch")
else:
    st.info("Sem vendas no período selecionado para exibir evolução diária.")


# =====================================================
# CANAIS
# =====================================================

if not base_mes.empty:
    st.subheader("🛒 Canais de venda do mês")

    canais = (
        base_mes.groupby("canal_estrategico", as_index=False)
        .agg(
            faturamento=("total_pedido", "sum"),
            pedidos=("id_pedido", "nunique")
        )
        .sort_values("faturamento", ascending=False)
    )

    fig_canais = px.bar(
        canais,
        x="canal_estrategico",
        y="faturamento",
        title="Faturamento por canal",
        text_auto=".2s"
    )

    st.plotly_chart(fig_canais, width="stretch")

    canais_view = canais.copy()
    canais_view["faturamento"] = canais_view["faturamento"].apply(moeda)

    st.dataframe(canais_view, width="stretch")
else:
    st.info("Sem canais de venda no período selecionado.")


# =====================================================
# METAS
# =====================================================

st.subheader("🎯 Minhas metas estratégicas")

if goals_base.empty:
    st.info("Nenhuma meta encontrada.")
else:
    goals_base = goals_base.copy()

    ordem_meses = [
        "Janeiro", "Fevereiro", "Março", "Abril",
        "Maio", "Junho", "Julho", "Agosto",
        "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    goals_base["mes_ordem"] = goals_base["mes"].apply(
        lambda x: ordem_meses.index(x) + 1 if x in ordem_meses else 99
    )

    goals_plot = goals_base.sort_values("mes_ordem")

    fig_goal = px.line(
        goals_plot,
        x="mes",
        y="meta_planejada_num",
        markers=True,
        title="Rampa estratégica de faturamento"
    )

    st.plotly_chart(fig_goal, width="stretch")

    goals_view = goals_plot.copy()
    goals_view["meta_planejada_num"] = goals_view["meta_planejada_num"].apply(moeda)

    st.dataframe(goals_view.drop(columns=["mes_ordem"], errors="ignore"), width="stretch")


# =====================================================
# PLANO DE AÇÃO
# =====================================================

st.subheader("📋 Meu plano de ação")

if actions_base.empty:
    st.info("Nenhuma ação encontrada.")
else:
    colunas_acoes = [
        "periodo",
        "objetivo",
        "categoria",
        "prioridade",
        "acao",
        "prazo",
        "status_execucao",
        "percentual_conclusao",
        "impacto_esperado",
    ]

    colunas_acoes = [c for c in colunas_acoes if c in actions_base.columns]

    st.dataframe(actions_base[colunas_acoes], width="stretch")


# =====================================================
# INSIGHTS
# =====================================================

st.subheader("🤖 Insights consultivos")

if insights_base.empty:
    st.info("Nenhum insight encontrado.")
else:
    for _, row in insights_base.iterrows():
        st.markdown(
            f"""
### {row.get('tipo_insight', '')}

**Insight:** {row.get('insight', '')}

**Ação recomendada:** {row.get('acao_recomendada', '')}

---
"""
        )


# =====================================================
# EVENTOS
# =====================================================

st.subheader("🚨 Eventos relevantes")

if events_base.empty:
    st.info("Nenhum evento encontrado.")
else:
    st.dataframe(events_base, width="stretch")


# =====================================================
# TIMELINE
# =====================================================

st.subheader("🕒 Minha timeline consultiva")

if timeline_base.empty:
    st.info("Nenhuma timeline encontrada.")
else:
    st.dataframe(timeline_base, width="stretch")
