import pandas as pd
from pathlib import Path
from utils.precificacao.meli.precificacao_io import carregar_dados, salvar_dados
from utils.utils_filtros import filtrar_vendas_json_por_periodo, quantidade_vendida_por_sku

def calcular_peso_quantidade(caminho_vendas: Path, data_inicio, data_fim, cd_nome: str, coluna_destino: str):
    df_vendas = filtrar_vendas_json_por_periodo(str(caminho_vendas), data_inicio, data_fim)
    df_qtd = quantidade_vendida_por_sku(df_vendas)

    qtd_total = df_qtd["Qtd Vendida"].sum()
    if qtd_total == 0:
        return {}

    df_qtd["peso_quantidade"] = df_qtd["Qtd Vendida"] / qtd_total
    return dict(zip(df_qtd["SKU"], df_qtd["peso_quantidade"]))

def atualizar_json_com_peso_quantidade(path_json: Path, pesos_sp: dict, pesos_mg: dict):
    df = carregar_dados()

    def atualizar_valor(row):
        sku = str(row["SKU"])
        cd = row["CD Mercado Livre"]

        if cd == "Araçariguama":
            for chave, peso in pesos_sp.items():
                if str(sku).startswith(str(chave)):
                    return round(peso, 6)
        elif cd == "Betim":
            for chave, peso in pesos_mg.items():
                if str(sku).startswith(str(chave)):
                    return round(peso, 6)
        return row.get("peso_quantidade_sp") if cd == "Araçariguama" else row.get("peso_quantidade_mg")

    df["peso_quantidade_sp"] = df.apply(lambda row: atualizar_valor(row) if row["CD Mercado Livre"] == "Araçariguama" else row.get("peso_quantidade_sp"), axis=1)
    df["peso_quantidade_mg"] = df.apply(lambda row: atualizar_valor(row) if row["CD Mercado Livre"] == "Betim" else row.get("peso_quantidade_mg"), axis=1)

    salvar_dados(df)
