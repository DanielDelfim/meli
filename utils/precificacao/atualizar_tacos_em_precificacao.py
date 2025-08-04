import json
from pathlib import Path
import pandas as pd

def atualizar_tacos_em_precificacao():
    caminho_custos = Path("C:/Users/dmdel/OneDrive/Aplicativos/Designer/custos.json")
    caminho_precificacao = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/precificacao_meli.json")

    # Carregar dados de custos
    with open(caminho_custos, encoding="utf-8") as f:
        dados_custos = json.load(f)

    if not isinstance(dados_custos, list):
        dados_custos = [dados_custos]

    # Criar cópias temporárias para extração de data
    dados_temp = []
    for item in dados_custos:
        item_temp = item.copy()
        try:
            item_temp["_data_obj"] = pd.to_datetime(item_temp["mes_competencia"], format="%m/%Y")
        except:
            item_temp["_data_obj"] = pd.Timestamp.min
        dados_temp.append(item_temp)

    # Selecionar o mês mais recente
    mais_recente = max(dados_temp, key=lambda x: x["_data_obj"])

    # Obter valores de TACoS
    publicidade = mais_recente.get("publicidade", {})
    tacos_sp = publicidade.get("tacos_sp", 0.0)
    tacos_mg = publicidade.get("tacos_mg", 0.0)

    # Carregar dados de precificação
    with open(caminho_precificacao, encoding="utf-8") as f:
        dados_precificacao = json.load(f)

    # Atualizar TACoS em produtos por CD
    for item in dados_precificacao:
        cd = item.get("CD Mercado Livre", "")
        if cd == "Araçariguama":
            item["% Marketing do anúncio"] = tacos_sp / 100.0
        elif cd == "Betim":
            item["% Marketing do anúncio"] = tacos_mg / 100.0

    # Salvar precificação atualizada
    with open(caminho_precificacao, "w", encoding="utf-8") as f:
        json.dump(dados_precificacao, f, indent=2, ensure_ascii=False)

    return tacos_sp, tacos_mg
