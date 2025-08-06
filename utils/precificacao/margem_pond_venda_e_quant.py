import pandas as pd
from pathlib import Path
from utils.precificacao.meli.precificacao_io import carregar_dados, salvar_dados
from utils.utils_filtros import filtrar_vendas_json_por_periodo, quantidade_vendida_por_sku

def calcular_mcp_ponderada_estado(df_prec: pd.DataFrame, df_vendas: pd.DataFrame, cd_nome: str) -> float:
    df_prec = df_prec[df_prec["CD Mercado Livre"] == cd_nome].copy()
    df_prec["SKU"] = df_prec["SKU"].astype(str)
    df_prec["Margem"] = pd.to_numeric(df_prec["% Margem de contribuição"], errors="coerce")
    df_prec["peso_quantidade"] = pd.to_numeric(df_prec["peso_quantidade_sp" if cd_nome == "Araçariguama" else "peso_quantidade_mg"], errors="coerce")
    df_prec["peso_venda"] = pd.to_numeric(df_prec["peso_sp" if cd_nome == "Araçariguama" else "peso_mg"], errors="coerce")

    df_prec["peso_combinado"] = df_prec["peso_quantidade"] * df_prec["peso_venda"]
    df_prec = df_prec[df_prec["peso_combinado"] > 0]

    df_prec["margem_ponderada"] = df_prec["Margem"] * df_prec["peso_combinado"]

    total_peso = df_prec["peso_combinado"].sum()
    total_margem = df_prec["margem_ponderada"].sum()

    if total_peso == 0:
        return 0.0

    return round(total_margem / total_peso, 4)


def atualizar_margens_ponderadas(
    caminho_json_precificacao: Path,
    caminho_vendas_sp: Path,
    caminho_vendas_mg: Path,
    data_inicio,
    data_fim
):
    df_prec = carregar_dados()

    # Calcula para SP
    mcp_sp = calcular_mcp_ponderada_estado(df_prec, None, "Araçariguama")
    mcp_mg = calcular_mcp_ponderada_estado(df_prec, None, "Betim")

    # Armazena os valores em todas as linhas do JSON (para leitura simples)
    df_prec["mcp_ponderada_sp"] = mcp_sp
    df_prec["mcp_ponderada_mg"] = mcp_mg

    salvar_dados(df_prec)
