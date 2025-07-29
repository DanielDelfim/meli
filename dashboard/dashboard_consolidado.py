import os
import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
from pathlib import Path
from utils.utils_dashboard import carregar_json_para_df

# Paths
BASE = Path(os.getenv("BASE_PATH", "C:/Users/dmdel/OneDrive/Aplicativos"))
CUSTOS_PATH = BASE / "Designer" / "custos.json"
JSON_SP_PP = BASE / "Designer" / "backup_vendas_sp_pp.json"
JSON_MG_PP = BASE / "Designer" / "backup_vendas_mg_pp.json"
PREC_PATH = BASE / "tokens" / "precificacao_meli.json"


def render_consolidado_financeiro():
    st.set_page_config(page_title="Consolidado Financeiro", layout="wide")
    st.title("8. Consolidado Financeiro (MCP Ponderado por Vendas)")

    # 1. Seleção do período
    df_custos = pd.read_json(CUSTOS_PATH)
    df_custos['period'] = pd.to_datetime(df_custos['mes_competencia'], format="%m/%Y").dt.to_period('M')
    periods = sorted(df_custos['period'].unique())
    labels = [p.strftime("%m/%Y") for p in periods]
    sel = st.selectbox("Mês de Competência", labels)
    period = periods[labels.index(sel)]
    start_date = period.start_time.date()
    end_date = period.end_time.date()

    # 2. Extrair custos e datas de publicidade
    record = df_custos[df_custos['period'] == period].iloc[0]
    custo_total = record.get('custo_total', 0)
    pub = record.get('publicidade', {})
    ads_sp = pub.get('valor_ads_sp', 0)
    ads_mg = pub.get('valor_ads_mg', 0)
    data_abertura_sp = pub.get('data_abertura_sp', '')
    data_fechamento_sp = pub.get('data_fechamento_sp', '')
    data_abertura_mg = pub.get('data_abertura_mg', '')
    data_fechamento_mg = pub.get('data_fechamento_mg', '')

    # 3. Carregar vendas pré-processadas
    df_sp = carregar_json_para_df(str(JSON_SP_PP))
    df_mg = carregar_json_para_df(str(JSON_MG_PP))
    df_sp['SKU'] = df_sp['SKU'].astype(str)
    df_mg['SKU'] = df_mg['SKU'].astype(str)
    df_sp['Data da venda'] = pd.to_datetime(df_sp['Data da venda']).dt.date
    df_mg['Data da venda'] = pd.to_datetime(df_mg['Data da venda']).dt.date

    # Filtrar vendas no mês
    df_sp_period = df_sp[(df_sp['Data da venda'] >= start_date) & (df_sp['Data da venda'] <= end_date)]
    df_mg_period = df_mg[(df_mg['Data da venda'] >= start_date) & (df_mg['Data da venda'] <= end_date)]

    # 4. Calcular MCP ponderado
    df_prec = pd.read_json(PREC_PATH)
    df_prec['SKU'] = df_prec['SKU'].astype(str)
    df_prec['% Margem'] = df_prec['% Margem de contribuição'].astype(float)

    sales_sp = df_sp_period.groupby('SKU', as_index=False)['Valor total'].sum().rename(columns={'Valor total': 'vendas'})
    sales_mg = df_mg_period.groupby('SKU', as_index=False)['Valor total'].sum().rename(columns={'Valor total': 'vendas'})

    prec_sp = df_prec[df_prec['CD Mercado Livre'] == 'Araçariguama'][['SKU', '% Margem']]
    prec_mg = df_prec[df_prec['CD Mercado Livre'] == 'Betim'][['SKU', '% Margem']]
    avg_marg_sp = prec_sp['% Margem'].mean() if not prec_sp.empty else 0.0
    avg_marg_mg = prec_mg['% Margem'].mean() if not prec_mg.empty else 0.0

    merged_sp = sales_sp.merge(prec_sp, on='SKU', how='left')
    merged_mg = sales_mg.merge(prec_mg, on='SKU', how='left')
    merged_sp['% Margem'].fillna(avg_marg_sp, inplace=True)
    merged_mg['% Margem'].fillna(avg_marg_mg, inplace=True)

    tot_rev_sp = merged_sp['vendas'].sum()
    tot_rev_mg = merged_mg['vendas'].sum()
    mcp_sp = (merged_sp['vendas'] * merged_sp['% Margem']).sum() / tot_rev_sp if tot_rev_sp > 0 else 0.0
    mcp_mg = (merged_mg['vendas'] * merged_mg['% Margem']).sum() / tot_rev_mg if tot_rev_mg > 0 else 0.0
    margin_sp = tot_rev_sp * mcp_sp
    margin_mg = tot_rev_mg * mcp_mg

    # 5. KPIs principais
    st.markdown("---")
    k1, k2, k3 = st.columns(3)
    k1.metric("Receita SP (R$)", f"R$ {tot_rev_sp:,.2f}")
    k2.metric("MCP SP (%)", f"{mcp_sp*100:.2f}%")
    k3.metric("Margem SP (R$)", f"R$ {margin_sp:,.2f}")
    k4, k5, k6 = st.columns(3)
    k4.metric("Receita MG (R$)", f"R$ {tot_rev_mg:,.2f}")
    k5.metric("MCP MG (%)", f"{mcp_mg*100:.2f}%")
    k6.metric("Margem MG (R$)", f"R$ {margin_mg:,.2f}")

    # 6. Custo, soma de margens e lucro/prejuízo
    st.markdown("---")
    f1, f2, f3 = st.columns(3)
    total_margin = margin_sp + margin_mg
    profit_loss = total_margin - custo_total
    f1.metric("Custo Total (R$)", f"R$ {custo_total:,.2f}")
    f2.metric("Total Margem (SP+MG) (R$)", f"R$ {total_margin:,.2f}")
    f3.metric("Lucro/Prejuízo (R$)", f"R$ {profit_loss:,.2f}")

    # 7. Publicidade com TACOS e confirmação
    st.markdown("---")
    # SP
    start_ads_sp = pd.to_datetime(data_abertura_sp).date() if data_abertura_sp else None
    end_ads_sp = pd.to_datetime(data_fechamento_sp).date() if data_fechamento_sp else None
    vendas_ads_sp = df_sp[(df_sp['Data da venda'] >= start_ads_sp) & (df_sp['Data da venda'] <= end_ads_sp)]['Valor total'].sum() if start_ads_sp and end_ads_sp else 0
    tacos_sp = ads_sp / vendas_ads_sp if vendas_ads_sp > 0 else 0.0
    st.markdown(f"### Publicidade SP <span style='font-size:12px;color:gray;'>{data_abertura_sp} – {data_fechamento_sp}</span>", unsafe_allow_html=True)
    sp_cols = st.columns(3)
    sp_cols[0].metric("Ads SP (R$)", f"R$ {ads_sp:,.2f}")
    sp_cols[1].metric("Vendas SP Período (R$)", f"R$ {vendas_ads_sp:,.2f}")
    sp_cols[2].metric("TACOS SP (%)", f"{tacos_sp*100:.2f}%")
    st.write("Confirmação necessária antes de atualizar marketing SP:")
    confirm_sp = st.checkbox("Confirmar atualização % Marketing SP")
    if confirm_sp and st.button("Atualizar % Marketing SP"):
        with open(PREC_PATH, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if item.get("CD Mercado Livre") == "Araçariguama":
                    item["% Marketing do anúncio"] = 0.0825
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()
        st.success("% Marketing SP atualizado para 8.25%")

    # MG
    start_ads_mg = pd.to_datetime(data_abertura_mg).date() if data_abertura_mg else None
    end_ads_mg = pd.to_datetime(data_fechamento_mg).date() if data_fechamento_mg else None
    vendas_ads_mg = df_mg[(df_mg['Data da venda'] >= start_ads_mg) & (df_mg['Data da venda'] <= end_ads_mg)]['Valor total'].sum() if start_ads_mg and end_ads_mg else 0
    tacos_mg = ads_mg / vendas_ads_mg if vendas_ads_mg > 0 else 0.0
    st.markdown(f"### Publicidade MG <span style='font-size:12px;color:gray;'>{data_abertura_mg} – {data_fechamento_mg}</span>", unsafe_allow_html=True)
    mg_cols = st.columns(3)
    mg_cols[0].metric("Ads MG (R$)", f"R$ {ads_mg:,.2f}")
    mg_cols[1].metric("Vendas MG Período (R$)", f"R$ {vendas_ads_mg:,.2f}")
    mg_cols[2].metric("TACOS MG (%)", f"{tacos_mg*100:.2f}%")
    st.write("Confirmação necessária antes de atualizar marketing MG:")
    confirm_mg = st.checkbox("Confirmar atualização % Marketing MG")
    if confirm_mg and st.button("Atualizar % Marketing MG"):
        with open(PREC_PATH, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                if item.get("CD Mercado Livre") == "Betim":
                    item["% Marketing do anúncio"] = 0.0825
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()
        st.success("% Marketing MG atualizado para 8.25%")

    # 8. Debug SKUs
    prod_map = df_prec[['SKU', 'Produto']].drop_duplicates().set_index('SKU')['Produto'].to_dict()
    missing_sp = sorted(set(prec_sp['SKU']) - set(sales_sp['SKU']))
    missing_mg = sorted(set(prec_mg['SKU']) - set(sales_mg['SKU']))
    missing_sp_df = pd.DataFrame({'SKU': missing_sp, 'Produto': [prod_map.get(s, '') for s in missing_sp]})
    missing_mg_df = pd.DataFrame({'SKU': missing_mg, 'Produto':[prod_map.get(s, '') for s in missing_mg]})
    no_margin_sp = sales_sp[~sales_sp['SKU'].isin(prec_sp['SKU'])].copy()
    no_margin_mg = sales_mg[~sales_mg['SKU'].isin(prec_mg['SKU'])].copy()
    no_margin_sp['Produto'] = no_margin_sp['SKU'].map(prod_map)
    no_margin_mg['Produto'] = no_margin_mg['SKU'].map(prod_map)

    st.markdown("---")
    st.subheader("SKUs com margem cadastrada sem vendas")
    st.table(missing_sp_df)
    st.table(missing_mg_df)

    st.markdown("---")
    st.subheader("SKUs em vendas sem margem cadastrada")
    st.table(no_margin_sp.rename(columns={'vendas':'Total Vendido'}))
    st.table(no_margin_mg.rename(columns={'vendas':'Total Vendido'}))


if __name__ == '__main__':
    render_consolidado_financeiro()
