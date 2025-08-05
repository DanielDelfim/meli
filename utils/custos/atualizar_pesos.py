from utils.utils_filtros import filtrar_vendas_json_por_periodo
import pandas as pd
from pathlib import Path

CAMINHO_JSON_PRECIFICACAO = Path(r"C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao/precificacao_meli.json")
CAMINHO_VENDAS_SP = Path(r"C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas/backup_vendas_sp_pp.json")
CAMINHO_VENDAS_MG = Path(r"C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas/backup_vendas_mg_pp.json")

def calcular_pesos_por_estado(caminho_json, data_inicio, data_fim, unidade) -> tuple[dict, float]:
    df = filtrar_vendas_json_por_periodo(
        caminho_json=str(caminho_json),
        data_inicio=data_inicio,
        data_fim=data_fim,
        unidade=unidade
    )

    if df.empty:
        return {}, 0.0

    vendas_por_sku = df.groupby("SKU")["Valor total"].sum()
    total_vendas = vendas_por_sku.sum()
    pesos = (vendas_por_sku / total_vendas).to_dict()

    return pesos, total_vendas

def atualizar_pesos_em_precificacao():
    try:
        df_precificacao = pd.read_json(CAMINHO_JSON_PRECIFICACAO)

        # Definir intervalo fixo (julho/2025)
        data_inicio = pd.to_datetime("2025-07-01").date()
        data_fim = pd.to_datetime("2025-07-31").date()

        # Calcular pesos filtrando por unidade
        pesos_sp, _ = calcular_pesos_por_estado(CAMINHO_VENDAS_SP, data_inicio, data_fim, "SP")
        pesos_mg, _ = calcular_pesos_por_estado(CAMINHO_VENDAS_MG, data_inicio, data_fim, "MG")

        def obter_peso(sku, pesos_dict):
            return round(pesos_dict.get(sku, 0.0), 6)

        df_precificacao["peso_sp"] = df_precificacao["SKU"].apply(lambda sku: obter_peso(sku, pesos_sp))
        df_precificacao["peso_mg"] = df_precificacao["SKU"].apply(lambda sku: obter_peso(sku, pesos_mg))

        df_precificacao.to_json(CAMINHO_JSON_PRECIFICACAO, orient="records", indent=2, force_ascii=False)

    except Exception as e:
        raise RuntimeError(f"Erro ao atualizar pesos: {e}")
