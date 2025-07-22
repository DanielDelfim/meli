import streamlit as st
import subprocess
from dashboard.sp_dashboard_vendas import render_sp
from dashboard.mg_dashboard_vendas import render_mg

# A página de publicidade será carregada via pages/4_Publicidade.py

st.set_page_config(page_title="Dashboard Vendas", layout="wide")

st.title("📊 Dashboard — Mercado Livre")

# --- Botão para atualizar MG + SP ---
if st.button("🔄 Atualizar Vendas (MG + SP)"):
    with st.spinner("Atualizando vendas de MG e SP..."):
        try:
            result = subprocess.run(
                ["python", "main.py"],  # main.py já atualiza MG e SP
                check=True,
                capture_output=True,
                text=True
            )
            st.success("✅ Vendas atualizadas com sucesso!")
            st.text("Saída do script:\n" + result.stdout)
            if result.stderr:
                st.error("Erros detectados:\n" + result.stderr)
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Erro ao atualizar vendas:\n{e.stderr}")

st.markdown("---")
st.subheader("Selecione uma Sessão:")

# --- Menu principal ---
aba = st.radio(
    "Ir para:",
    [
        "São Paulo (SP)",
        "Minas Gerais (MG)",
        "Publicidade (Mercado Ads)"
    ]
)

# --- Renderização condicional ---
if aba == "São Paulo (SP)":
    render_sp()
elif aba == "Minas Gerais (MG)":
    render_mg()
else:
    st.write(
        "Acesse a página de Publicidade no menu lateral (pages/4_Publicidade.py) para visualizar campanhas e métricas."
    )
