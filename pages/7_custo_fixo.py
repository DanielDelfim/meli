import streamlit as st
from dashboard.dashboard_custos import render_custos_dashboard

st.set_page_config(
    page_title="Custos Fixos e Publicidade",
    layout="wide",
)

# Executa a interface principal
render_custos_dashboard()