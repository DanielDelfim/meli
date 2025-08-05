import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.utils_custos import carregar_custos, obter_mes, atualizar_custo_mes
from utils.publicidade.metricas import calcular_metricas_publicidade
from utils.utils_filtros import filtrar_vendas_json_por_periodo
from utils.margem_contribuição_pond import calcular_margem_ponderada

ADS_SP_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/publicidade/ads_mes_sp.json")
ADS_MG_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/publicidade/ads_mes_mg.json")
VENDAS_SP = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas/backup_vendas_sp_pp.json")
VENDAS_MG = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas/backup_vendas_mg_pp.json")
PREC_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao/precificacao_meli.json")

def carregar_ads(path):
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_json(path)
    if "gasto_total" not in df.columns:
        if "investimento" in df.columns:
            df["gasto_total"] = df["investimento"]
        else:
            df["gasto_total"] = 0.0
    return df

def render_aba_publicidade():
    custos = carregar_custos()
    meses_existentes = [c["mes_competencia"] for c in custos]

    st.subheader("Editar / Adicionar Mês de Publicidade")
    opcao_mes_pub = st.selectbox("Selecione o mês de competência:", ["➕ Novo Mês"] + meses_existentes, key="selectbox_pub")

    if opcao_mes_pub == "➕ Novo Mês":
        mes_pub = st.text_input("Digite o mês (YYYY-MM):", datetime.today().strftime("%Y-%m"), key="input_pub")
        dados_mes = {}
    else:
        mes_pub = opcao_mes_pub
        dados_mes = obter_mes(mes_pub) or {}

    pub = dados_mes.get("publicidade", {})
    editar_pub = st.checkbox("✏️ Editar dados de publicidade")

    col1, col2 = st.columns(2)
    with col1:
        valor_ads_sp = st.number_input("Ads SP (R$):", value=float(pub.get("valor_ads_sp", 0.0)), step=0.01, disabled=not editar_pub)
        tacos_sp = st.number_input("TACoS SP (%):", value=float(pub.get("tacos_sp", 0.0)), step=0.01, disabled=not editar_pub)
        mcp_sp_manual = st.number_input("MCP SP (%):", value=float(pub.get("mcp_sp", 0.0)), step=0.01, disabled=not editar_pub)

    with col2:
        valor_ads_mg = st.number_input("Ads MG (R$):", value=float(pub.get("valor_ads_mg", 0.0)), step=0.01, disabled=not editar_pub)
        tacos_mg = st.number_input("TACoS MG (%):", value=float(pub.get("tacos_mg", 0.0)), step=0.01, disabled=not editar_pub)
        mcp_mg_manual = st.number_input("MCP MG (%):", value=float(pub.get("mcp_mg", 0.0)), step=0.01, disabled=not editar_pub)

    if editar_pub and st.button("📏 Salvar Publicidade"):
        try:
            datetime.strptime(mes_pub, "%Y-%m")
        except ValueError:
            st.error("⚠️ Mês de competência inválido. Use o formato 'YYYY-MM'.")
            st.stop()

        pub_atualizado = {
            "valor_ads_sp": valor_ads_sp,
            "valor_ads_mg": valor_ads_mg,
            "valor_ads_total": valor_ads_sp + valor_ads_mg,
            "tacos_sp": tacos_sp,
            "tacos_mg": tacos_mg,
            "mcp_sp": mcp_sp_manual,
            "mcp_mg": mcp_mg_manual
        }

        atualizar_custo_mes(mes_pub, {"publicidade": pub_atualizado})
        st.success("Publicidade salva com sucesso!")
        st.rerun()

    df_sp = carregar_ads(ADS_SP_PATH)
    df_mg = carregar_ads(ADS_MG_PATH)

    data_inicio_sp = pd.to_datetime(df_sp['desde'], errors='coerce').min().date() if 'desde' in df_sp else None
    data_fim_sp = pd.to_datetime(df_sp['ate'], errors='coerce').max().date() if 'ate' in df_sp else None
    data_inicio_mg = pd.to_datetime(df_mg['desde'], errors='coerce').min().date() if 'desde' in df_mg else None
    data_fim_mg = pd.to_datetime(df_mg['ate'], errors='coerce').max().date() if 'ate' in df_mg else None

    df_vendas_sp = filtrar_vendas_json_por_periodo(str(VENDAS_SP), data_inicio_sp, data_fim_sp, unidade="SP") if data_inicio_sp and data_fim_sp else pd.DataFrame()
    df_vendas_mg = filtrar_vendas_json_por_periodo(str(VENDAS_MG), data_inicio_mg, data_fim_mg, unidade="MG") if data_inicio_mg and data_fim_mg else pd.DataFrame()

    st.markdown("---")
    st.markdown("### 📈 Métricas de Performance")
    col1, col2 = st.columns(2)
    with col1:
        met_sp = calcular_metricas_publicidade(df_sp, df_vendas_sp)
        st.metric("ACoS SP", f"{met_sp['ACoS (%)']:.2f}%")
        st.metric("TACoS SP", f"{met_sp['TACoS (%)']:.2f}%")
        st.metric("Receita SP", f"R$ {met_sp['Investimento']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with col2:
        met_mg = calcular_metricas_publicidade(df_mg, df_vendas_mg)
        st.metric("ACoS MG", f"{met_mg['ACoS (%)']:.2f}%")
        st.metric("TACoS MG", f"{met_mg['TACoS (%)']:.2f}%")
        st.metric("Receita MG", f"R$ {met_mg['Investimento']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    if data_inicio_sp and data_fim_sp:
        df_precos = pd.read_json(PREC_PATH)
        mcp_sp = calcular_margem_ponderada(df_precos, str(VENDAS_SP), data_inicio_sp, data_fim_sp)
        mcp_mg = calcular_margem_ponderada(df_precos, str(VENDAS_MG), data_inicio_mg, data_fim_mg)

        st.markdown("---")
        st.markdown("### 📊 Margem de Contribuição Ponderada (MCP)")
        col_mcp1, col_mcp2 = st.columns(2)
        col_mcp1.metric("MCP SP", f"{mcp_sp * 100:.2f}%")
        col_mcp2.metric("MCP MG", f"{mcp_mg * 100:.2f}%")
