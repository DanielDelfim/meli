import streamlit as st
from datetime import datetime
from dashboard.sp_dashboard_vendas import render_sp
from dashboard.mg_dashboard_vendas import render_mg
import subprocess

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

# --- Dashboard SP ---
st.subheader("Vendas São Paulo (SP)")
render_sp(start_date=start_date, end_date=end_date)

# --- Dashboard MG ---
st.subheader("Vendas Minas Gerais (MG)")
render_mg(start_date=start_date, end_date=end_date)
