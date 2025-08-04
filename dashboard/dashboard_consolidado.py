import os
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.utils_filtros import filtrar_vendas_json_por_periodo

# Caminhos
BASE = Path(os.getenv("BASE_PATH", "C:/Users/dmdel/OneDrive/Aplicativos"))
CUSTOS_PATH = BASE / "Designer" / "custos.json"
VENDAS_SP_JSON = BASE / "tokens" / "vendas" / "backup_vendas_sp_pp.json"
VENDAS_MG_JSON = BASE / "tokens" / "vendas" / "backup_vendas_mg_pp.json"

def render_consolidado_financeiro():
    st.set_page_config(page_title="Receita Consolidada", layout="wide")
    st.title("📊 Receita Consolidada por Mês")

    # Carrega custos e períodos
    df_custos = pd.read_json(CUSTOS_PATH)
    df_custos['period'] = pd.to_datetime(df_custos['mes_competencia'], format="%m/%Y").dt.to_period('M')
    periods = sorted(df_custos['period'].unique())
    labels = [p.strftime("%m/%Y") for p in periods]

    sel = st.selectbox("🗓️ Mês de Competência", labels)
    period = periods[labels.index(sel)]
    start_date = period.start_time.date()
    end_date = period.end_time.date()

    st.caption(f"📅 Período: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")

    # Filtra vendas
    df_sp = filtrar_vendas_json_por_periodo(str(VENDAS_SP_JSON), start_date, end_date, unidade="SP")
    df_mg = filtrar_vendas_json_por_periodo(str(VENDAS_MG_JSON), start_date, end_date, unidade="MG")
    receita_sp = df_sp["Valor total"].sum()
    receita_mg = df_mg["Valor total"].sum()

    # Busca custos e MCP do mês
    record = df_custos[df_custos['period'] == period]
    if not record.empty:
        dados_mes = record.iloc[0].to_dict()
        custo_total = float(dados_mes.get("custo_total", 0.0))
        pub_raw = dados_mes.get("publicidade", {})
        pub = pub_raw if isinstance(pub_raw, dict) else {}

        mcp_sp = float(pub.get("mcp_sp", 0.0))
        mcp_mg = float(pub.get("mcp_mg", 0.0))

    else:
        custo_total = 0.0
        mcp_sp = 0.0
        mcp_mg = 0.0

    # Calcular margens em R$
    margem_contribuicao_sp = receita_sp * (mcp_sp / 100)
    margem_contribuicao_mg = receita_mg * (mcp_mg / 100)
    margem_total = margem_contribuicao_sp + margem_contribuicao_mg

    # Lucro ou prejuízo
    lucro_prejuizo = margem_total - custo_total

    # Layout compacto
    st.markdown("### 🔢 Receita e MCP (%)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Receita SP", f"R$ {receita_sp:,.2f}")
    col2.metric("Receita MG", f"R$ {receita_mg:,.2f}")
    col3.metric("MCP SP", f"{mcp_sp:.2f}%")
    col4.metric("MCP MG", f"{mcp_mg:.2f}%")

    st.markdown("### 💰 Margens e Custo")
    col5, col6 = st.columns(2)
    col5.metric("Margem Total (SP + MG)", f"R$ {margem_total:,.2f}")
    col6.metric("Custo Total", f"R$ {custo_total:,.2f}")

    st.markdown("### 🧾 Resultado Final")
    st.metric("Lucro / Prejuízo", f"R$ {lucro_prejuizo:,.2f}")
