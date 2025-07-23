import streamlit as st
from dashboard.dashboard_vendas import render_dashboard

st.set_page_config(page_title="Vendas SP", layout="wide")
render_dashboard("São Paulo (SP)", "C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_sp.json")
