import pandas as pd
import unicodedata
import os

# Caminhos dos arquivos Excel
EXCEL_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_SP.xlsx"
EXCEL_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_MG.xlsx"
EXCEL_MES_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_mes_total_SP.xlsx"
EXCEL_MES_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_mes_total_MG.xlsx"

# Caminhos dos arquivos JSON de saída
JSON_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_sp.json"
JSON_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_mg.json"
JSON_MES_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_mes_sp.json"
JSON_MES_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Designer\ads_mes_mg.json"

def normalizar_texto(texto: str) -> str:
    """Remove acentos, espaços extras, quebra de linha e converte para minúsculo com underscores."""
    if not isinstance(texto, str):
        return texto
    texto = texto.strip()
    texto = texto.replace("\n", "_")
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    texto = texto.lower().replace(" ", "_")
    return texto

def excel_para_json(excel_path: str, json_path: str):
    if not os.path.exists(excel_path):
        print(f"❌ Arquivo não encontrado: {excel_path}")
        return

    print(f"🔄 Lendo Excel: {excel_path}")
    df = pd.read_excel(excel_path, skiprows=1)
    df.columns = [normalizar_texto(c) for c in df.columns]
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    print(f"✅ JSON gerado: {json_path} ({len(df)} registros)")

if __name__ == "__main__":
    excel_para_json(EXCEL_SP, JSON_SP)
    excel_para_json(EXCEL_MG, JSON_MG)
    excel_para_json(EXCEL_MES_SP, JSON_MES_SP)
    excel_para_json(EXCEL_MES_MG, JSON_MES_MG)
    print("✅ Conversão concluída.")
