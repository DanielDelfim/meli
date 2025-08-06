def render_precificacao():
    import streamlit as st
    import pandas as pd
    from utils.precificacao.meli.precificacao_calc import calcular_e_salvar
    from utils.precificacao.precificacao_parametros import PARAMETROS_PRECIFICACAO
    from utils.precificacao.meli.precificacao_io import carregar_dados, salvar_dados, atualizar_linha, deletar_produto, adicionar_produto
    from utils.precificacao.atualizar_parametros import atualizar_parametros

    st.set_page_config(page_title="Precificacao Supramel", layout="wide")
    st.title("Dashboard de Precificacao - Supramel")

    if st.button("🔁 Atualizar TACoS com dados mais recentes"):
        try:
            atualizar_parametros()
            st.success("TACoS atualizados com sucesso! Recarregando página...")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar TACoS: {e}")

    cd_selecionado = st.sidebar.selectbox("Selecione o CD Mercado Livre:", ["Araçariguama", "Betim"])

    df_completo = carregar_dados()

    for coluna in ["SKU", "Código do anúncio"]:
        if coluna not in df_completo.columns:
            df_completo[coluna] = ""

    df = calcular_e_salvar()
    df_filtrado = df[df["CD Mercado Livre"] == cd_selecionado].copy()

    df_filtrado["SKU"] = df_completo.loc[df_filtrado.index, "SKU"]
    df_filtrado["Código do anúncio"] = df_completo.loc[df_filtrado.index, "Código do anúncio"]

    marketing_padrao = PARAMETROS_PRECIFICACAO[cd_selecionado]["% Marketing do anúncio"]
    imposto_padrao = PARAMETROS_PRECIFICACAO[cd_selecionado]["% Imposto Simples Nacional"]

    df_filtrado["% Marketing do anúncio"] = marketing_padrao
    df_filtrado["% Imposto Simples Nacional"] = df_filtrado["Preço de Venda Atual (R$)"] * imposto_padrao
    df_filtrado["Frete até CD (R$)"] = df_filtrado["Preço de Compra (R$)"] * 0.08

    colunas_principais = ["Produto", "% Marketing do anúncio", "% Margem de contribuição"]
    df_principal = df_filtrado[colunas_principais].copy()

    def formatar_percentual(x):
        try:
            return f"{float(x)*100:.2f}%"
        except:
            return ""

    for col in ["% Marketing do anúncio", "% Margem de contribuição"]:
        df_principal[col] = df_principal[col].map(formatar_percentual)

    # Produto selecionado e controle de contexto
    produtos_unicos = df_filtrado["Produto"].dropna().unique()
    produto_selecionado = st.selectbox("Filtrar por Produto:", produtos_unicos, key="produto_unico")
    filtrar_contexto = st.checkbox("☑️ Filtrar contexto da tabela acima pelo produto selecionado")

    st.subheader(f"Produtos - CD {cd_selecionado}")
    if filtrar_contexto:
        df_contexto = df_principal[df_principal["Produto"] == produto_selecionado]
    else:
        df_contexto = df_principal
    st.dataframe(df_contexto, use_container_width=True)

    # Detalhes e edição do produto selecionado
    linha = df_completo[df_completo["Produto"] == produto_selecionado]
    if linha.empty:
        st.warning("Produto não encontrado.")
        return
    linha = linha.iloc[0]
    produto_id = int(linha["ID"])

    modo_edicao = st.checkbox("✏️ Editar produto selecionado")
    st.subheader("Detalhes do Produto Selecionado")

    col1, col2, col3 = st.columns(3)
    with col1:
        sku = st.text_input("SKU", value=linha.get("SKU", ""), disabled=not modo_edicao)
        preco_venda = st.number_input("Preço de Venda Atual (R$)", value=float(linha["Preço de Venda Atual (R$)"]), step=0.01, disabled=not modo_edicao)
        taxa_fixa = st.number_input("Taxa Fixa Mercado Livre (R$)", value=float(linha["Taxa Fixa Mercado Livre (R$)"]), step=0.01, disabled=not modo_edicao)
        rotulo = st.number_input("Rótulo", value=float(linha["Rótulo"]), step=0.01, disabled=not modo_edicao)
    with col2:
        codigo_anuncio = st.text_input("Código do anúncio", value=linha.get("Código do anúncio", ""), disabled=not modo_edicao)
        preco_compra = st.number_input("Preço de Compra (R$)", value=float(linha["Preço de Compra (R$)"]), step=0.01, disabled=not modo_edicao)
        comissao = st.number_input("% Comissão Mercado Livre", value=float(linha["% Comissão Mercado Livre"]), step=0.001, format="%.3f", disabled=not modo_edicao)
        embalagem = st.number_input("Embalagem (R$)", value=float(linha["Embalagem (R$)"]), step=0.01, disabled=not modo_edicao)
    with col3:
        desconto = st.number_input("Desconto em Taxas ML (R$)", value=float(linha["Desconto em Taxas ML (R$)"]), step=0.01, disabled=not modo_edicao)

    imposto = preco_venda * imposto_padrao
    marketing = preco_venda * marketing_padrao
    frete_cd = preco_compra * 0.08
    custo_total = preco_compra + frete_cd + taxa_fixa + (preco_venda * comissao) + rotulo + embalagem + imposto + marketing - desconto
    margem = (preco_venda - custo_total) / preco_venda if preco_venda else 0

    st.markdown("### 📊 Margem de Contribuição Estimada")
    st.metric("Margem de Contribuição", f"{margem*100:.2f}%")

    if modo_edicao and st.button("💾 Salvar alterações"):
        novos_dados = {
            "SKU": sku,
            "Código do anúncio": codigo_anuncio,
            "Preço de Venda Atual (R$)": preco_venda,
            "Preço de Compra (R$)": preco_compra,
            "% Comissão Mercado Livre": comissao,
            "Taxa Fixa Mercado Livre (R$)": taxa_fixa,
            "Rótulo": rotulo,
            "Embalagem (R$)": embalagem,
            "Desconto em Taxas ML (R$)": desconto
        }
        df_atualizado = atualizar_linha(df_completo.copy(), produto_id, novos_dados)
        salvar_dados(df_atualizado)
        st.success("Produto atualizado com sucesso!")
        st.rerun()

    # Exclusão
    if st.checkbox("❌ Deletar produto selecionado"):
        if st.button("Confirmar exclusão"):
            df_novo = deletar_produto(df_completo.copy(), produto_id)
            salvar_dados(df_novo)
            st.success("Produto removido com sucesso!")
            st.rerun()