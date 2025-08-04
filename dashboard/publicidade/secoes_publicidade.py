import streamlit as st
import pandas as pd
from utils.publicidade.metricas import calcular_metricas_publicidade, projetar_investimento

def aplicar_filtros_interface(df_geral_ads):
    campanhas = sorted(df_geral_ads["campanha"].dropna().unique())
    titulos = sorted(df_geral_ads["titulo_do_anuncio_patrocinado"].dropna().unique())
    col1, col2 = st.columns(2)
    campanha = col1.selectbox("Campanha", ["Todas"] + campanhas)
    titulo = col2.selectbox("Título do Anúncio", ["Todos"] + titulos)
    return campanha, titulo

def exibir_expander_vendas(vendas):
    with st.expander("🔍 Vendas encontradas (30 dias)"):
        total = vendas.get("Valor total", pd.Series(dtype=float)).sum()
        st.write("📅 Total (R$)", f"R$ {total:,.2f}")
        st.write("Registros:", len(vendas))
        st.dataframe(vendas)

def exibir_expander_fora_ads(df_vendas_geral, df_ads_geral):
    codigos_ads = df_ads_geral["codigo_do_anuncio"].dropna().astype(str).unique().tolist()
    df_fora = df_vendas_geral[~df_vendas_geral["codigo_do_anuncio"].isin(codigos_ads)]
    with st.expander("🔹 Vendas fora da Publicidade"):
        total = df_fora.get("Valor total", pd.Series(dtype=float)).sum()
        st.write(f"💼 Total: R$ {total:,.2f}")
        st.dataframe(df_fora)

def exibir_metricas_aggregadas(m7, m15, m30):
    st.subheader("📊 Métricas Agregadas")
    r1, r2, r3 = st.columns(3)
    r1.metric("ACoS 30 dias", f"{m30['ACoS (%)']:.2f}%")
    r2.metric("ACoS 15 dias", f"{m15['ACoS (%)']:.2f}%")
    r3.metric("ACoS 7 dias", f"{m7['ACoS (%)']:.2f}%")

    r4, r5, r6 = st.columns(3)
    r4.metric("TACoS 30 dias", f"{m30['TACoS (%)']:.2f}%")
    r5.metric("TACoS 15 dias", f"{m15['TACoS (%)']:.2f}%")
    r6.metric("TACoS 7 dias", f"{m7['TACoS (%)']:.2f}%")

    r7, r8, r9 = st.columns(3)
    r7.metric("Invest. 30 dias", f"R$ {m30['Investimento']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    r8.metric("Invest. 15 dias", f"R$ {m15['Investimento']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    r9.metric("Invest. 7 dias", f"R$ {m7['Investimento']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

def exibir_projecoes(m7, m15):
    st.subheader("📈 Projeções para 30 dias")
    p1, p2, _ = st.columns(3)
    p1.metric("Proj. Invest. (7d)", f"R$ {projetar_investimento(m7['Investimento'], 7):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    p2.metric("Proj. Invest. (15d)", f"R$ {projetar_investimento(m15['Investimento'], 15):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
