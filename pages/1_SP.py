import streamlit as st
from dashboard.sp_dashboard_vendas import render_sp

st.set_page_config(page_title="SP", layout="wide")
render_sp()
