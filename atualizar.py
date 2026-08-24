import os
import pandas as pd
import sqlite3

def limpar_preco(val):
    if pd.isna(val) or val == '':
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    # Tratamento para strings de moeda brasileira
    val_str = str(val).replace("R$", "").replace("\xa0", "").strip()
    val_str = val_str.replace(".", "").replace(",", ".")
    try:
        return float(val_str)
    except ValueError:
        return 0.0

def atualizar_estoque_via_excel():
    raiz = os.path.dirname(os.path.abspath(__file__))
    caminho_excel = os.path.join(raiz, "dados", "planilha_estoque.xlsx")
    caminho_db = os.path.join(raiz, "banco de dados", "estoque.db")

    if not os.path.exists(caminho_excel):
        print(f"Erro: Planilha não encontrada em {caminho_excel}")
        return

    df = pd.read_excel(caminho_excel)

    # Conexão com SQLite
    conn = sqlite3.connect(caminho_db)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE,
            nome TEXT NOT NULL,
            categoria TEXT DEFAULT 'TRANSPORTE',
            estoque REAL DEFAULT 0,
            unidade TEXT DEFAULT 'UN',
            preco REAL DEFAULT 0.0
        )
    """)

    # Prepara os dados em uma lista de tuplas para inserção em lote
    dados_para_inserir = [
        (
            str(row['Código']).strip(),
            str(row['Descrição']).strip(),
            float(row['Estoque']) if pd.notnull(row['Estoque']) else 0.0,
            str(row['UN']).strip(),
            limpar_preco(row['Vl. Últ. Ent.'])
        )
        for _, row in df.iterrows()
    ]

    # Inserção rápida em lote
    query = """
        INSERT INTO produtos (codigo, nome, categoria, estoque, unidade, preco)
        VALUES (?, ?, 'TRANSPORTE', ?, ?, ?)
        ON CONFLICT(codigo) DO UPDATE SET
            nome=excluded.nome,
            estoque=excluded.estoque,
            unidade=excluded.unidade,
            preco=excluded.preco
    """
    
    cursor.executemany(query, dados_para_inserir)
    conn.commit()
    conn.close()

    print(f"Sucesso! {len(dados_para_inserir)} produtos atualizados no banco de dados.")

if __name__ == "__main__":
    atualizar_estoque_via_excel()
