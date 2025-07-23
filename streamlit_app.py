import streamlit as st
from datetime import datetime
from utils.utils_dashboard import carregar_json_para_df
import subprocess
import pandas as pd

st.set_page_config(page_title="Dashboard Vendas", layout="wide")

st.title("📊 Dashboard de Vendas — Mercado Livre")

st.markdown(
    """
    **Navegue pelas páginas no menu lateral:**
    - **Página 2:** Vendas SP  
    - **Página 3:** Vendas MG  
    - **Página 4:** Publicidade SP  
    - **Página 5:** Publicidade MG  
    """
)

import streamlit as st
import pandas as pd
from datetime import datetime
from utils.utils_dashboard import carregar_json_para_df

st.set_page_config(page_title="Dashboard Vendas", layout="wide")

st.title("📊 Dashboard de Vendas — Mercado Livre")

# --- Data de hoje como filtro padrão ---
today = datetime.today().date()
start_dt = pd.to_datetime(today)
end_dt = pd.to_datetime(today) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

# --- Carregar dados SP e MG ---
df_sp = carregar_json_para_df("C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_sp.json")
df_mg = carregar_json_para_df("C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_mg.json")

# --- Filtrar apenas a data de hoje ---
df_sp_f = df_sp[(df_sp["Data da venda"] >= start_dt) & (df_sp["Data da venda"] <= end_dt)]
df_mg_f = df_mg[(df_mg["Data da venda"] >= start_dt) & (df_mg["Data da venda"] <= end_dt)]

# --- Cards com faturamento ---
fat_sp = df_sp_f["Valor total"].sum()
fat_mg = df_mg_f["Valor total"].sum()
fat_total = fat_sp + fat_mg

st.markdown("## Faturamento Consolidado")
col1, col2, col3 = st.columns(3)
col1.metric("Faturamento SP (R$)", f"R$ {fat_sp:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("Faturamento MG (R$)", f"R$ {fat_mg:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Total (R$)", f"R$ {fat_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

st.markdown("---")

# --- Tabela de vendas SP ---
st.subheader(f"Vendas São Paulo (SP) — {today.strftime('%d/%m/%Y')}")
if df_sp_f.empty:
    st.warning("Nenhuma venda encontrada em SP hoje.")
else:
    df_sp_resumo = df_sp_f.groupby("Produto", as_index=False).agg({"Quantidade": "sum", "Valor total": "sum"})
    df_sp_resumo = df_sp_resumo.sort_values("Valor total", ascending=False)
    st.dataframe(df_sp_resumo, use_container_width=True)

st.markdown("---")

# --- Tabela de vendas MG ---
st.subheader(f"Vendas Minas Gerais (MG) — {today.strftime('%d/%m/%Y')}")
if df_mg_f.empty:
    st.warning("Nenhuma venda encontrada em MG hoje.")
else:
    df_mg_resumo = df_mg_f.groupby("Produto", as_index=False).agg({"Quantidade": "sum", "Valor total": "sum"})
    df_mg_resumo = df_mg_resumo.sort_values("Valor total", ascending=False)
    st.dataframe(df_mg_resumo, use_container_width=True)


# --- Botão para atualizar vendas ---
if st.button("🔄 Atualizar Vendas Agora"):
    with st.spinner("Buscando pedidos atualizados..."):
        try:
            subprocess.run(["python", "main.py"], check=True)
            st.success("✅ Vendas atualizadas com sucesso!")
        except subprocess.CalledProcessError as e:
            st.error(f"❌ Erro ao atualizar vendas: {e}")

st.sidebar.header("Filtro Diário")
today = datetime.today().date()
start_date = st.sidebar.date_input("Data inicial", value=today)
end_date = st.sidebar.date_input("Data final", value=today)

st.markdown("---")

# --- Carrega dados SP e MG ---
df_sp = carregar_json_para_df("C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_sp.json")
df_mg = carregar_json_para_df("C:/Users/dmdel/OneDrive/Aplicativos/Designer/backup_vendas_mg.json")

def filtrar_periodo(df, start_date, end_date):
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    return df[(df["Data da venda"] >= start_dt) & (df["Data da venda"] <= end_dt)]

df_sp_f = filtrar_periodo(df_sp, start_date, end_date)
df_mg_f = filtrar_periodo(df_mg, start_date, end_date)

# --- Calcula totais combinados ---
qt_total = int(df_sp_f["Quantidade"].sum() + df_mg_f["Quantidade"].sum())
vl_total = df_sp_f["Valor total"].sum() + df_mg_f["Valor total"].sum()

# --- Card resumo geral ---
st.markdown("## Resumo Geral")
col1, col2 = st.columns(2)
col1.metric("Total de Itens Vendidos (SP + MG)", qt_total)
col2.metric(
    "Faturamento Total (R$)",
    f"R$ {vl_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
)

st.markdown("---")