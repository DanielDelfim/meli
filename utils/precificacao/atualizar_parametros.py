import json
import re
from datetime import datetime
from pathlib import Path

# Caminhos
CAMINHO_CUSTOS = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/custos.json")
CAMINHO_PARAMETROS = Path("C:/Users/dmdel/OneDrive/Aplicativos/utils/precificacao/precificacao_parametros.py")

def atualizar_parametros():
    if not CAMINHO_CUSTOS.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {CAMINHO_CUSTOS}")

    with open(CAMINHO_CUSTOS, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # Filtra somente registros com mes_competencia no formato YYYY-MM
    dados_validos = [
        d for d in dados
        if "mes_competencia" in d
        and isinstance(d["mes_competencia"], str)
        and len(d["mes_competencia"]) == 7
        and "/" not in d["mes_competencia"]
    ]

    if not dados_validos:
        raise ValueError("Nenhuma entrada válida com 'mes_competencia' encontrada.")

    # Encontra o mais recente
    dados_ordenados = sorted(dados_validos, key=lambda x: datetime.strptime(x["mes_competencia"], "%Y-%m"), reverse=True)
    entrada_recente = dados_ordenados[0]

    publicidade = entrada_recente.get("publicidade", {})
    tacos_sp = publicidade.get("tacos_sp") / 100
    tacos_mg = publicidade.get("tacos_mg") / 100

    if tacos_sp is None or tacos_mg is None:
        raise ValueError("Valores de TACoS SP/MG não encontrados na entrada mais recente.")

    # Atualiza o arquivo de parâmetros
    with open(CAMINHO_PARAMETROS, "r", encoding="utf-8") as f:
        conteudo = f.read()

    # Usa lambda no re.sub para evitar erro de group reference
    conteudo = re.sub(
        r'(\"Araçariguama\".+?% Marketing do anúncio\":\s*)([\d.]+)',
        lambda m: f"{m.group(1)}{tacos_sp}",
        conteudo,
        flags=re.DOTALL
    )

    conteudo = re.sub(
        r'(\"Betim\".+?% Marketing do anúncio\":\s*)([\d.]+)',
        lambda m: f"{m.group(1)}{tacos_mg}",
        conteudo,
        flags=re.DOTALL
    )

    with open(CAMINHO_PARAMETROS, "w", encoding="utf-8") as f:
        f.write(conteudo)