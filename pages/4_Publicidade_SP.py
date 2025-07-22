import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from dashboard.sp_dashboard_publicidade import render_sp_publicidade
import subprocess

st.set_page_config(page_title="Publicidade SP", layout="wide")

st.title("📢 Publicidade — São Paulo (SP)")

if st.button("🔄 Atualizar Publicidade SP"):
    with st.spinner("Atualizando dados de publicidade SP..."):
        try:
            subprocess.run(["python", "atualizar_jsons_ads.py"], check=True)
            st.success("✅ Publicidade SP atualizada com sucesso!")
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Erro ao atualizar publicidade SP: {e}")

st.markdown("---")
render_sp_publicidade()
