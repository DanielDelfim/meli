import streamlit as st
import pandas as pd
from utils.precificacao.meli.precificacao_calc import calcular_e_salvar
from utils.precificacao.precificacao_parametros import PARAMETROS_PRECIFICACAO
from utils.precificacao.meli.precificacao_io import carregar_dados, salvar_dados, atualizar_linha, deletar_produto, adicionar_produto
from utils.precificacao.atualizar_parametros import atualizar_parametros

# -------------------------
# Dashboard Precificacao
# -------------------------

def render_precificacao():
    st.set_page_config(page_title="Precificacao Supramel", layout="wide")
    st.title("Dashboard de Precificacao - Supramel")

    # Botao para atualizar TACoS
    if st.button("\U0001F501 Atualizar TACoS com dados mais recentes"):
        try:
            atualizar_parametros()
            st.success("TACoS atualizados com sucesso! Recarregando página...")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar TACoS: {e}")

    # Filtro lateral para escolher o CD
    cd_selecionado = st.sidebar.selectbox("Selecione o CD Mercado Livre:", ["Araçariguama", "Betim"])

    # Carrega dados completos para edição
    df_completo = carregar_dados()
    df = calcular_e_salvar()
    df_filtrado = df[df["CD Mercado Livre"] == cd_selecionado].copy()

    marketing_padrao = PARAMETROS_PRECIFICACAO[cd_selecionado]["% Marketing do anúncio"]
    imposto_padrao = PARAMETROS_PRECIFICACAO[cd_selecionado]["% Imposto Simples Nacional"]

    df_filtrado["% Marketing do anúncio"] = marketing_padrao
    df_filtrado["% Imposto Simples Nacional"] = df_filtrado["Preço de Venda Atual (R$)"] * imposto_padrao
    df_filtrado["Frete até CD (R$)"] = df_filtrado["Preço de Compra (R$)"] * 0.08

    colunas_principais = ["Produto", "% Marketing do anúncio", "% Margem de contribuição"]
    df_principal = df_filtrado[colunas_principais].copy()

    for col in ["% Marketing do anúncio", "% Margem de contribuição"]:
        df_principal[col] = df_principal[col].map(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "")

    st.subheader(f"Produtos - CD {cd_selecionado}")
    st.dataframe(df_principal, use_container_width=True)

    produtos_unicos = df_filtrado["Produto"].dropna().unique()
    produto_selecionado = st.selectbox("Filtrar por Produto:", produtos_unicos)

    colunas_detalhes = [
        "Produto", "Preço de Venda Atual (R$)", "Preço de Compra (R$)", "Frete até CD (R$)",
        "% Imposto Simples Nacional", "% Comissão Mercado Livre", "Taxa Fixa Mercado Livre (R$)",
        "Rótulo", "Embalagem (R$)", "% Marketing do anúncio", "Desconto em Taxas ML (R$)", "% Margem de contribuição"
    ]
    df_produto = df_filtrado[df_filtrado["Produto"] == produto_selecionado][colunas_detalhes].copy()

    df_produto["% Imposto Simples Nacional"] = df_produto["% Imposto Simples Nacional"].map(lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "")
    df_produto["Embalagem (R$)"] = df_produto["Embalagem (R$)"].map(lambda x: f"R$ {x:.2f}" if pd.notnull(x) else "")
    df_produto["% Comissão Mercado Livre"] = df_produto["% Comissão Mercado Livre"].map(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "")
    df_produto["% Marketing do anúncio"] = df_produto["% Marketing do anúncio"].map(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "")
    df_produto["% Margem de contribuição"] = df_produto["% Margem de contribuição"].map(lambda x: f"{x*100:.2f}%" if pd.notnull(x) else "")

    st.subheader("Detalhes do Produto Selecionado")
    st.dataframe(df_produto.T, use_container_width=True)

    # Resto permanece igual...


    if st.checkbox("Editar produto selecionado"):
        st.subheader("Editar Campos do Produto")
        linha = df_completo[df_completo["Produto"] == produto_selecionado]
        if not linha.empty:
            produto_id = int(linha.iloc[0]["ID"])

            preco_venda = st.number_input("Preço de Venda Atual (R$)", value=float(linha.iloc[0]["Preço de Venda Atual (R$)"]), step=0.01)
            preco_compra = st.number_input("Preço de Compra (R$)", value=float(linha.iloc[0]["Preço de Compra (R$)"]), step=0.01)
            comissao = st.number_input("% Comissão Mercado Livre", value=float(linha.iloc[0]["% Comissão Mercado Livre"]), step=0.001, format="%.3f")
            taxa_fixa = st.number_input("Taxa Fixa Mercado Livre (R$)", value=float(linha.iloc[0]["Taxa Fixa Mercado Livre (R$)"]), step=0.01)
            rotulo = st.number_input("Rótulo", value=float(linha.iloc[0]["Rótulo"]), step=0.01)
            embalagem = st.number_input("Embalagem (R$)", value=float(linha.iloc[0]["Embalagem (R$)"]), step=0.01)
            desconto = st.number_input("Desconto em Taxas ML (R$)", value=float(linha.iloc[0]["Desconto em Taxas ML (R$)"]), step=0.01)

            imposto = preco_venda * imposto_padrao
            marketing = preco_venda * marketing_padrao
            frete_cd = preco_compra * 0.08
            custo_total = preco_compra + frete_cd + taxa_fixa + (preco_venda * comissao) + rotulo + embalagem + imposto + marketing - desconto
            margem = (preco_venda - custo_total) / preco_venda if preco_venda else 0

            with st.container():
                st.markdown("### 📊 Margem de Contribuição Estimada")
                st.metric("Margem de Contribuição", f"{margem*100:.2f}%")

            if st.button("Salvar alterações"):
                novos_dados = {
                    "Preço de Venda Atual (R$)": preco_venda,
                    "Preço de Compra (R$)": preco_compra,
                    "% Comissão Mercado Livre": comissao,
                    "Taxa Fixa Mercado Livre (R$)": taxa_fixa,
                    "Rótulo": rotulo,
                    "Embalagem (R$)": embalagem,
                    "Desconto em Taxas ML (R$)": desconto
                }
                df_completo_atualizado = atualizar_linha(df_completo.copy(), produto_id, novos_dados)
                salvar_dados(df_completo_atualizado)
                st.success("Produto atualizado com sucesso!")

    with st.expander("➕ Adicionar novo produto"):
        with st.form("form_adicionar_produto"):
            novo_produto = st.text_input("Nome do Produto")
            novo_cd = st.selectbox("CD Mercado Livre", ["Araçariguama", "Betim"])
            novo_preco_venda = st.number_input("Preço de Venda Atual (R$)", step=0.01)
            novo_preco_compra = st.number_input("Preço de Compra (R$)", step=0.01)
            novo_comissao = st.number_input("% Comissão Mercado Livre", step=0.001, format="%.3f")
            novo_taxa_fixa = st.number_input("Taxa Fixa Mercado Livre (R$)", step=0.01)
            novo_rotulo = st.number_input("Rótulo", step=0.01)
            novo_embalagem = st.number_input("Embalagem (R$)", step=0.01)
            novo_desconto = st.number_input("Desconto em Taxas ML (R$)", step=0.01)
            submitted = st.form_submit_button("Adicionar")
            if submitted:
                novo_id = int(df_completo["ID"].max()) + 1 if not df_completo.empty else 1
                novo_dict = {
                    "ID": novo_id,
                    "Produto": novo_produto,
                    "CD Mercado Livre": novo_cd,
                    "Preço de Venda Atual (R$)": novo_preco_venda,
                    "Preço de Compra (R$)": novo_preco_compra,
                    "% Comissão Mercado Livre": novo_comissao,
                    "Taxa Fixa Mercado Livre (R$)": novo_taxa_fixa,
                    "Rótulo": novo_rotulo,
                    "Embalagem (R$)": novo_embalagem,
                    "Desconto em Taxas ML (R$)": novo_desconto
                }
                df_atualizado = adicionar_produto(df_completo.copy(), novo_dict)
                salvar_dados(df_atualizado)
                st.success("Produto adicionado com sucesso!")

    if st.checkbox("❌ Deletar produto selecionado"):
        produto_id = int(df_completo[df_completo["Produto"] == produto_selecionado].iloc[0]["ID"])
        if st.button("Confirmar exclusão"):
            df_atualizado = deletar_produto(df_completo.copy(), produto_id)
            salvar_dados(df_atualizado)
            st.success("Produto removido com sucesso!")
