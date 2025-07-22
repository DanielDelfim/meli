import streamlit as st
from dashboard.precificacao_dashboard import render_precificacao

st.set_page_config(page_title="Precificação Supramel", layout="wide")
render_precificacao()
