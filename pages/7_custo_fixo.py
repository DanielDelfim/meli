import json
import os
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

CUSTOS_PATH = r"C:\\Users\\dmdel\\OneDrive\\Aplicativos\\Designer\\custos.json"

# Funções utilitárias
def carregar_custos():
    if not os.path.exists(CUSTOS_PATH) or os.path.getsize(CUSTOS_PATH) == 0:
        return []
    try:
        with open(CUSTOS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return [data]
            return data
    except json.JSONDecodeError:
        return []

def salvar_custos(custos):
    with open(CUSTOS_PATH, 'w', encoding='utf-8') as f:
        json.dump(custos, f, ensure_ascii=False, indent=2)

st.header("📊 Custos Fixos — Cadastro Mensal")

# Carregar custos existentes
custos = carregar_custos()

# Histórico de meses e tabela resumida
novo_mes = False
if custos:
    for c in custos:
        c["custo_total"] = sum(
            v for k, v in c.items()
            if isinstance(v, (int, float)) and k not in ["mes_competencia", "custo_total", "publicidade"]
        )
    df = pd.DataFrame(custos)
    st.subheader("Histórico de Custos")
    st.dataframe(df[["mes_competencia", "custo_total"]], use_container_width=True)
    opcoes = [c["mes_competencia"] for c in custos] + ["➕ Adicionar Novo Mês"]
    mes_sel = st.selectbox("Selecione um mês para editar ou adicionar:", opcoes)
    if mes_sel == "➕ Adicionar Novo Mês":
        novo_mes = True
        mes_competencia = st.text_input("Digite o novo mês (MM/AAAA):", datetime.today().strftime("%m/%Y"))
        dados_mes = {}
    else:
        mes_competencia = mes_sel
        dados_mes = next((c for c in custos if c["mes_competencia"] == mes_sel), {})
else:
    novo_mes = True
    mes_competencia = st.text_input("Digite o novo mês (MM/AAAA):", datetime.today().strftime("%m/%Y"))
    dados_mes = {}

# Lista inicial de campos fixos, mas que podem crescer dinamicamente
campos = list(dados_mes.keys()) if dados_mes else [
    "salario_janaine", "salario_ivanete", "salario_daniel", "decimo_terceiro",
    "tarifa_bb", "contador", "deposito_sp", "internet", "agua", "luz",
    "fgts", "inss", "tiny"
]

# Inputs para cada campo
valores = {}
cols = st.columns(3)
for i, campo in enumerate(campos):
    if campo not in ["mes_competencia", "custo_total", "publicidade"]:
        with cols[i % 3]:
            valores[campo] = st.number_input(
                campo.replace('_', ' ').capitalize() + " (R$):",
                value=float(dados_mes.get(campo, 0.0) if dados_mes else 0.0),
                step=0.01
            )

# Adicionar novo custo fixo
st.markdown("---")
st.subheader("➕ Adicionar Novo Custo Fixo")
col_novo1, col_novo2 = st.columns([2, 1])
novo_nome = col_novo1.text_input("Nome do Novo Custo:")
novo_valor = col_novo2.number_input("Valor (R$):", min_value=0.0, step=0.01)

if st.button("Adicionar Custo Fixo") and novo_nome:
    valores[novo_nome] = novo_valor
    st.experimental_rerun()

# Cálculo do custo total
custo_total = sum(valores.values())
st.metric("Custo Total Atual", f"R$ {custo_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

# Salvar custos fixos
if st.button("💾 Salvar Custos Fixos"):
    novo_registro = {"mes_competencia": mes_competencia}
    novo_registro.update(valores)
    novo_registro["custo_total"] = custo_total
    custos = [c for c in custos if c["mes_competencia"] != mes_competencia]
    custos.append(novo_registro)
    custos = sorted(custos, key=lambda x: datetime.strptime(x["mes_competencia"], "%m/%Y"))
    salvar_custos(custos)
    st.success("Custos fixos salvos com sucesso!")

# --- Nova seção: Publicidade Mercado Livre ---
st.markdown("---")
st.header("📢 Custo de Publicidade — Mercado Livre")

meses_publicidade = [c["mes_competencia"] for c in custos] + ["➕ Adicionar Novo"]
mes_pub_sel = st.selectbox("Selecione o mês de competência (Publicidade):", meses_publicidade, key="pub")

if mes_pub_sel == "➕ Adicionar Novo":
    mes_pub = st.text_input("Digite o novo mês (MM/AAAA):", datetime.today().strftime("%m/%Y"), key="pub_input")
    pub_dados = {}
else:
    mes_pub = mes_pub_sel
    pub_dados = next((c.get("publicidade", {}) for c in custos if c["mes_competencia"] == mes_pub_sel), {})

# Campos separados para SP e MG
col_pub_sp1, col_pub_sp2 = st.columns(2)
data_abertura_sp = col_pub_sp1.date_input("Data de Abertura SP:", value=pd.to_datetime(pub_dados.get("data_abertura_sp", datetime.today())))
data_fechamento_sp = col_pub_sp2.date_input("Data de Fechamento SP:", value=pd.to_datetime(pub_dados.get("data_fechamento_sp", datetime.today())))

col_pub_mg1, col_pub_mg2 = st.columns(2)
data_abertura_mg = col_pub_mg1.date_input("Data de Abertura MG:", value=pd.to_datetime(pub_dados.get("data_abertura_mg", datetime.today())))
data_fechamento_mg = col_pub_mg2.date_input("Data de Fechamento MG:", value=pd.to_datetime(pub_dados.get("data_fechamento_mg", datetime.today())))

valor_ads_sp = st.number_input("Valor Investido Ads MELI — São Paulo (R$):", value=float(pub_dados.get("valor_ads_sp", 0.0)), step=0.01)
valor_ads_mg = st.number_input("Valor Investido Ads MELI — Minas Gerais (R$):", value=float(pub_dados.get("valor_ads_mg", 0.0)), step=0.01)

valor_ads_total = valor_ads_sp + valor_ads_mg
st.metric("Total Ads MELI (SP + MG)", f"R$ {valor_ads_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

if st.button("💾 Salvar Publicidade"):
    for c in custos:
        if c["mes_competencia"] == mes_pub:
            c["publicidade"] = {
                "data_abertura_sp": str(data_abertura_sp),
                "data_fechamento_sp": str(data_fechamento_sp),
                "data_abertura_mg": str(data_abertura_mg),
                "data_fechamento_mg": str(data_fechamento_mg),
                "valor_ads_sp": valor_ads_sp,
                "valor_ads_mg": valor_ads_mg,
                "valor_ads_total": valor_ads_total
            }
            break
    else:
        custos.append({
            "mes_competencia": mes_pub,
            "publicidade": {
                "data_abertura_sp": str(data_abertura_sp),
                "data_fechamento_sp": str(data_fechamento_sp),
                "data_abertura_mg": str(data_abertura_mg),
                "data_fechamento_mg": str(data_fechamento_mg),
                "valor_ads_sp": valor_ads_sp,
                "valor_ads_mg": valor_ads_mg,
                "valor_ads_total": valor_ads_total
            }
        })
    salvar_custos(custos)
    st.success("Dados de publicidade salvos com sucesso!")