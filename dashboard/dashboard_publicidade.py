import streamlit as st
import pandas as pd
from pathlib import Path
from utils.utils_filtros import filtrar_vendas_json_por_periodo
from utils.utils_publicidade import carregar_ads_json

# Caminhos base
DESIGNER_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas")
PUBLICIDADE_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/publicidade")

# ---------------- CONFIGURAÇÕES DE REGIÃO ----------------
REGION_CONFIG = {
    "SP": {
        "display_name": "São Paulo (SP)",
        "vendas": "backup_vendas_sp_pp.json",
        "ads_7d": "ads_7d_sp.json",
        "ads_15d": "ads_15d_sp.json",
        "ads_30d": "ads_30d_sp.json",
    },
    "MG": {
        "display_name": "Minas Gerais (MG)",
        "vendas": "backup_vendas_mg_pp.json",
        "ads_7d": "ads_7d_mg.json",
        "ads_15d": "ads_15d_mg.json",
        "ads_30d": "ads_30d_mg.json",
    },
}

# ---------------- FUNÇÕES DE CARGA ----------------
def load_ads(path_ads: Path) -> pd.DataFrame:
    df = carregar_ads_json(str(path_ads))
    if not df.empty:
        for col in ["desde", "ate"]:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        df['codigo_do_anuncio'] = df['codigo_do_anuncio'].astype(str).str.strip()
    return df

# ---------------- FILTROS ----------------
def filtrar_ads(df: pd.DataFrame, campanha: str, titulo: str) -> pd.DataFrame:
    df = df.copy()
    if campanha != "Todas":
        df = df[df['campanha'] == campanha]
    if titulo != "Todos":
        df = df[df['titulo_do_anuncio_patrocinado'] == titulo]
    return df

def filtrar_vendas(df_ads: pd.DataFrame, df_vendas: pd.DataFrame) -> pd.DataFrame:
    if df_ads.empty or df_vendas.empty:
        return pd.DataFrame(columns=df_vendas.columns)

    codigos_filtrados = df_ads["codigo_do_anuncio"].dropna().astype(str).unique().tolist()
    df_vendas = df_vendas.copy()
    if "codigo_do_anuncio" not in df_vendas.columns:
        return pd.DataFrame()
    df_vendas["codigo_do_anuncio"] = df_vendas["codigo_do_anuncio"].astype(str)
    return df_vendas[df_vendas["codigo_do_anuncio"].isin(codigos_filtrados)]

# ---------------- INTERFACE ----------------
def render_publicidade(region_key: str):
    cfg = REGION_CONFIG[region_key]

    # Carregar dados de anúncios
    df_ads_7d  = load_ads(PUBLICIDADE_PATH / cfg["ads_7d"])
    df_ads_15d = load_ads(PUBLICIDADE_PATH / cfg["ads_15d"])
    df_ads_30d = load_ads(PUBLICIDADE_PATH / cfg["ads_30d"])

    # Determinar intervalo de datas mais amplo (ads 30 dias)
    df_geral_ads = pd.concat([df_ads_7d, df_ads_15d, df_ads_30d])
    min_date = df_geral_ads["desde"].min().date()
    max_date = df_geral_ads["ate"].max().date()

    # Carregar vendas já filtradas por período
    df_vendas_geral = filtrar_vendas_json_por_periodo(
        caminho_json=str(DESIGNER_PATH / cfg["vendas"]),
        data_inicio=min_date,
        data_fim=max_date,
        unidade=region_key
    )

    df_vendas_geral = df_vendas_geral.copy()
    if "codigo_do_anuncio" in df_vendas_geral.columns:
        df_vendas_geral["codigo_do_anuncio"] = df_vendas_geral["codigo_do_anuncio"].astype(str)

    # Filtros da interface
    st.header(f"📢 Publicidade — {cfg['display_name']}")
    campanhas = sorted(df_geral_ads["campanha"].dropna().unique())
    titulos   = sorted(df_geral_ads["titulo_do_anuncio_patrocinado"].dropna().unique())
    col1, col2 = st.columns(2)
    campanha = col1.selectbox("Campanha", ["Todas"] + campanhas)
    titulo   = col2.selectbox("Título do Anúncio", ["Todos"] + titulos)

    # Aplicar filtros nos anúncios
    df_ads7  = filtrar_ads(df_ads_7d, campanha, titulo)
    df_ads15 = filtrar_ads(df_ads_15d, campanha, titulo)
    df_ads30 = filtrar_ads(df_ads_30d, campanha, titulo)

    # Filtrar vendas por anúncio
    vendas7  = filtrar_vendas(df_ads7, df_vendas_geral)
    vendas15 = filtrar_vendas(df_ads15, df_vendas_geral)
    vendas30 = filtrar_vendas(df_ads30, df_vendas_geral)

    with st.expander("🔍 Vendas encontradas (30 dias)"):
        st.write("📅 Total (R$)", f"R$ {vendas30.get('Valor total', pd.Series(dtype=float)).sum():,.2f}")
        st.write("Registros:", len(vendas30))
        st.dataframe(vendas30)

    # Vendas fora da publicidade
    codigos_ads = df_geral_ads["codigo_do_anuncio"].dropna().astype(str).unique().tolist()
    df_skus_fora_ads = df_vendas_geral[~df_vendas_geral["codigo_do_anuncio"].isin(codigos_ads)]

    with st.expander("🔹 Vendas fora da Publicidade"):
        total_fora = df_skus_fora_ads.get("Valor total", pd.Series(dtype=float)).sum()
        st.write(f"💼 Total: R$ {total_fora:,.2f}")
        st.dataframe(df_skus_fora_ads)

        # Adicionar cards de métricas agregadas e projeções
        
    # Calcular métricas agregadas para cada período
    def calcular_metricas(df_ads, df_vendas):
        investimento = df_ads.get("investimento", pd.Series(dtype=float)).sum()
        vendas_total = df_vendas.get("Valor total", pd.Series(dtype=float)).sum()
        acos = (investimento / vendas_total * 100) if vendas_total > 0 else 0
        # TACoS: investimento sobre todas as vendas do período
        tacos = (investimento / df_vendas_geral.get("Valor total", pd.Series(dtype=float)).sum() * 100) if df_vendas_geral.get("Valor total", pd.Series(dtype=float)).sum() > 0 else 0
        return {
            "Investimento": investimento,
            "ACoS (%)": acos,
            "TACoS (%)": tacos
        }

    m7  = calcular_metricas(df_ads7, vendas7)
    m15 = calcular_metricas(df_ads15, vendas15)
    m30 = calcular_metricas(df_ads30, vendas30)

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

    st.subheader("📈 Projeções para 30 dias")
    p1, p2, _ = st.columns(3)
    p1.metric("Proj. Invest. (7d)", f"R$ {m7['Investimento'] / 7 * 30:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    p2.metric("Proj. Invest. (15d)", f"R$ {m15['Investimento'] / 15 * 30:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
