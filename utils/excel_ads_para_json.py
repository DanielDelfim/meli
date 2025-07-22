import pandas as pd
import json
import unicodedata

EXCEL_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_SP.xlsx"
EXCEL_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_MG.xlsx"
JSON_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_sp.json"
JSON_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_mg.json"

def normalizar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        return texto
    texto = texto.strip()
    texto = texto.replace("\n", "_")
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    texto = texto.lower().replace(" ", "_")
    return texto

def excel_para_json(excel_path: str, json_path: str):
    df = pd.read_excel(excel_path, skiprows=1)
    df.columns = [normalizar_texto(col) for col in df.columns]
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    print(f"✅ Convertido: {excel_path} → {json_path}")

if __name__ == "__main__":
    excel_para_json(EXCEL_SP, JSON_SP)
    excel_para_json(EXCEL_MG, JSON_MG)
