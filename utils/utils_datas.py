from datetime import datetime
from calendar import monthrange
import streamlit as st

def obter_data_inicio_fim_mes(mes_competencia: str):
    """
    Retorna as datas de início e fim do mês no formato date a partir de 'YYYY-MM'.
    """
    ano, mes = map(int, mes_competencia.split("-"))
    data_inicio = datetime(ano, mes, 1).date()
    data_fim = datetime(ano, mes, monthrange(ano, mes)[1]).date()
    return data_inicio, data_fim

def obter_lista_meses_existentes():
    """
    Retorna uma lista de meses existentes em formato 'YYYY-MM'.
    Pode ser adaptado para ler dinamicamente de custos.json, se desejar.
    """
    from utils.utils_custos import carregar_custos
    meses = [c["mes_competencia"] for c in carregar_custos()]
    return sorted(meses, reverse=True)

def selecionar_mes_competencia(meses_existentes: list, chave: str = "select_mes_competencia") -> str:
    """
    Centraliza a seleção do mês de competência em Streamlit.
    """
    opcao = st.selectbox(
        "📅 Mês de referência",
        options=["➕ Novo Mês"] + meses_existentes,
        index=0,
        key=chave  # <- chave agora é variável
    )

    if opcao == "➕ Novo Mês":
        return st.text_input("Digite o novo mês (YYYY-MM):", value=datetime.today().strftime("%Y-%m"), key=f"input_{chave}")
    return opcao
