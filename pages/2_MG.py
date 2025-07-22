import streamlit as st
from dashboard.mg_dashboard_vendas import render_mg

st.set_page_config(page_title="MG", layout="wide")
render_mg()
