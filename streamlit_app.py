import streamlit as st
from datetime import datetime
from dashboard.sp_dashboard_vendas import render_sp
from dashboard.mg_dashboard_vendas import render_mg
from utils.utils_dashboard import carregar_json_para_df
import subprocess
import pandas as pd

st.set_page_config(page_title="Dashboard Vendas", layout="wide")

st.title("📊 Dashboard de Vendas — Mercado Livre")

# --- Botão para atualizar vendas ---
if st.button("🔄 Atualizar Vendas Agora"):
    with st.spinner("Buscando pedidos atualizados..."):
        try:
            subprocess.run(["python", "main.py"], check=True)
            st.success("✅ Vendas atualizadas com sucesso!")
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Erro ao atualizar vendas: {e}")

st.sidebar.header("Filtro Diário")
today = datetime.today().date()
start_date = st.sidebar.date_input("Data inicial", value=today)
end_date = st.sidebar.date_input("Data final", value=today)

st.markdown("---")

# --- Carrega dados SP e MG ---
df_sp = carregar_json_para_df("C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_sp.json")
df_mg = carregar_json_para_df("C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_mg.json")

def filtrar_periodo(df, start_date, end_date):
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    return df[(df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)]

df_sp_f = filtrar_periodo(df_sp, start_date, end_date)
df_mg_f = filtrar_periodo(df_mg, start_date, end_date)

# --- Calcula totais combinados ---
qt_total = int(df_sp_f["Quantidade"].sum() + df_mg_f["Quantidade"].sum())
vl_total = df_sp_f["Valor total"].sum() + df_mg_f["Valor total"].sum()

# --- Card resumo geral ---
st.markdown("## Resumo Geral")
col1, col2 = st.columns(2)
col1.metric("Total de Itens Vendidos (SP + MG)", qt_total)
col2.metric(
    "Faturamento Total (R$)",
    f"R$ {vl_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

st.markdown("---")

# --- Dashboard SP ---
st.subheader("Vendas São Paulo (SP)")
render_sp(start_date=start_date, end_date=end_date)

# --- Dashboard MG ---
st.subheader("Vendas Minas Gerais (MG)")
render_mg(start_date=start_date, end_date=end_date)
