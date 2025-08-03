import streamlit as st
import pandas as pd

from utils.precificacao.meli.precificacao_calc import calcular_margens
from utils.precificacao.meli.precificacao_io import (
    carregar_dados,
    salvar_alteracoes_json,
    deletar_produto,
    adicionar_produto,
)

# Colunas editáveis para precificação
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

# --------- Filtrar e mostrar tabela ---------
def render_filtros_precificacao(df):
    if "CD Mercado Livre" in df.columns:
        cds = sorted(df["CD Mercado Livre"].dropna().unique())
        escolha = st.sidebar.selectbox("CD Mercado Livre", ["Todos"] + cds, key="filtro_cd")
        if escolha != "Todos":
            df = df[df["CD Mercado Livre"] == escolha]
    termo = st.sidebar.text_input("Buscar produto", key="filtro_produto")
    if termo:
        df = df[df["Produto"].str.contains(termo, case=False, na=False)]
    return df

# --------- Exibir tabela resumida ---------
def render_tabela(df):
    cols = [
        "ID", 
        "Produto", 
        "% Marketing do anúncio",
        "Lucro/Prejuízo Real (R$)", 
        "% Margem de contribuição"
    ]
    disponiveis = [c for c in cols if c in df.columns]
    df_mostra = df[disponiveis].rename(columns={
        "Lucro/Prejuízo Real (R$)": "Lucro (R$)",
        "% Margem de contribuição": "Margem (%)",
        "% Marketing do anúncio": "Marketing (%)"
    })

    # Marketing e Margem estão em fração — aplicar * 100
    if "Marketing (%)" in df_mostra.columns:
        df_mostra["Marketing (%)"] = df_mostra["Marketing (%)"].apply(lambda x: f"{x * 100:.1f}%")

    if "Margem (%)" in df_mostra.columns:
        df_mostra["Margem (%)"] = df_mostra["Margem (%)"].apply(lambda x: f"{x * 100:.1f}%")

    st.dataframe(df_mostra, use_container_width=True)

# --------- Edição e recalculo dinâmico ---------
def render_edicao(df):
    if df.empty:
        st.info("Nenhum registro para editar.")
        return

    itens = [f"{row['Produto']} (ID {row['ID']})" for _, row in df.iterrows()]
    escolha = st.selectbox("Produto:", itens, key="sel_item")
    id_sel = int(escolha.split("ID ")[1].rstrip(")"))
    linha = df[df["ID"] == id_sel].iloc[0]
    base = linha.to_dict()

    st.subheader(f"Editar — {linha['Produto']}")
    inputs = {}
    cols = st.columns(2)
    for campo in CAMPOS_EDITAVEIS:
        cont = cols[0] if CAMPOS_EDITAVEIS.index(campo) % 2 == 0 else cols[1]
        if campo == "ID do anúncio":
            # campo texto
            val0 = base.get(campo, "")
            novo = cont.text_input(campo, value=str(val0), key=f"in_{campo}")
            inputs[campo] = novo
        elif "%" in campo:
            # percentual: exibe 0-100
            val0 = base.get(campo) or 0.0
            raw = cont.number_input(campo, value=float(val0) * 100, step=0.1, key=f"in_{campo}")
            inputs[campo] = raw / 100.0
        else:
            # valor numérico
            val0 = base.get(campo) or 0.0
            novo = cont.number_input(campo, value=float(val0), step=0.01, key=f"in_{campo}")
            inputs[campo] = novo

    frete_cd, imposto, _, lucro, margem = calcular_margens(inputs, json_base=base)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Frete até CD (R$)", f"R$ {frete_cd:.2f}")
    m2.metric("Imposto",           f"R$ {imposto:.2f}")
    m3.metric("Lucro (R$)",        f"R$ {lucro:.2f}")
    m4.metric("Margem (%)",        f"{margem:.2f}%")

    st.markdown("---")
    if st.button("Salvar", key="btn_save"):
        if salvar_alteracoes_json(id_sel, inputs):
            st.success("Salvo com sucesso.")
            st.experimental_rerun()
    if st.button("Deletar", key="btn_del"):
        deletar_produto(id_sel)
        st.warning("Deletado.")
        st.experimental_rerun()

# --------- Adicionar novo ---------
def render_adicao():
    st.subheader("Adicionar Produto")
    novo = {}
    novo['Produto'] = st.text_input("Produto", key="add_prod")
    for campo in CAMPOS_EDITAVEIS:
        if campo == "ID do anúncio":
            novo[campo] = st.text_input(campo, key=f"add_{campo}")
        elif "%" in campo:
            raw = st.number_input(campo, value=0.0, step=0.1, key=f"add_{campo}")
            novo[campo] = raw / 100.0
        else:
            novo[campo] = st.number_input(campo, value=0.0, step=0.01, key=f"add_{campo}")
    if st.button("Adicionar Produto", key="btn_add"):
        adicionar_produto(novo)
        st.success("Produto adicionado.")
        st.experimental_rerun()

# --------- RENDER PRINCIPAL ---------
def render_precificacao():
    st.title("Precificação Supramel")
    df = carregar_dados()
    df = render_filtros_precificacao(df)
    render_tabela(df)
    render_edicao(df)
    render_adicao()
