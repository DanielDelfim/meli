import streamlit as st
from dashboard.custos.abas.aba_custos_fixos import render_aba_custos_fixos
from dashboard.custos.abas.aba_publicidade import render_aba_publicidade
from dashboard.custos.abas.aba_atualizacoes import render_aba_atualizacoes

def render_custos_dashboard():
    st.set_page_config("Custos Fixos e Publicidade", layout="wide")
    st.title("💰 Controle de Custos Fixos e Publicidade")

    tabs = st.tabs(["📦 Custos Fixos", "📢 Publicidade Mercado Livre", "🔄 Atualizações"])

    with tabs[0]:
        render_aba_custos_fixos()

    with tabs[1]:
        render_aba_publicidade()

    with tabs[2]:
        render_aba_atualizacoes()