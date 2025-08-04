import pandas as pd
import streamlit as st
from datetime import datetime
from pathlib import Path
from utils.utils_custos import (
    carregar_custos,
    salvar_custos,
    obter_mes,
    atualizar_custo_mes,
    adicionar_novo_custo_a_todos_os_meses,
    excluir_mes
)
from utils.publicidade.metricas import calcular_metricas_publicidade

ADS_SP_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/publicidade/ads_mes_sp.json")
ADS_MG_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/publicidade/ads_mes_mg.json")


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


def render_custos_dashboard():
    st.set_page_config("Custos Fixos e Publicidade", layout="wide")
    st.title("💰 Controle de Custos Fixos e Publicidade")

    tabs = st.tabs(["📦 Custos Fixos", "📢 Publicidade Mercado Livre"])

    # --------------------- ABA 1 - CUSTOS FIXOS ---------------------
    with tabs[0]:
        custos = carregar_custos()
        meses_existentes = [c["mes_competencia"] for c in custos]

        st.subheader("Histórico de Custos Fixos")
        if custos:
            df_resumo = pd.DataFrame(custos)
            if "custo_total" not in df_resumo.columns or df_resumo["custo_total"].isnull().any():
                df_resumo["custo_total"] = df_resumo.apply(lambda row: sum(
                    v for k, v in row.items() if isinstance(v, (int, float)) and k != "custo_total" and not isinstance(v, dict)
                ), axis=1)
            st.dataframe(df_resumo[["mes_competencia", "custo_total"]].sort_values("mes_competencia", ascending=False), use_container_width=True)

        st.markdown("---")
        st.subheader("Editar / Adicionar Mês de Custo")
        opcao_mes = st.selectbox("Selecione o mês de competência:", ["➕ Novo Mês"] + meses_existentes)

        if opcao_mes == "➕ Novo Mês":
            mes = st.text_input("Digite o mês (MM/AAAA):", datetime.today().strftime("%m/%Y"))
            dados = {}
        else:
            mes = opcao_mes
            dados = obter_mes(mes) or {}

        editar = st.checkbox("✏️ Editar valores deste mês")

        campos_fixos = list(dados.keys()) if dados else [
            "salario_janaine", "salario_ivanete", "salario_daniel", "decimo_terceiro",
            "tarifa_bb", "contador", "deposito_sp", "internet", "agua", "luz",
            "fgts", "inss", "tiny", "gustavo"
        ]

        valores = {}
        cols = st.columns(3)
        for i, campo in enumerate(campos_fixos):
            if campo not in ["mes_competencia", "custo_total", "publicidade"]:
                with cols[i % 3]:
                    if editar:
                        valores[campo] = st.number_input(
                            campo.replace("_", " ").capitalize() + " (R$):",
                            value=float(dados.get(campo, 0.0)),
                            step=0.01,
                            key=f"val_{campo}"
                        )
                    else:
                        valores[campo] = float(dados.get(campo, 0.0))
                        st.markdown(f"**{campo.replace('_', ' ').capitalize()}:** R$ {valores[campo]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        st.markdown("---")
        st.subheader("Adicionar Novo Custo Fixo a Todos os Meses")
        col_novo1, col_novo2 = st.columns([2, 1])
        novo_nome = col_novo1.text_input("Nome do Novo Custo:")
        novo_valor = col_novo2.number_input("Valor Inicial (R$):", min_value=0.0, step=0.01)

        if st.button("➕ Adicionar Custo Fixo Global") and novo_nome:
            adicionar_novo_custo_a_todos_os_meses(novo_nome, novo_valor)
            st.success(f"Custo '{novo_nome}' adicionado a todos os meses.")
            st.rerun()

        if editar and st.button("📂 Salvar Todos os Dados do Mês"):
            atualizar_custo_mes(mes, valores)
            st.success("Custos salvos com sucesso!")
            st.rerun()

# --------------------- ABA 2 - PUBLICIDADE ---------------------
    with tabs[1]:
        custos = carregar_custos()
        meses = [c["mes_competencia"] for c in custos]

        st.subheader("Investimentos Publicidade por Mês")

        df_sp = carregar_ads(ADS_SP_PATH)
        df_mg = carregar_ads(ADS_MG_PATH)

        if not df_sp.empty or not df_mg.empty:
            st.markdown("### Dados Gerais de Investimento - Arquivo JSON")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**SP:**")
                data_inicio_sp = pd.to_datetime(df_sp['desde'], errors='coerce').min().date() if 'desde' in df_sp else None
                data_fim_sp = pd.to_datetime(df_sp['ate'], errors='coerce').max().date() if 'ate' in df_sp else None
                st.markdown(f"- Desde: {data_inicio_sp or '—'}")
                st.markdown(f"- Até: {data_fim_sp or '—'}")
                investimento_sp = df_sp["investimento_(moeda_local)"].sum() if "investimento_(moeda_local)" in df_sp.columns else 0
                st.markdown(f"- Investimento: R$ {investimento_sp:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with col2:
                st.markdown("**MG:**")
                data_inicio_mg = pd.to_datetime(df_mg['desde'], errors='coerce').min().date() if 'desde' in df_mg else None
                data_fim_mg = pd.to_datetime(df_mg['ate'], errors='coerce').max().date() if 'ate' in df_mg else None
                st.markdown(f"- Desde: {data_inicio_mg or '—'}")
                st.markdown(f"- Até: {data_fim_mg or '—'}")
                investimento_mg = df_mg["investimento_(moeda_local)"].sum() if "investimento_(moeda_local)" in df_mg.columns else 0
                st.markdown(f"- Investimento: R$ {investimento_mg:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

        # ACOS e TACOS
        from utils.utils_filtros import filtrar_vendas_json_por_periodo
        VENDAS_SP = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas/backup_vendas_sp_pp.json")
        VENDAS_MG = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas/backup_vendas_mg_pp.json")

        df_vendas_sp = filtrar_vendas_json_por_periodo(str(VENDAS_SP), data_inicio_sp, data_fim_sp, unidade="SP") if data_inicio_sp and data_fim_sp else pd.DataFrame()
        df_vendas_mg = filtrar_vendas_json_por_periodo(str(VENDAS_MG), data_inicio_mg, data_fim_mg, unidade="MG") if data_inicio_mg and data_fim_mg else pd.DataFrame()

        st.markdown("---")
        st.markdown("### Métricas de Performance")
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

        # Seletor de mês e edição dos valores
        mes_pub = st.selectbox("Selecione o mês de competência:", meses)
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

            total = valor_ads_sp + valor_ads_mg
            st.metric("Investimento Total", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

            if editar_pub and st.button("📏 Salvar Publicidade"):
                pub_atualizado = {
                    "valor_ads_sp": valor_ads_sp,
                    "valor_ads_mg": valor_ads_mg,
                    "valor_ads_total": total,
                    "tacos_sp": tacos_sp,
                    "tacos_mg": tacos_mg,
                    "mcp_sp": mcp_sp_manual,
                    "mcp_mg": mcp_mg_manual
    }

                dados_mes["publicidade"] = pub_atualizado
                atualizar_custo_mes(mes_pub, dados_mes)
                st.success("Publicidade salva com sucesso!")
                st.rerun()

            # ---------------- MCP SP e MG ----------------
        from utils.margem_contribuição_pond import calcular_margem_ponderada
        PREC_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao_meli.json")

        if data_inicio_sp and data_fim_sp:
            df_precos = pd.read_json(PREC_PATH)
            mcp_sp = calcular_margem_ponderada(df_precos, str(VENDAS_SP), data_inicio_sp, data_fim_sp)
            mcp_mg = calcular_margem_ponderada(df_precos, str(VENDAS_MG), data_inicio_mg, data_fim_mg)

            st.markdown("---")
            st.markdown("### 📈 Margem de Contribuição Ponderada (MCP)")
            col_mcp1, col_mcp2 = st.columns(2)
            col_mcp1.metric("MCP SP", f"{mcp_sp * 100:.2f}%")
            col_mcp2.metric("MCP MG", f"{mcp_mg * 100:.2f}%")

