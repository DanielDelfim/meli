import os
import subprocess
import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from utils.utils_dashboard import carregar_json_para_df

# ---------------- CONFIGURAÇÕES ----------------
BASE_PATH = Path(__file__).resolve().parent
load_dotenv(BASE_PATH / ".env")

SCRIPTS_DIR = BASE_PATH / "scripts"
UPDATE_ONCE_SCR = SCRIPTS_DIR / "update_once.py"
PREPROCESS_SCR = SCRIPTS_DIR / "preprocess_dates.py"

JSON_SP_PP = BASE_PATH / "Designer" / "backup_vendas_sp_pp.json"
JSON_MG_PP = BASE_PATH / "Designer" / "backup_vendas_mg_pp.json"

# ---------------- FUNÇÕES AUXILIARES ----------------
@st.cache_data
def carregar_dados():
    """Carrega os arquivos pré-processados com as datas normalizadas."""
    df_sp = carregar_json_para_df(JSON_SP_PP) if JSON_SP_PP.exists() else pd.DataFrame()
    df_mg = carregar_json_para_df(JSON_MG_PP) if JSON_MG_PP.exists() else pd.DataFrame()

    if not df_sp.empty and "Data da venda" in df_sp.columns:
        df_sp["Data da venda"] = pd.to_datetime(df_sp["Data da venda"], format="%Y-%m-%d")
    if not df_mg.empty and "Data da venda" in df_mg.columns:
        df_mg["Data da venda"] = pd.to_datetime(df_mg["Data da venda"], format="%Y-%m-%d")

    return df_sp, df_mg


def filtrar_periodo(df, inicio, fim):
    """Filtra vendas no intervalo [inicio, fim]."""
    if df.empty:
        return df
    return df[(df["Data da venda"] >= inicio) & (df["Data da venda"] <= fim)]


def atualizar_dados():
    """Executa update_once.py e preprocess_dates.py."""
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

# Botão de atualização
if st.button("🔄 Atualizar Dados Agora", key="btn_atualizar"):
    atualizar_dados()

# Carrega dados
df_sp, df_mg = carregar_dados()
if df_sp.empty and df_mg.empty:
    st.warning("⚠️ Nenhum dado encontrado. Clique em 'Atualizar Dados Agora'.")
    st.stop()

# ---------------- FILTRO LATERAL (DIÁRIO) ----------------
st.sidebar.header("Filtro por Período")
today = datetime.now().date()

start_date = st.sidebar.date_input("Data inicial", value=today, key="start_date")
end_date = st.sidebar.date_input("Data final", value=today, key="end_date")

start_dt = pd.to_datetime(f"{start_date}")
end_dt = pd.to_datetime(f"{end_date}")

# Filtra dados
df_sp_periodo = filtrar_periodo(df_sp, start_dt, end_dt)
df_mg_periodo = filtrar_periodo(df_mg, start_dt, end_dt)

# ---------------- CARDS DE FATURAMENTO ----------------
fat_sp = df_sp_periodo["Valor total"].sum() if not df_sp_periodo.empty else 0
fat_mg = df_mg_periodo["Valor total"].sum() if not df_mg_periodo.empty else 0
fat_total = fat_sp + fat_mg

qt_itens = int(df_sp_periodo["Quantidade"].sum() + df_mg_periodo["Quantidade"].sum())
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
