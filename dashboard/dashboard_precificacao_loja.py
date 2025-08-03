import streamlit as st
import pandas as pd
from utils.precificacao.loja.precificacao_calc_loja import calcular_preco_venda
from utils.precificacao.loja.precificacao_io_loja import carregar_dados, salvar_dados

CAMPOS_EDITAVEIS = [
    "Preço de Compra (R$)",
    "Frete R$",
    "Rótulo R$",
    "Embalagem (R$)",
    "% Comissão Representante",
    "% Imposto Simples Nacional",
    "% Margem de contribuição"
]

def render_tabela_precificacao(df):
    # Converte valores para float, tratando vazios
    df["Preço de Compra (R$)"] = pd.to_numeric(df["Preço de Compra (R$)"], errors="coerce").fillna(0)
    df["Frete de Compra (R$)"] = df["Preço de Compra (R$)"] * 0.08

    colunas_exibir = [
        c for c in ["Produto", "Preço de Venda", "Preço de Compra (R$)", "Frete de Compra (R$)", "% Margem de contribuição"]
        if c in df.columns
    ]
    df_exibir = df[colunas_exibir].copy()

    def formatar_moeda(x):
        try:
            valor = float(x)
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "R$ 0,00"

    def formatar_percentual(x):
        try:
            valor = float(x) * 100
            return f"{valor:.2f}%"
        except (ValueError, TypeError):
            return "0,00%"

    for col in ["Preço de Venda", "Preço de Compra (R$)", "Frete de Compra (R$)"]:
        if col in df_exibir.columns:
            df_exibir[col] = df_exibir[col].apply(formatar_moeda)

    if "% Margem de contribuição" in df_exibir.columns:
        df_exibir["% Margem de contribuição"] = df_exibir["% Margem de contribuição"].apply(formatar_percentual)

    st.dataframe(df_exibir, use_container_width=True)

def render_edicao_produto(df):
    if df.empty:
        st.info("Nenhum produto disponível para edição.")
        return

    produtos_lista = df["Produto"].tolist()
    produto_sel = st.selectbox("Selecione um produto para editar:", produtos_lista, key="select_produto")

    produto_df = df[df["Produto"] == produto_sel].copy()
    dados_base = produto_df.iloc[0].to_dict()

    st.subheader(f"Edição — {produto_sel}")
    edits = {}
    cols = st.columns(3)

    for i, campo in enumerate(CAMPOS_EDITAVEIS):
        val = dados_base.get(campo, 0)
        col_st = cols[i % 3]
        if "%" in campo:
            percentage_val = float(val or 0) * 100
            novo_val = col_st.number_input(campo, value=percentage_val, step=0.01, key=f"{campo}_{produto_sel}") / 100
        else:
            numeric_val = float(val or 0)
            novo_val = col_st.number_input(campo, value=numeric_val, step=0.01, key=f"{campo}_{produto_sel}")
        edits[campo] = novo_val

    # Cálculo do novo preço de venda
    dados_calc = dados_base.copy()
    dados_calc.update(edits)
    preco_venda = calcular_preco_venda(dados_calc)
    frete_compra = dados_calc.get("Frete de Compra (R$)", 0)

    st.metric("Preço de Venda Sugerido", f"R$ {preco_venda:.2f}")
    st.metric("Frete de Compra (8%)", f"R$ {frete_compra:.2f}")

    # Botão salvar
    if st.button("💾 Salvar Alterações", key=f"save_{produto_sel}"):
        dados_novos = dados_base.copy()
        dados_novos.update(edits)
        dados_novos["Preço de Venda"] = preco_venda
        dados_novos["Frete de Compra (R$)"] = frete_compra

        df.loc[df["Produto"] == produto_sel, dados_novos.keys()] = dados_novos.values()
        salvar_dados(df.to_dict(orient="records"))
        st.success("Alterações salvas com sucesso!")
        st.rerun()

def render_precificacao_loja():
    st.header("📊 Precificação — Loja Supramel")

    dados = carregar_dados()
    df = pd.DataFrame(dados)

    if df.empty:
        st.warning("Nenhum dado encontrado no arquivo de precificação.")
        return

    render_tabela_precificacao(df)
    st.markdown("---")
    render_edicao_produto(df)

if __name__ == "__main__":
    render_precificacao_loja()
