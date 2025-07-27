import streamlit as st
from utils.precificacao_calc import calcular_margens
from utils.precificacao_io import carregar_dados, salvar_alteracoes_json, deletar_produto, adicionar_produto
from utils.margem_contribuição_pond import calcular_margem_ponderada
from utils.utils_dashboard import DESIGNER_PATH

JSON_SP = f"{DESIGNER_PATH}/backup_vendas_sp.json"
JSON_MG = f"{DESIGNER_PATH}/backup_vendas_mg.json"  # Novo JSON para MG

CAMPOS_EDITAVEIS = [
    "ID do anúncio",
    "Preço de Venda Atual (R$)",
    "Preço de Compra (R$)",
    "Rótulo",
    "Embalagem (R$)",
    "% Comissão Mercado Livre",
    "Frete Mercado Livre (R$)",
    "Taxa Fixa Mercado Livre (R$)",
    "Desconto em Taxas ML (R$)"
]


# ------------------- FUNÇÕES -------------------

def render_filtros_precificacao(df):
    cds_disponiveis = sorted(df["CD Mercado Livre"].dropna().unique().tolist())
    cds_opcoes = ["Todos"] + cds_disponiveis
    cd_sel = st.sidebar.selectbox("Filtrar por CD Mercado Livre:", cds_opcoes)
    if cd_sel != "Todos":
        df = df[df["CD Mercado Livre"] == cd_sel]

    filtro = st.text_input("🔍 Buscar produto:", "")
    if filtro:
        df = df[df["Produto"].str.contains(filtro, case=False, na=False)]

    return df


def render_tabela_precificacao(df_filtrado):
    colunas_tabela = ["ID", "CD Mercado Livre", "Produto",
                      "Lucro/Prejuízo Real (R$)", "% Margem de contribuição", "% Marketing do anúncio"]
    colunas_existentes = [c for c in colunas_tabela if c in df_filtrado.columns]
    df_exibir = df_filtrado[colunas_existentes].copy()

    if "Lucro/Prejuízo Real (R$)" in df_exibir.columns:
        df_exibir["Lucro/Prejuízo Real (R$)"] = df_exibir["Lucro/Prejuízo Real (R$)"].apply(
            lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )
    for col in ["% Margem de contribuição", "% Marketing do anúncio"]:
        if col in df_exibir.columns:
            df_exibir[col] = (df_exibir[col] * 100).apply(lambda x: f"{x:.2f}%")

    st.dataframe(df_exibir, use_container_width=True)


def render_margens_cards(df_precos):
    """Renderiza os dois cards de Margem Contribuição Ponderada (SP e MG)."""
    st.markdown("### Métricas Ponderadas (30 dias)")
    col_sp, col_mg = st.columns(2)

    # SP (Araçariguama)
    margem_sp = calcular_margem_ponderada(df_precos, JSON_SP, dias=30, cd="Araçariguama")
    col_sp.metric("Margem Contribuição Ponderada SP", f"{margem_sp * 100:.2f}%" if margem_sp > 0 else "0.00%")

    # MG (Betim)
    margem_mg = calcular_margem_ponderada(df_precos, JSON_MG, dias=30, cd="Betim")
    col_mg.metric("Margem Contribuição Ponderada MG", f"{margem_mg * 100:.2f}%" if margem_mg > 0 else "0.00%")


def render_edicao_produto(df_filtrado):
    opcoes = [f"{row['Produto']} (ID {row['ID']})" for _, row in df_filtrado.iterrows()]
    produto_sel = st.selectbox("Selecione um produto para editar:", opcoes)
    id_sel = int(produto_sel.split("ID ")[1].replace(")", ""))
    produto_df = df_filtrado[df_filtrado["ID"] == id_sel].copy()

    st.subheader(f"Edição — {produto_df['Produto'].values[0]}")
    edits = {}
    cols = st.columns(3)
    for i, campo in enumerate(CAMPOS_EDITAVEIS):
        val = produto_df[campo].values[0] if campo in produto_df.columns else ""
        col_st = cols[i % 3]
        if campo == "ID do anúncio":
            edits[campo] = col_st.text_input(campo, value=str(val))
        elif "%" in campo:
            percentage_val = float(val or 0) * 100 if val != "" else 0.0
            edits[campo] = col_st.number_input(campo, value=percentage_val, step=0.01) / 100
        else:
            numeric_val = float(val or 0) if val != "" else 0.0
            edits[campo] = col_st.number_input(campo, value=numeric_val, step=0.01)

    try:
        frete_cd, imposto, custo_total, lucro_real, margem_pct = calcular_margens(edits)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Frete até CD (R$)", f"R$ {frete_cd:.2f}")
        col2.metric("Imposto (10%)", f"R$ {imposto:.2f}")
        col3.metric("Lucro (R$)", f"R$ {lucro_real:.2f}")
        col4.metric("Margem (%)", f"{margem_pct:.2f}%")
    except Exception as e:
        st.error(f"Erro ao calcular margens: {e}")

    col_b1, col_b2 = st.columns([1, 1])
    if col_b1.button("💾 Salvar Alterações"):
        if not edits.get("ID do anúncio"):
            st.error("⚠️ 'ID do anúncio' é obrigatório para salvar.")
        elif salvar_alteracoes_json(id_sel, edits):
            st.success("Alterações salvas com sucesso!")
            st.rerun()

    if col_b2.button("🗑️ Deletar Produto"):
        deletar_produto(id_sel)
        st.warning("Produto excluído com sucesso!")
        st.rerun()

    st.markdown("---")
    st.subheader("➕ Adicionar Novo Produto")
    col_add1, col_add2, col_add3 = st.columns(3)
    produto_novo = col_add1.text_input("Nome do Produto:")
    id_anuncio_novo = col_add2.text_input("ID do anúncio:")
    cd_novo = col_add3.selectbox("CD Mercado Livre:", ["", "Araçariguama", "Betim", "Guarapari"])
    preco_compra_novo = st.number_input("Preço de Compra (R$):", min_value=0.0, step=0.01)

    if st.button("Adicionar Produto"):
        if not produto_novo or not id_anuncio_novo or not cd_novo or preco_compra_novo <= 0:
            st.error("⚠️ Preencha Produto, ID do anúncio, CD Mercado Livre e Preço de Compra.")
        else:
            novo = {
                "Produto": produto_novo,
                "ID do anúncio": id_anuncio_novo,
                "CD Mercado Livre": cd_novo,
                "Preço de Compra (R$)": preco_compra_novo,
                "Preço de Venda Atual (R$)": 0.0,
                "Rótulo": 0.0,
                "Embalagem (R$)": 0.0,
                "% Comissão Mercado Livre": 0.0,
                "% Marketing do anúncio": 0.0,
                "Frete Mercado Livre (R$)": 0.0,
                "Taxa Fixa Mercado Livre (R$)": 0.0,
                "Desconto em Taxas ML (R$)": 0.0,
                "Lucro/Prejuízo Real (R$)": 0.0,
                "% Margem de contribuição": 0.0
            }
            adicionar_produto(novo)
            st.success(f"Produto '{produto_novo}' adicionado com sucesso!")
            st.rerun()


def render_precificacao():
    st.header("📊 Precificação — Margens de Lucro Supramel")

    df = carregar_dados()
    if df.empty:
        st.warning("Nenhum dado encontrado no banco de dados.")
        return

    df_filtrado = render_filtros_precificacao(df)
    render_tabela_precificacao(df_filtrado)
    render_margens_cards(df)  # Exibe os dois cards SP e MG
    render_edicao_produto(df_filtrado)
