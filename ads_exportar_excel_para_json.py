import os
import json
import pandas as pd
import unicodedata

# Caminhos dos arquivos Excel
EXCEL_7d_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_SP.xlsx"
EXCEL_7d_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_07d_total_MG.xlsx"
EXCEL_15d_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_15d_total_SP.xlsx"
EXCEL_15d_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_15d_total_MG.xlsx"
EXCEL_30d_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_30d_total_SP.xlsx"
EXCEL_30d_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_30d_total_MG.xlsx"
EXCEL_MES_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_mes_total_SP.xlsx"
EXCEL_MES_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\Relatorio_anuncios_patrocinados_mes_total_MG.xlsx"

# Caminhos dos arquivos JSON de saída
JSON_7d_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\tokens\publicidade\ads_7d_sp.json"
JSON_7d_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\tokens\publicidade\ads_7d_mg.json"
JSON_15d_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\tokens\publicidade\ads_15d_sp.json"
JSON_15d_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\tokens\publicidade\ads_15d_mg.json"
JSON_30d_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\tokens\publicidade\ads_30d_sp.json"
JSON_30d_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\tokens\publicidade\ads_30d_mg.json"
JSON_MES_SP = r"C:\Users\dmdel\OneDrive\Aplicativos\tokens\publicidade\ads_mes_sp.json"
JSON_MES_MG = r"C:\Users\dmdel\OneDrive\Aplicativos\tokens\publicidade\ads_mes_mg.json"

# -------------------- Função de normalização de colunas --------------------
def normalizar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        return texto
    texto = texto.strip().replace("\n", "_")
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("ASCII")
    return texto.lower().replace(" ", "_")

# -------------------- Conversão Excel → JSON --------------------
def excel_para_json(excel_path: str, json_path: str):
    if not os.path.exists(excel_path):
        print(f"❌ Arquivo não encontrado: {excel_path}")
        return

    print(f"🔄 Lendo Excel: {excel_path}")
    df = pd.read_excel(excel_path, skiprows=1)
    df.columns = [normalizar_texto(c) for c in df.columns]

    meses_pt_en = {
        "jan": "Jan", "fev": "Feb", "mar": "Mar", "abr": "Apr", "mai": "May", "jun": "Jun",
        "jul": "Jul", "ago": "Aug", "set": "Sep", "out": "Oct", "nov": "Nov", "dez": "Dec"
    }

    def traduzir_mes(data_str):
        if isinstance(data_str, str):
            for pt, en in meses_pt_en.items():
                data_str = data_str.lower().replace(f"-{pt}-", f"-{en}-")
        return data_str

    for col in ["desde", "ate"]:
        if col in df.columns:
            df[col] = df[col].astype(str).apply(traduzir_mes)
            df[col] = pd.to_datetime(df[col], format="%d-%b-%Y", errors="coerce").dt.date.astype(str)

    df.to_json(json_path, orient="records", force_ascii=False, indent=2)
    print(f"✅ JSON gerado: {json_path} ({len(df)} registros)")

# -------------------- Execução principal --------------------
if __name__ == "__main__":
    print("🚀 Iniciando exportação de relatórios de ADS para JSON...\n")

    excel_para_json(EXCEL_7d_SP, JSON_7d_SP)
    excel_para_json(EXCEL_7d_MG, JSON_7d_MG)
    excel_para_json(EXCEL_15d_SP, JSON_15d_SP)
    excel_para_json(EXCEL_15d_MG, JSON_15d_MG)
    excel_para_json(EXCEL_30d_SP, JSON_30d_SP)
    excel_para_json(EXCEL_30d_MG, JSON_30d_MG)
    excel_para_json(EXCEL_MES_SP, JSON_MES_SP)
    excel_para_json(EXCEL_MES_MG, JSON_MES_MG)

    print("\n✅ Conversão concluída com sucesso.")