import streamlit as st
import os
import pandas as pd
from pathlib import Path
from database.db import get_connection

st.markdown("## 📦 Gestão de Produtos")

# ---------------------------------------------------------------------
# REPARO E GARANTIA DA TABELA DE PRODUTOS
# ---------------------------------------------------------------------
def ajustar_estrutura_tabela():
    conn = get_connection()
    c = conn.cursor()
    c.execute("PRAGMA table_info(produtos)")
    colunas = [info[1] for info in c.fetchall()]
    
    if not colunas or 'estoque' not in colunas:
        c.execute("DROP TABLE IF EXISTS produtos")
        c.execute("""
            CREATE TABLE produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT UNIQUE,
                nome TEXT NOT NULL,
                categoria TEXT DEFAULT 'TRANSPORTE',
                estoque REAL DEFAULT 0,
                unidade TEXT DEFAULT 'UN',
                preco REAL DEFAULT 0.0
            )
        """)
        conn.commit()
    conn.close()

ajustar_estrutura_tabela()

# ---------------------------------------------------------------------
# LOCALIZADOR AUTOMÁTICO DA PLANILHA NO PROJETO
# ---------------------------------------------------------------------
def localizar_planilha():
    raiz_projeto = Path(__file__).resolve().parents[1]
    for arquivo in raiz_projeto.rglob("*.xlsx"):
        if "estoque" in arquivo.name.lower() or "planilha" in arquivo.name.lower():
            return str(arquivo)
    
    for arquivo in Path.cwd().rglob("*.xlsx"):
        if "estoque" in arquivo.name.lower() or "planilha" in arquivo.name.lower():
            return str(arquivo)
        
    return None

def extrair_coluna(row, opcoes_nomes, padrao=""):
    for col in row.index:
        col_limpa = str(col).strip().lower()
        for opcao in opcoes_nomes:
            if opcao.lower() == col_limpa:
                val = row[col]
                if pd.notnull(val):
                    return val
    return padrao

# ---------------------------------------------------------------------
# SINCRONIZAÇÃO SILENCIOSA E NATIVA DA PLANILHA COM O SQLite
# ---------------------------------------------------------------------
def carregar_dados_nativamente():
    caminho_anexado = localizar_planilha()
    if not caminho_anexado:
        return

    try:
        conn = get_connection()
        c = conn.cursor()
        
        # Verifica se o banco já tem dados
        c.execute("SELECT COUNT(*) FROM produtos")
        total_banco = c.fetchone()[0]

        # Lê o arquivo da pasta dados
        df = pd.read_excel(caminho_anexado)
        df.columns = [str(col).strip() for col in df.columns]

        # Se o banco estiver vazio ou o número de itens for diferente, atualiza o banco
        if total_banco == 0 or total_banco != len(df):
            c.execute("DELETE FROM produtos")
            
            for _, row in df.iterrows():
                codigo_raw = extrair_coluna(row, ['Código', 'Codigo', 'Cod'], None)
                if not codigo_raw or str(codigo_raw).strip().lower() in ['nan', 'none', '']:
                    continue
                codigo = str(codigo_raw).strip()

                nome_raw = extrair_coluna(row, ['Descrição', 'Descricao', 'Nome'], "PRODUTO SEM NOME")
                nome = str(nome_raw).strip()

                unidade_raw = extrair_coluna(row, ['Un.', 'Un', 'UN', 'Emb.', 'Emb'], "UN")
                unidade = str(unidade_raw).strip()

                estoque_raw = extrair_coluna(row, ['Estoque', 'Qtd', 'Quantidade'], 0.0)
                try:
                    estoque = float(str(estoque_raw).replace(".", "").replace(",", ".")) if isinstance(estoque_raw, str) else float(estoque_raw)
                except (ValueError, TypeError):
                    estoque = 0.0

                preco_raw = extrair_coluna(row, ['Últ. Ent.', 'Ult. Ent.', 'Últ.Ent.', 'Ult.Ent.', 'Preço', 'Preco'], 0.0)
                if pd.isna(preco_raw):
                    preco = 0.0
                elif isinstance(preco_raw, (int, float)):
                    preco = float(preco_raw)
                else:
                    p_str = str(preco_raw).replace("R$", "").replace("\xa0", "").strip()
                    p_str = p_str.replace(".", "").replace(",", ".")
                    try:
                        preco = float(p_str)
                    except ValueError:
                        preco = 0.0

                c.execute("""
                    INSERT INTO produtos (codigo, nome, categoria, estoque, unidade, preco)
                    VALUES (?, ?, 'TRANSPORTE', ?, ?, ?)
                """, (codigo, nome, estoque, unidade, preco))

            conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro no carregamento automático do estoque: {e}")

# Executa a carga nativa automaticamente antes de exibir a tela
carregar_dados_nativamente()

# ---------------------------------------------------------------------
# LISTAGEM EM FORMATO DE TABELA
# ---------------------------------------------------------------------
conn = get_connection()
c = conn.cursor()
c.execute("SELECT * FROM produtos ORDER BY id ASC")
produtos = [dict(r) for r in c.fetchall()]
conn.close()

if produtos:
    st.subheader(f"Lista de Produtos ({len(produtos)} itens)")
    
    pesquisa = st.text_input("🔍 Pesquisar produto por nome ou código...", "")
    
    c_cod, c_nome, c_un, c_est, c_pr, c_tot, c_act = st.columns([1.5, 4, 1, 1.5, 1.5, 1.5, 1])
    c_cod.markdown("**Código**")
    c_nome.markdown("**Descrição**")
    c_un.markdown("**Un.**")
    c_est.markdown("**Estoque**")
    c_pr.markdown("**Últ. Ent.**")
    c_tot.markdown("**Valor Total**")
    c_act.markdown("**Ação**")
    st.divider()

    for p in produtos:
        if pesquisa.lower() in str(p['codigo']).lower() or pesquisa.lower() in str(p['nome']).lower():
            col_cd, col_nm, col_u, col_es, col_pr, col_tot, col_bt = st.columns([1.5, 4, 1, 1.5, 1.5, 1.5, 1])
            
            qtd_est = float(p.get('estoque', 0.0))
            prc_un = float(p.get('preco', 0.0))
            val_tot = qtd_est * prc_un
            
            col_cd.write(p.get('codigo', '-'))
            col_nm.write(f"**{p.get('nome', '-')}**")
            col_u.write(p.get('unidade', 'UN'))
            col_es.write(f"{qtd_est:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            col_pr.write(f"R$ {prc_un:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            col_tot.write(f"R$ {val_tot:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            if col_bt.button("🗑️", key=f"del_prod_{p['id']}"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM produtos WHERE id = ?", (p['id'],))
                conn.commit()
                conn.close()
                st.rerun()
else:
    st.info("Nenhum produto cadastrado no banco de dados.")
