import streamlit as st
import pandas as pd
from datetime import datetime
from utils.utils_custos import (
    carregar_custos,
    obter_mes,
    atualizar_custo_mes,
    adicionar_novo_custo_a_todos_os_meses
)

def render_aba_custos_fixos():
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
    opcao_mes = st.selectbox("Selecione o mês de competência:", ["➕ Novo Mês"] + meses_existentes, key="selectbox_fixos")

    if opcao_mes == "➕ Novo Mês":
        mes = st.text_input("Digite o mês (YYYY-MM):", datetime.today().strftime("%Y-%m"), key="input_fixos")
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
                        key=f"val_fixos_{campo}"
                    )
                else:
                    valores[campo] = float(dados.get(campo, 0.0))
                    st.markdown(f"**{campo.replace('_', ' ').capitalize()}:** R$ {valores[campo]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.markdown("---")
    st.subheader("Adicionar Novo Custo Fixo a Todos os Meses")
    col_novo1, col_novo2 = st.columns([2, 1])
    novo_nome = col_novo1.text_input("Nome do Novo Custo:")
    novo_valor = col_novo2.number_input("Valor Inicial (R$):", min_value=0.0, step=0.01)

    if st.button("➕ Adicionar Custo Fixo Global"):
        if novo_nome:
            adicionar_novo_custo_a_todos_os_meses(novo_nome, novo_valor)
            st.success(f"Custo '{novo_nome}' adicionado a todos os meses.")
            st.rerun()

    if editar and st.button("📂 Salvar Todos os Dados do Mês"):
        try:
            datetime.strptime(mes, "%Y-%m")
        except ValueError:
            st.error("⚠️ Mês de competência inválido. Use o formato 'YYYY-MM'.")
            st.stop()

        atualizar_custo_mes(mes, valores)
        st.success("Custos salvos com sucesso!")
        st.rerun()
