import streamlit as st
import os
import pandas as pd
from pathlib import Path
from database.db import get_connection

st.markdown("## 📦 Gestão de Produtos")

# ---------------------------------------------------------------------
# GARANTIA DA TABELA DE PRODUTOS
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
# LOCALIZADOR DE CAMINHO ABSOLUTO
# ---------------------------------------------------------------------
def obter_caminho_planilha_dados():
    # Sobe 1 nível do arquivo atual (vistas/produtos.py -> Raiz do Projeto)
    raiz = Path(__file__).resolve().parents[1]
    caminho = raiz / "dados" / "planilha_estoque.xlsx"
    if caminho.exists():
        return str(caminho)
    return None

# ---------------------------------------------------------------------
# AUXILIAR PARA PEGAR VALOR DE COLUNA DE FORMA SEGURA
# ---------------------------------------------------------------------
def obter_valor(row, nomes_possiveis, padrao=""):
    for col in row.index:
        if str(col).strip().lower() in [n.lower() for n in nomes_possiveis]:
            val = row[col]
            if pd.notnull(val):
                return val
    return padrao

# ---------------------------------------------------------------------
# PROCESSADOR DA PLANILHA EXCEL
# ---------------------------------------------------------------------
def processar_df_produtos(df):
    try:
        conn = get_connection()
        c = conn.cursor()
        inseridos = 0

        for _, row in df.iterrows():
            codigo_raw = obter_valor(row, ['Código', 'Codigo', 'Cod'], None)
            if not codigo_raw or str(codigo_raw).strip().lower() in ['nan', 'none', '']:
                continue
            codigo = str(codigo_raw).strip()

            nome_raw = obter_valor(row, ['Descrição', 'Descricao', 'Nome', 'Produto'], "PRODUTO SEM NOME")
            nome = str(nome_raw).strip()

            unidade_raw = obter_valor(row, ['UN', 'Unidade', 'Un', 'U.M.', 'UM'], "UN")
            unidade = str(unidade_raw).strip()

            estoque_raw = obter_valor(row, ['Estoque', 'Qtd', 'Quantidade', 'Saldo'], 0.0)
            try:
                estoque = float(estoque_raw)
            except (ValueError, TypeError):
                estoque = 0.0

            preco_val = obter_valor(row, ['Vl. Últ. Ent.', 'Vl. Ult. Ent.', 'Preço', 'Preco', 'Valor', 'Vl. Unit.'], 0.0)
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
        st.error(f"Erro ao processar dados da planilha: {e}")
        return 0

# ---------------------------------------------------------------------
# CONTROLES E PAINEL
# ---------------------------------------------------------------------
caminho_anexado = obter_caminho_planilha_dados()

if caminho_anexado:
    st.success(f"📌 Planilha detectada na pasta `dados`: **`planilha_estoque.xlsx`**")
else:
    st.warning("⚠️ O arquivo `planilha_estoque.xlsx` não foi localizado na pasta `dados`.")

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    if caminho_anexado and st.button("🔄 Sincronizar da Pasta 'dados'", type="primary", use_container_width=True):
        df_local = pd.read_excel(caminho_anexado)
        qtd = processar_df_produtos(df_local)
        if qtd > 0:
            st.success(f"✅ {qtd} produtos importados do arquivo local!")
            st.rerun()

with col2:
    arquivo_upload = st.file_uploader("Ou envie manualmente (.xlsx)", type=["xlsx"], label_visibility="collapsed")
    if arquivo_upload:
        df_upload = pd.read_excel(arquivo_upload)
        qtd = processar_df_produtos(df_upload)
        if qtd > 0:
            st.success(f"✅ {qtd} produtos carregados via upload!")
            st.rerun()

with col3:
    if st.button("🗑️ Limpar Banco", use_container_width=True):
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM produtos")
        conn.commit()
        conn.close()
        st.warning("Banco zerado!")
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------------------
# LISTAGEM DE PRODUTOS
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
    st.info("Nenhum produto cadastrado no banco de dados.")
