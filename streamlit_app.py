import streamlit as st
from utils.utils_dashboard import render_dashboard
from datetime import datetime

st.set_page_config(page_title="Dashboard Vendas", layout="wide")

st.title("📊 Dashboard Consolidado — Mercado Livre")

# --- Botão para atualizar vendas ---
if st.button("🔄 Atualizar Vendas Agora"):
    with st.spinner("Buscando pedidos atualizados..."):
        import subprocess
        try:
            subprocess.run(["python", "main.py"], check=True)
            st.success("✅ Vendas atualizadas com sucesso!")
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Erro ao atualizar vendas: {e}")

st.sidebar.header("📅 Filtro Diário — Período Personalizado")
today = datetime.today().date()
start_date = st.sidebar.date_input("Data inicial", value=today)
end_date = st.sidebar.date_input("Data final", value=today)

st.markdown("---")

# --- Tabela de São Paulo ---
st.subheader("Vendas - São Paulo (SP)")
render_dashboard("São Paulo (SP)", "C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_sp.json",
                 start_date, end_date)

st.markdown("---")

# --- Tabela de Minas Gerais ---
st.subheader("Vendas - Minas Gerais (MG)")
render_dashboard("Minas Gerais (MG)", "C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_mg.json",
                 start_date, end_date)
