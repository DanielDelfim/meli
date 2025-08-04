from pathlib import Path

DESIGNER_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/vendas")
PUBLICIDADE_PATH = Path("C:/Users/dmdel/OneDrive/Aplicativos/tokens/publicidade")

REGION_CONFIG = {
    "SP": {
        "display_name": "São Paulo (SP)",
        "vendas": "backup_vendas_sp_pp.json",
        "ads_7d": "ads_7d_sp.json",
        "ads_15d": "ads_15d_sp.json",
        "ads_30d": "ads_30d_sp.json",
        "ads_mes": "ads_mes_sp.json"  # ✅ Adicionado aqui
    },
    "MG": {
        "display_name": "Minas Gerais (MG)",
        "vendas": "backup_vendas_mg_pp.json",
        "ads_7d": "ads_7d_mg.json",
        "ads_15d": "ads_15d_mg.json",
        "ads_30d": "ads_30d_mg.json",
        "ads_mes": "ads_mes_mg.json"  # ✅ Adicionado aqui
    },
}
