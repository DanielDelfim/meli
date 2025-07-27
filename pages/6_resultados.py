import pandas as pd
import streamlit as st
import json
import os
from datetime import date, datetime

# Caminhos de arquivos
RESULTADOS_JSON = r"C:\\Users\\dmdel\\OneDrive\\Aplicativos\\Designer\\resultados.json"
PREC_PATH = r"C:\Users\dmdel\OneDrive\Aplicativos\tokens\precificacao_meli.json"
VENDAS_SP = r"C:\\Users\\dmdel\\OneDrive\\Aplicativos\\Designer\\backup_vendas_sp.json"
VENDAS_MG = r"C:\\Users\\dmdel\\OneDrive\\Aplicativos\\Designer\\backup_vendas_mg.json"

# Estrutura padrão de resultados
VALORES_PADRAO = {
    "SP": {"investimento_ads": 0.0, "data_inicial": str(date.today()), "data_final": str(date.today())},
    "MG": {"investimento_ads": 0.0, "data_inicial": str(date.today()), "data_final": str(date.today())}
}

# Funções utilitárias
def salvar_json(dados):
    with open(RESULTADOS_JSON, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def garantir_json_valido():
    if not os.path.exists(RESULTADOS_JSON) or os.path.getsize(RESULTADOS_JSON) == 0:
        salvar_json(VALORES_PADRAO)
        return VALORES_PADRAO
    try:
        with open(RESULTADOS_JSON, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                salvar_json(VALORES_PADRAO)
                return VALORES_PADRAO
            return json.loads(content)
    except json.JSONDecodeError:
        salvar_json(VALORES_PADRAO)
        return VALORES_PADRAO

def carregar_vendas(caminho_json, data_inicial, data_final):
    if not os.path.exists(caminho_json):
        return 0.0
    try:
        with open(caminho_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        pagamentos = []
        if isinstance(data, list):
            for pedido in data:
                pagamentos.extend(pedido.get("payments", []))
        elif isinstance(data, dict):
            pagamentos = data.get("payments", [])
        total = 0.0
        for p in pagamentos:
            date_str = p.get("date_approved")
            if date_str and "total_paid_amount" in p:
                try:
                    data_pagamento = datetime.fromisoformat(date_str.replace("Z", "+00:00")).date()
                    if data_inicial <= data_pagamento <= data_final:
                        total += float(p["total_paid_amount"])
                except Exception:
                    continue
        return total
    except Exception as e:
        st.error(f"Erro ao carregar vendas: {e}")
        return 0.0

# Layout principal
st.title("Resultados de Ads")
dados = garantir_json_valido()

# ----------- Atualização de dados SP -----------
st.subheader("Atualizar Dados — São Paulo (SP)")
with st.form("form_sp"):
    investimento_sp = st.number_input("Investimento Ads SP (R$)", min_value=0.0, step=100.0, value=dados["SP"]["investimento_ads"])
    data_inicial_sp = st.date_input("Data Inicial SP", value=date.fromisoformat(dados["SP"]["data_inicial"]))
    data_final_sp = st.date_input("Data Final SP", value=date.fromisoformat(dados["SP"]["data_final"]))
    confirmar_sp = st.checkbox("Confirmar salvamento de SP")
    salvar_sp = st.form_submit_button("Salvar Dados SP")
    if salvar_sp and confirmar_sp:
        dados["SP"] = {"investimento_ads": investimento_sp, "data_inicial": str(data_inicial_sp), "data_final": str(data_final_sp)}
        salvar_json(dados)
        st.success("Dados de SP atualizados!")

# ----------- Atualização de dados MG -----------
st.subheader("Atualizar Dados — Minas Gerais (MG)")
with st.form("form_mg"):
    investimento_mg = st.number_input("Investimento Ads MG (R$)", min_value=0.0, step=100.0, value=dados["MG"]["investimento_ads"])
    data_inicial_mg = st.date_input("Data Inicial MG", value=date.fromisoformat(dados["MG"]["data_inicial"]))
    data_final_mg = st.date_input("Data Final MG", value=date.fromisoformat(dados["MG"]["data_final"]))
    confirmar_mg = st.checkbox("Confirmar salvamento de MG")
    salvar_mg = st.form_submit_button("Salvar Dados MG")
    if salvar_mg and confirmar_mg:
        dados["MG"] = {"investimento_ads": investimento_mg, "data_inicial": str(data_inicial_mg), "data_final": str(data_final_mg)}
        salvar_json(dados)
        st.success("Dados de MG atualizados!")

# ----------- Seção SP -----------
data_ini_sp = date.fromisoformat(dados["SP"]["data_inicial"])
data_fim_sp = date.fromisoformat(dados["SP"]["data_final"])
vendas_sp = carregar_vendas(VENDAS_SP, data_ini_sp, data_fim_sp)
tacos_sp = (dados["SP"]["investimento_ads"] / vendas_sp) * 100 if vendas_sp > 0 else 0

st.subheader(f"Resultados — São Paulo (SP) [{dados['SP']['data_inicial']} → {dados['SP']['data_final']}]")
col_sp1, col_sp2, col_sp3, col_sp4 = st.columns(4)
with col_sp1:
    st.metric("💰 Investimento Ads (SP)", f"R$ {dados['SP']['investimento_ads']:.2f}")
with col_sp2:
    st.metric("📦 Vendas no Período (SP)", f"R$ {vendas_sp:.2f}")
with col_sp3:
    st.metric("📊 TACOS (SP) (%)", f"{tacos_sp:.2f}%")
with col_sp4:
    st.metric("🛍️ Total de Vendas (SP)", f"R$ {vendas_sp:.2f}")

# ----------- Seção MG -----------
data_ini_mg = date.fromisoformat(dados["MG"]["data_inicial"])
data_fim_mg = date.fromisoformat(dados["MG"]["data_final"])
vendas_mg = carregar_vendas(VENDAS_MG, data_ini_mg, data_fim_mg)
tacos_mg = (dados["MG"]["investimento_ads"] / vendas_mg) * 100 if vendas_mg > 0 else 0

st.subheader(f"Resultados — Minas Gerais (MG) [{dados['MG']['data_inicial']} → {dados['MG']['data_final']}]")
col_mg1, col_mg2, col_mg3, col_mg4 = st.columns(4)
with col_mg1:
    st.metric("💰 Investimento Ads (MG)", f"R$ {dados['MG']['investimento_ads']:.2f}")
with col_mg2:
    st.metric("📦 Vendas no Período (MG)", f"R$ {vendas_mg:.2f}")
with col_mg3:
    st.metric("📊 TACOS (MG) (%)", f"{tacos_mg:.2f}%")
with col_mg4:
    st.metric("🛍️ Total de Vendas (MG)", f"R$ {vendas_mg:.2f}")

# ----------- Atualizar JSON de Precificação com TACOS -----------
st.markdown("### Precificação: aplicar TACOS no JSON")
if st.button("Aplicar TACOS aos produtos SP e MG"):
    try:
        with open(PREC_PATH, 'r', encoding='utf-8') as pf:
            prec_data = json.load(pf)
        for rec in prec_data:
            if rec.get("CD Mercado Livre") == "Araçariguama":
                rec['% Marketing do anúncio'] = round(tacos_sp / 100, 4)
            elif rec.get("CD Mercado Livre") == "Betim":
                rec['% Marketing do anúncio'] = round(tacos_mg / 100, 4)
        with open(PREC_PATH, 'w', encoding='utf-8') as pf:
            json.dump(prec_data, pf, ensure_ascii=False, indent=2)
        st.success("% Marketing do anúncio atualizado com TACOS para SP e MG no JSON de precificação.")
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado: {PREC_PATH}")
    except json.JSONDecodeError:
        st.error("Erro ao ler o JSON de precificação.")
    except Exception as e:
        st.error(f"Erro inesperado: {e}")