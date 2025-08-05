import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from utils.custos.atualizar_pesos import atualizar_pesos_em_precificacao, calcular_pesos_por_estado

def encontrar_peso_por_prefixo(sku_prefixo: str, pesos_dict: dict) -> float:
    for sku, peso in pesos_dict.items():
        if str(sku).startswith(str(sku_prefixo)):
            return round(peso, 6)
    return 0.0

def encontrar_valor_por_cd(sku_prefixo: str, df: pd.DataFrame, coluna: str, cd_nome: str) -> float:
    for _, row in df.iterrows():
        if (
            str(row.get("SKU", "")).startswith(str(sku_prefixo)) and
            str(row.get("CD Mercado Livre", "")).strip().lower() == cd_nome.strip().lower()
        ):
            try:
                return round(float(row.get(coluna, 0.0)), 6)
            except (ValueError, TypeError):
                return 0.0
    return 0.0

def encontrar_margem_por_cd(sku_prefixo: str, df: pd.DataFrame, cd_nome: str) -> float:
    for _, row in df.iterrows():
        if (
            str(row.get("SKU", "")).startswith(str(sku_prefixo)) and
            str(row.get("CD Mercado Livre", "")).strip().lower() == cd_nome.strip().lower()
        ):
            try:
                return round(float(row.get("% Margem de contribuição", 0.0)), 4)
            except (ValueError, TypeError):
                return 0.0
    return 0.0

def calcular_mcp_ponderada(df: pd.DataFrame, cd_nome: str, coluna_peso: str) -> float:
    total_contribuicao = 0.0
    total_peso = 0.0

    for _, row in df.iterrows():
        if str(row.get("CD Mercado Livre", "")).strip().lower() == cd_nome.strip().lower():
            try:
                margem = float(row.get("% Margem de contribuição", 0.0))
                peso = float(row.get(coluna_peso, 0.0))

                if pd.notna(margem) and pd.notna(peso) and peso > 0:
                    total_contribuicao += margem * peso
                    total_peso += peso

            except (ValueError, TypeError):
                continue

    if total_peso == 0:
        return 0.0  # evita divisão por zero

    return round(total_contribuicao / total_peso, 4)


def render_aba_atualizacoes():
    st.subheader("📘 Atualizar Pesos de SKU com Base em Julho/2025")

    SKU_ALVO = "7898915380927"
    CAMINHO_VENDAS_SP = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas/backup_vendas_sp_pp.json")
    CAMINHO_VENDAS_MG = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas/backup_vendas_mg_pp.json")
    CAMINHO_JSON_PRECIFICACAO = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao/precificacao_meli.json")

    data_inicio = datetime.strptime("2025-07-01", "%Y-%m-%d").date()
    data_fim = datetime.strptime("2025-07-31", "%Y-%m-%d").date()

    if st.button("🔁 Atualizar Pesos e Exibir Info do SKU"):
        # 🔄 Atualiza pesos
        atualizar_pesos_em_precificacao()

        # 📥 Calcula pesos e vendas por estado
        pesos_sp, vendas_sp = calcular_pesos_por_estado(CAMINHO_VENDAS_SP, data_inicio, data_fim, "SP")
        pesos_mg, vendas_mg = calcular_pesos_por_estado(CAMINHO_VENDAS_MG, data_inicio, data_fim, "MG")

        peso_sp = encontrar_peso_por_prefixo(SKU_ALVO, pesos_sp)
        peso_mg = encontrar_peso_por_prefixo(SKU_ALVO, pesos_mg)

        st.success("✅ Pesos atualizados com sucesso!")

        # 📊 Vendas e Peso Calculado
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📈 Vendas Totais (Julho/2025)")
            st.markdown(f"- **SP:** R$ {vendas_sp:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            st.markdown(f"- **MG:** R$ {vendas_mg:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        with col2:
            st.markdown(f"### 🧪 Peso do SKU `:green[{SKU_ALVO}]`")
            st.markdown(f"- **Peso SP (calculado):** {peso_sp:.6f}")
            st.markdown(f"- **Peso MG (calculado):** {peso_mg:.6f}")

        # 📦 Dados do JSON de Precificação
        st.markdown("---")
        st.markdown("### 📦 Dados do SKU no JSON de Precificação")

        df_precificacao = pd.read_json(CAMINHO_JSON_PRECIFICACAO)

        margem_sp = encontrar_margem_por_cd(SKU_ALVO, df_precificacao, "Araçariguama")
        margem_mg = encontrar_margem_por_cd(SKU_ALVO, df_precificacao, "Betim")

        peso_sp_json = encontrar_valor_por_cd(SKU_ALVO, df_precificacao, "peso_sp", "Araçariguama")
        peso_mg_json = encontrar_valor_por_cd(SKU_ALVO, df_precificacao, "peso_mg", "Betim")

        colsp, colmg = st.columns(2)
        with colsp:
            st.markdown("**🟦 SP (Araçariguama)**")
            st.markdown(f"- **Margem de contribuição:** {margem_sp:.2%}")
            st.markdown(f"- **Peso no JSON:** {peso_sp_json:.6f}")

        with colmg:
            st.markdown("**🟩 MG (Betim)**")
            st.markdown(f"- **Margem de contribuição:** {margem_mg:.2%}")
            st.markdown(f"- **Peso no JSON:** {peso_mg_json:.6f}")

        # 📊 Margem de Contribuição Ponderada
        st.markdown("---")
        st.markdown("### 📊 Margem de Contribuição Ponderada (MCP)")

        mcp_sp = calcular_mcp_ponderada(df_precificacao, "Araçariguama", "peso_sp")
        mcp_mg = calcular_mcp_ponderada(df_precificacao, "Betim", "peso_mg")

        col_mcp_sp, col_mcp_mg = st.columns(2)
        with col_mcp_sp:
            st.metric(label="🟦 MCP SP (Araçariguama)", value=f"{mcp_sp:.2%}")
        with col_mcp_mg:
            st.metric(label="🟩 MCP MG (Betim)", value=f"{mcp_mg:.2%}")

        # 🏋️‍♂️ Top 10 Produtos com Maior Peso por Estado
        st.markdown("---")

                # SP
        df_sp = df_precificacao[df_precificacao["CD Mercado Livre"] == "Araçariguama"].copy()
        df_sp["Margem"] = pd.to_numeric(df_sp["% Margem de contribuição"], errors="coerce")
        df_sp["Peso"] = pd.to_numeric(df_sp["peso_sp"], errors="coerce")
        df_sp["Contribuição"] = df_sp["Margem"] * df_sp["Peso"]

        top_sp = df_sp.sort_values(by="Peso", ascending=False).head(10)[["Produto", "SKU", "Margem", "Peso", "Contribuição"]]

        st.markdown("### 🟦 Top 10 Produtos com Maior Peso - SP (Araçariguama)")
        st.dataframe(top_sp)

        # MG
        df_mg = df_precificacao[df_precificacao["CD Mercado Livre"] == "Betim"].copy()
        df_mg["Margem"] = pd.to_numeric(df_mg["% Margem de contribuição"], errors="coerce")
        df_mg["Peso"] = pd.to_numeric(df_mg["peso_mg"], errors="coerce")
        df_mg["Contribuição"] = df_mg["Margem"] * df_mg["Peso"]

        top_mg = df_mg.sort_values(by="Peso", ascending=False).head(10)[["Produto", "SKU", "Margem", "Peso", "Contribuição"]]

        st.markdown("### 🟩 Top 10 Produtos com Maior Peso - MG (Betim)")
        st.dataframe(top_mg)
