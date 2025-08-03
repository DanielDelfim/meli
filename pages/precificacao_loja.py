import streamlit as st
from dashboard.dashboard_precificacao_loja import render_precificacao_loja

st.set_page_config(page_title="Precificação Supramel", layout="wide")
render_precificacao_loja()
