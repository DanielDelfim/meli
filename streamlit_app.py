import os
import subprocess
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from utils.utils_filtros import filtrar_vendas_json_por_periodo

# ---------------- CONFIGURAÇÕES ----------------
BASE_PATH = Path(__file__).resolve().parent
load_dotenv(BASE_PATH / ".env")

SCRIPTS_DIR = BASE_PATH / "scripts"
UPDATE_ONCE_SCR = SCRIPTS_DIR / "update_once.py"
PREPROCESS_SCR = SCRIPTS_DIR / "preprocess_dates.py"

JSON_SP = BASE_PATH / "tokens" / "vendas" / "backup_vendas_sp_pp.json"
JSON_MG = BASE_PATH / "tokens" / "vendas" / "backup_vendas_mg_pp.json"

# ---------------- FUNÇÃO DE ATUALIZAÇÃO ----------------
def atualizar_dados():
    try:
        with st.spinner("🔄 Atualizando dados, aguarde..."):
            subprocess.run(["python", str(UPDATE_ONCE_SCR)], check=True)
            subprocess.run(["python", str(PREPROCESS_SCR)], check=True)
        st.success("✅ Dados atualizados com sucesso!")
        st.cache_data.clear()
        st.rerun()
    except subprocess.CalledProcessError as e:
        st.error(f"❌ Erro ao atualizar dados: {e}")
    except Exception as e:
        st.error(f"❌ Erro inesperado: {e}")

# ---------------- LAYOUT ----------------
st.set_page_config(page_title="Dashboard de Vendas", layout="wide")
st.title("📊 Dashboard de Vendas — Mercado Livre")

if st.button("🔄 Atualizar Dados Agora", key="btn_atualizar"):
    atualizar_dados()

# ---------------- FILTRO DIÁRIO ----------------
st.sidebar.header("Filtro por Data")
today = date.today()
start_date = st.sidebar.date_input("Data inicial", value=today, key="start_date")
end_date = st.sidebar.date_input("Data final", value=today, key="end_date")

# ---------------- FILTRAR VENDAS ----------------
df_sp_periodo = filtrar_vendas_json_por_periodo(str(JSON_SP), start_date, end_date, unidade="SP")
df_mg_periodo = filtrar_vendas_json_por_periodo(str(JSON_MG), start_date, end_date, unidade="MG")

# ---------------- CARDS ----------------
fat_sp = df_sp_periodo.get("Valor total", pd.Series(dtype=float)).sum()
fat_mg = df_mg_periodo.get("Valor total", pd.Series(dtype=float)).sum()
fat_total = fat_sp + fat_mg
qt_itens = int(df_sp_periodo.get("Quantidade", pd.Series(dtype=float)).sum() + df_mg_periodo.get("Quantidade", pd.Series(dtype=float)).sum())
qt_pedidos = len(df_sp_periodo) + len(df_mg_periodo)

st.markdown(f"## Resumo de {start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Faturamento SP (R$)", f"R$ {fat_sp:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("Faturamento MG (R$)", f"R$ {fat_mg:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Total (R$)", f"R$ {fat_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric("Pedidos / Itens", f"{qt_pedidos} / {qt_itens}")
st.markdown("---")

# ---------------- TABELAS ----------------
st.subheader(f"Vendas São Paulo (SP) — {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}")
if df_sp_periodo.empty:
    st.info("Nenhuma venda encontrada em SP no período selecionado.")
else:
    df_sp_resumo = df_sp_periodo.groupby("Produto", as_index=False).agg({"Quantidade": "sum", "Valor total": "sum"})
    df_sp_resumo = df_sp_resumo.sort_values("Valor total", ascending=False)
    st.dataframe(df_sp_resumo, use_container_width=True)

st.markdown("---")
st.subheader(f"Vendas Minas Gerais (MG) — {start_date.strftime('%d/%m/%Y')} → {end_date.strftime('%d/%m/%Y')}")
if df_mg_periodo.empty:
    st.info("Nenhuma venda encontrada em MG no período selecionado.")
else:
    df_mg_resumo = df_mg_periodo.groupby("Produto", as_index=False).agg({"Quantidade": "sum", "Valor total": "sum"})
    df_mg_resumo = df_mg_resumo.sort_values("Valor total", ascending=False)
    st.dataframe(df_mg_resumo, use_container_width=True)
