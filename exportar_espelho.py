import pandas as pd
import json

EXCEL_PATH = "C:/Users/dmdel/OneDrive/Aplicativos/Planilha_Precificacao_Supramel_MargemLiquida.xlsx"
JSON_PATH = "C:/Users/dmdel/OneDrive/Aplicativos/precificacao_meli.json"

def exportar_meli_para_json():
    print("🔄 Lendo aba MELI do Excel...")
    df = pd.read_excel(EXCEL_PATH, sheet_name="MELI", skiprows=1)
    df = df.fillna("")  # Substitui valores NaN por vazio

    print(f"💾 Exportando {len(df)} registros para JSON...")
    df.to_json(JSON_PATH, orient="records", force_ascii=False, indent=2)

    print(f"✅ Arquivo gerado com sucesso: {JSON_PATH}")

if __name__ == "__main__":
    exportar_meli_para_json()
