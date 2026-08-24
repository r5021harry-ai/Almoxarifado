import streamlit as st
import os
import pandas as pd
from database.db import get_connection

st.markdown("## 📦 Gestão de Produtos")

# ---------------------------------------------------------------------
# REPARO E GARANTIA DA TABELA DE PRODUTOS
# ---------------------------------------------------------------------
def garantir_tabela_produtos():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
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
    conn.commit()
    conn.close()

garantir_tabela_produtos()

# ---------------------------------------------------------------------
# LOCALIZADOR AUTOMÁTICO DA PLANILHA DE ESTOQUE
# ---------------------------------------------------------------------
def encontrar_planilha_estoque():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    caminho_excel = os.path.join(raiz, "dados", "planilha_estoque.xlsx")
    
    if os.path.exists(caminho_excel):
        return caminho_excel
    return None

# ---------------------------------------------------------------------
# PROCESSADOR DA PLANILHA EXCEL
# ---------------------------------------------------------------------
def processar_planilha_produtos(caminho_excel):
    try:
        df = pd.read_excel(caminho_excel)
        
        conn = get_connection()
        c = conn.cursor()
        inseridos = 0

        for _, row in df.iterrows():
            codigo = str(row['Código']).strip() if pd.notnull(row['Código']) else None
            if not codigo or codigo.lower() == 'nan':
                continue

            nome = str(row['Descrição']).strip() if pd.notnull(row['Descrição']) else "PRODUTO SEM NOME"
            unidade = str(row['UN']).strip() if pd.notnull(row['UN']) else "UN"
            
            try:
                estoque = float(row['Estoque']) if pd.notnull(row['Estoque']) else 0.0
            except ValueError:
                estoque = 0.0

            preco_val = row.get('Vl. Últ. Ent.', 0.0)
            if pd.isna(preco_val):
                preco = 0.0
            elif isinstance(preco_val, (int, float)):
                preco = float(preco_val)
            else:
                p_str = str(preco_val).replace("R$", "").replace("\xa0", "").strip()
                p_str = p_str.replace(".", "").replace(",", ".")
                try:
                    preco = float(p_str)
                except ValueError:
                    preco = 0.0

            c.execute("""
                INSERT INTO produtos (codigo, nome, categoria, estoque, unidade, preco)
                VALUES (?, ?, 'TRANSPORTE', ?, ?, ?)
                ON CONFLICT(codigo) DO UPDATE SET
                    nome=excluded.nome,
                    estoque=excluded.estoque,
                    unidade=excluded.unidade,
                    preco=excluded.preco
            """, (codigo, nome, estoque, unidade, preco))
            inseridos += 1

        conn.commit()
        conn.close()
        return inseridos
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")
        return 0

# ---------------------------------------------------------------------
# BOTÃO DE IMPORTAÇÃO E PROCESSAMENTO
# ---------------------------------------------------------------------
caminho_excel = encontrar_planilha_estoque()

col_imp1, col_imp2 = st.columns([3, 1])
with col_imp1:
    if caminho_excel:
        st.info(f"📊 Planilha localizada: `{os.path.basename(caminho_excel)}`")
    else:
        st.warning("⚠️ Arquivo `planilha_estoque.xlsx` não foi encontrado na pasta `dados`.")

with col_imp2:
    if caminho_excel and st.button("🔄 Importar da Planilha", use_container_width=True):
        qtd = processar_planilha_produtos(caminho_excel)
        if qtd > 0:
            st.success(f"✅ {qtd} produtos atualizados!")
            st.rerun()

st.markdown("---")

# ---------------------------------------------------------------------
# LISTAGEM E EXIBIÇÃO DOS PRODUTOS
# ---------------------------------------------------------------------
conn = get_connection()
c = conn.cursor()
c.execute("SELECT * FROM produtos ORDER BY id DESC")
produtos = [dict(r) for r in c.fetchall()]
conn.close()

if produtos:
    st.subheader(f"Lista de Produtos ({len(produtos)} itens)")
    
    pesquisa = st.text_input("🔍 Pesquisar produto por nome ou código...", "")
    
    c_cod, c_nome, c_cat, c_est, c_un, c_pr, c_act = st.columns([1.5, 4, 2, 1.5, 1, 1.5, 1])
    c_cod.markdown("**Código**")
    c_nome.markdown("**Nome do Produto**")
    c_cat.markdown("**Categoria**")
    c_est.markdown("**Estoque**")
    c_un.markdown("**UN**")
    c_pr.markdown("**Preço Un.**")
    c_act.markdown("**Ação**")
    st.divider()

    for p in produtos:
        if pesquisa.lower() in str(p['codigo']).lower() or pesquisa.lower() in str(p['nome']).lower():
            col_cd, col_nm, col_ct, col_es, col_u, col_pr, col_bt = st.columns([1.5, 4, 2, 1.5, 1, 1.5, 1])
            
            col_cd.write(p.get('codigo', '-'))
            col_nm.write(f"**{p.get('nome', '-')}**")
            col_ct.write(p.get('categoria', 'TRANSPORTE'))
            col_es.write(f"{p.get('estoque', 0.0)}")
            col_u.write(p.get('unidade', 'UN'))
            col_pr.write(f"R$ {p.get('preco', 0.0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            
            if col_bt.button("🗑️", key=f"del_prod_{p['id']}"):
                conn = get_connection()
                c = conn.cursor()
                c.execute("DELETE FROM produtos WHERE id = ?", (p['id'],))
                conn.commit()
                conn.close()
                st.rerun()
else:
    st.info("Nenhum produto cadastrado.")
