import streamlit as st
from dashboard.dashboard_vendas import render_dashboard

st.set_page_config(page_title="Vendas MG", layout="wide")
render_dashboard("Minas Gerais (MG)", "C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_mg_pp.json")

