import sqlite3
import openpyxl
import pypdf
import re
import os

# Caminho do banco de dados dentro da pasta 'banco de dados'
DB_PATH = os.path.join("banco de dados", "almoxarifado.db")

def atualizar_sistema():
    if not os.path.exists(DB_PATH):
        # Procura por qualquer arquivo .db dentro da pasta 'banco de dados'
        arquivos = [f for f in os.listdir("banco de dados") if f.endswith('.db')]
        if arquivos:
            caminho_db = os.path.join("banco de dados", arquivos[0])
        else:
            print("❌ Banco de dados não encontrado na pasta 'banco de dados'.")
            return
    else:
        caminho_db = DB_PATH

    conn = sqlite3.connect(caminho_db)
    c = conn.cursor()

    # 1. ZERAR E REIMPORTAR PRODUTOS (286.pdf)
    pdf_path = os.path.join("dados", "286.pdf")
    if os.path.exists(pdf_path):
        print("🔄 Apagando produtos antigos...")
        c.execute("DELETE FROM produtos;")
        
        reader = pypdf.PdfReader(pdf_path)
        produtos_inseridos = 0
        
        for page in reader.pages:
            for line in page.extract_text().splitlines():
                line = line.strip()
                m = re.match(r'^(\d{2,6})(.+?)\s+(\d+UN|\d+BL|\d+PT|\d+LT|\d+KG|1|UN|BL|PT|KG|LT|1 PT)\s+([\d\.\,]+)\s+([\d\.\,]+)\s*(UN|BL|PT|KG|LT)?\s*2$', line)
                if m:
                    codigo = m.group(1).strip()
                    nome = m.group(2).strip()
                    estoque = float(m.group(4).replace('.', '').replace(',', '.'))
                    preco = float(m.group(5).replace('.', '').replace(',', '.'))
                    unidade = m.group(6) if m.group(6) else "UN"

                    c.execute("""
                        INSERT INTO produtos (codigo, nome, estoque_atual, preco_unitario, unidade)
                        VALUES (?, ?, ?, ?, ?)
                    """, (codigo, nome, estoque, preco, unidade))
                    produtos_inseridos += 1

        print(f"✅ {produtos_inseridos} produtos cadastrados com sucesso!")
    else:
        print("❌ Arquivo 'dados/286.pdf' não encontrado.")

    # 2. IMPORTAR VEÍCULOS (FROTA.xlsx)
    excel_path = os.path.join("dados", "FROTA.xlsx")
    if os.path.exists(excel_path):
        wb = openpyxl.load_workbook(excel_path)
        sheet = wb.active
        veiculos_inseridos = 0
        
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row[0]:
                placa = str(row[0]).strip()
                propriedade = str(row[1]).strip() if row[1] else ""
                renavam = str(row[2]).strip() if row[2] else ""
                chassi = str(row[3]).strip() if row[3] else ""
                modelo = str(row[4]).strip() if row[4] else ""

                c.execute("""
                    INSERT OR REPLACE INTO veiculos (placa, modelo, renavam, chassi, propriedade)
                    VALUES (?, ?, ?, ?, ?)
                """, (placa, modelo, renavam, chassi, propriedade))
                veiculos_inseridos += 1
                
        print(f"✅ {veiculos_inseridos} veículos cadastrados com sucesso!")
    else:
        print("❌ Arquivo 'dados/FROTA.xlsx' não encontrado.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    atualizar_sistema()
