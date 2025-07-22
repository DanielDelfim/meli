import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.utils_dashboard import carregar_json_para_df, preparar_periodos, aplicar_filtro

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from utils.utils_dashboard import carregar_json_para_df

def render_sp(start_date=None, end_date=None):
    st.header("📍 Dashboard de Vendas — São Paulo")

    try:
        df = carregar_json_para_df("C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_sp.json")
    except FileNotFoundError:
        st.error("Arquivo de vendas SP não encontrado!")
        return

    if df.empty:
        st.warning("Nenhuma venda encontrada para SP.")
        return

    # --- Se não vier data da página Home, usar padrão: 01 do mês até hoje ---
    if not start_date or not end_date:
        start_date = datetime.today().replace(day=1).date()
        end_date = datetime.today().date()

    # --- Filtro de datas ---
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    mask = (df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)
    dff = df[mask]

    if dff.empty:
        st.warning("Nenhuma venda encontrada no período selecionado.")
        return

    # --- Resumo ---
    df_resumo = (
        dff.groupby("Produto", as_index=False)
        .agg({"Quantidade": "sum", "Valor total": "sum"})
        .sort_values("Valor total", ascending=False)
    )

    # --- Métricas ---
    total_qt = int(dff["Quantidade"].sum())
    total_vl = dff["Valor total"].sum()
    col1, col2 = st.columns(2)
    col1.metric("Itens vendidos", total_qt)
    col2.metric("Faturamento (R$)",
        f"R$ {total_vl:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.subheader(f"Período ➔ {start_date.strftime('%d/%m/%y')} → {end_date.strftime('%d/%m/%y')}")

    # --- Tabela principal ---
    df_display = df_resumo.copy()
    df_display["Valor total"] = df_display["Valor total"].apply(
        lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    st.dataframe(df_display, use_container_width=True)

def gerar_tabela_previsao(df, df_resumo):
    """Tabela de previsão de vendas 7 e 15 dias."""
    today = pd.to_datetime("today").date()

    df15 = df_resumo[["Produto", "Quantidade"]].rename(
        columns={"Quantidade": "Quantidade 15 dias"}
    )

    start7 = pd.to_datetime(today - pd.Timedelta(days=7))
    mask7 = (df["Data da venda"] >= start7) & (df["Data da venda"] <= pd.to_datetime(today))
    df7 = df[mask7]
    df7_sum = (
        df7.groupby("Produto", as_index=False)
        .agg({"Quantidade": "sum"})
        .rename(columns={"Quantidade": "Quantidade 7 dias"})
    )

    df_prev = pd.merge(df15, df7_sum, on="Produto", how="outer").fillna(0)
    df_prev["Quantidade 15 dias"] = df_prev["Quantidade 15 dias"].astype(int)
    df_prev["Quantidade 7 dias"] = df_prev["Quantidade 7 dias"].astype(int)

    df_prev["Estimativa 30 dias (base 7)"] = (df_prev["Quantidade 7 dias"] / 7 * 30).round().astype(int)
    df_prev["Estimativa 30 dias (base 15)"] = (df_prev["Quantidade 15 dias"] / 15 * 30).round().astype(int)

    df_prev = df_prev.sort_values("Quantidade 15 dias", ascending=False)

    st.subheader("Previsão de Vendas — 7 e 15 dias")
    st.dataframe(df_prev, use_container_width=True)


def gerar_curva_abc(df_resumo):
    """Gera gráfico de Curva ABC Top 15."""
    top15 = df_resumo.head(15).copy()
    top15["Acumulado"] = top15["Valor total"].cumsum()
    total15 = top15["Valor total"].sum()
    top15["% Acumulado"] = (top15["Acumulado"] / total15 * 100).round(2)
    top15["Produto"] = pd.Categorical(
        top15["Produto"], categories=top15["Produto"].tolist(), ordered=True
    )
    fig = px.line(
        top15, x="Produto", y="% Acumulado", markers=True,
        title="Curva ABC (Top 15 Produtos)",
        category_orders={"Produto": top15["Produto"].tolist()}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
