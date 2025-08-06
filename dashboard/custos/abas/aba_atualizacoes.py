import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

from utils.custos.atualizar_pesos import atualizar_pesos_em_precificacao, calcular_pesos_por_estado
from utils.utils_filtros import filtrar_vendas_json_por_periodo, quantidade_vendida_por_sku, buscar_valor_por_prefixo
from utils.precificacao.meli.atualizar_peso_quantidade import calcular_peso_quantidade, atualizar_json_com_peso_quantidade
from utils.precificacao.margem_pond_venda_e_quant import atualizar_margens_ponderadas
from utils.utils_datas import obter_data_inicio_fim_mes, obter_lista_meses_existentes, selecionar_mes_competencia
from utils.utils_custos import atualizar_custo_mes

CAMINHO_VENDAS_SP = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas/backup_vendas_sp_pp.json")
CAMINHO_VENDAS_MG = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas/backup_vendas_mg_pp.json")
CAMINHO_JSON_PRECIFICACAO = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao/precificacao_meli.json")

SKU_ALVO = "7898915380927"

def render_aba_atualizacoes():
    st.subheader("📘 Atualizar Pesos e Informações do SKU")

    if "mcp_pond_sp" not in st.session_state:
        st.session_state["mcp_pond_sp"] = 0.0
    if "mcp_pond_mg" not in st.session_state:
        st.session_state["mcp_pond_mg"] = 0.0

    mes_competencia = selecionar_mes_competencia(obter_lista_meses_existentes())

    # Exibe valores já salvos para o mês, se existirem
    from utils.utils_custos import obter_mes
    dados_salvos = obter_mes(mes_competencia)
    if dados_salvos and any(k in dados_salvos for k in ["mcp_sp", "mcp_mg"]):
        st.markdown("### 💾 Dados Salvos para o Mês")
        col1, col2 = st.columns(2)
        col1.metric("🟦 MCP SP Salva", f"{dados_salvos.get('mcp_sp', 0.0):.2%}")
        col2.metric("🟩 MCP MG Salva", f"{dados_salvos.get('mcp_mg', 0.0):.2%}")
    data_inicio, data_fim = obter_data_inicio_fim_mes(mes_competencia)

    if st.button("🔁 Atualizar Pesos e Exibir Info do SKU"):
        # Atualiza pesos financeiros
        atualizar_pesos_em_precificacao()
        pesos_sp, _ = calcular_pesos_por_estado(CAMINHO_VENDAS_SP, data_inicio, data_fim, "SP")
        pesos_mg, _ = calcular_pesos_por_estado(CAMINHO_VENDAS_MG, data_inicio, data_fim, "MG")

        # Quantidade vendida e valor vendido por SKU
        df_sp_vendas = filtrar_vendas_json_por_periodo(str(CAMINHO_VENDAS_SP), data_inicio, data_fim)
        df_mg_vendas = filtrar_vendas_json_por_periodo(str(CAMINHO_VENDAS_MG), data_inicio, data_fim)

        qtd_sp = quantidade_vendida_por_sku(df_sp_vendas)
        qtd_mg = quantidade_vendida_por_sku(df_mg_vendas)

        qtd_vendida_sp = int(qtd_sp[qtd_sp["SKU"].astype(str).str.startswith(SKU_ALVO)]["Qtd Vendida"].sum())
        qtd_vendida_mg = int(qtd_mg[qtd_mg["SKU"].astype(str).str.startswith(SKU_ALVO)]["Qtd Vendida"].sum())

        valor_sp = df_sp_vendas[df_sp_vendas["SKU"].astype(str).str.startswith(SKU_ALVO)]["Valor total"].sum()
        valor_mg = df_mg_vendas[df_mg_vendas["SKU"].astype(str).str.startswith(SKU_ALVO)]["Valor total"].sum()

        # Calcula peso_quantidade por SKU
        pesos_qtd_sp = calcular_peso_quantidade(CAMINHO_VENDAS_SP, data_inicio, data_fim, "Araçariguama", "peso_quantidade_sp")
        pesos_qtd_mg = calcular_peso_quantidade(CAMINHO_VENDAS_MG, data_inicio, data_fim, "Betim", "peso_quantidade_mg")
        atualizar_json_com_peso_quantidade(CAMINHO_JSON_PRECIFICACAO, pesos_qtd_sp, pesos_qtd_mg)

        # Atualiza margens ponderadas
        atualizar_margens_ponderadas(
            caminho_json_precificacao=CAMINHO_JSON_PRECIFICACAO,
            caminho_vendas_sp=CAMINHO_VENDAS_SP,
            caminho_vendas_mg=CAMINHO_VENDAS_MG,
            data_inicio=data_inicio,
            data_fim=data_fim
        )

        # Carrega JSON atualizado para buscar MCPs
        df_prec = pd.read_json(CAMINHO_JSON_PRECIFICACAO)
        st.session_state["mcp_pond_sp"] = df_prec["mcp_ponderada_sp"].iloc[0]
        st.session_state["mcp_pond_mg"] = df_prec["mcp_ponderada_mg"].iloc[0]

        # Salva também os dados do SKU em session_state
        st.session_state["detalhes_sku"] = {
            "qtd_vendida_sp": qtd_vendida_sp,
            "qtd_vendida_mg": qtd_vendida_mg,
            "valor_sp": valor_sp,
            "valor_mg": valor_mg,
            "peso_qtd_sp": buscar_valor_por_prefixo(pesos_qtd_sp, SKU_ALVO),
            "peso_qtd_mg": buscar_valor_por_prefixo(pesos_qtd_mg, SKU_ALVO),
            "peso_fin_sp": buscar_valor_por_prefixo(pesos_sp, SKU_ALVO),
            "peso_fin_mg": buscar_valor_por_prefixo(pesos_mg, SKU_ALVO)
        }

        st.success("✅ Dados atualizados. Revise antes de salvar.")

    if st.button("💾 Salvar MCP Ponderada no mês"):
        atualizar_custo_mes(mes_competencia, {
            "mcp_sp": st.session_state["mcp_pond_sp"],
            "mcp_mg": st.session_state["mcp_pond_mg"]
        })
        st.success(f"💾 MCP Ponderada salva com sucesso para {mes_competencia}.")

    if "detalhes_sku" in st.session_state:
        dados = st.session_state["detalhes_sku"]

        st.markdown("### 🔍 Detalhes do SKU Selecionado")
        col_sp, col_mg = st.columns(2)

        with col_sp:
            st.markdown("#### 🟦 SP (Araçariguama)")
            st.metric("Quantidade Vendida", dados["qtd_vendida_sp"])
            st.metric("Valor de Vendas", f"R$ {dados['valor_sp']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.metric("Peso Quantidade", f"{dados['peso_qtd_sp']:.6f}")
            st.metric("Peso Financeiro", f"{dados['peso_fin_sp']:.6f}")

        with col_mg:
            st.markdown("#### 🟩 MG (Betim)")
            st.metric("Quantidade Vendida", dados["qtd_vendida_mg"])
            st.metric("Valor de Vendas", f"R$ {dados['valor_mg']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.metric("Peso Quantidade", f"{dados['peso_qtd_mg']:.6f}")
            st.metric("Peso Financeiro", f"{dados['peso_fin_mg']:.6f}")

        st.markdown("### 📉 Margem de Contribuição Ponderada Final")
        col_mcp1, col_mcp2 = st.columns(2)
        col_mcp1.metric("🟦 MCP Ponderada SP", f"{st.session_state['mcp_pond_sp']:.2%}")
        col_mcp2.metric("🟩 MCP Ponderada MG", f"{st.session_state['mcp_pond_mg']:.2%}")
