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
# BUSCA DINÂMICA PELA PLANILHA NO PROJETO
# ---------------------------------------------------------------------
def localizar_planilha():
    # Busca 'planilha_estoque.xlsx' em qualquer pasta do projeto
    raiz_projeto = Path(__file__).resolve().parents[1]
    for arquivo in raiz_projeto.rglob("planilha_estoque.xlsx"):
        return str(arquivo)
    
    # Busca alternativa pelo diretório de trabalho atual
    for arquivo in Path.cwd().rglob("planilha_estoque.xlsx"):
        return str(arquivo)
        
    return None

# ---------------------------------------------------------------------
# EXTRATOR ROBUSTO DE COLUNAS
# ---------------------------------------------------------------------
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
# PROCESSADOR DO DATAFRAME
# ---------------------------------------------------------------------
def processar_dataframe(df):
    try:
        conn = get_connection()
        c = conn.cursor()
        inseridos = 0

        # Normaliza nomes de colunas no DF para facilitar busca
        df.columns = [str(col).strip() for col in df.columns]

        for _, row in df.iterrows():
            codigo_raw = extrair_coluna(row, ['Código', 'Codigo', 'Cod', 'ID'], None)
            if not codigo_raw or str(codigo_raw).strip().lower() in ['nan', 'none', '']:
                continue
            codigo = str(codigo_raw).strip()

            nome_raw = extrair_coluna(row, ['Descrição', 'Descricao', 'Nome', 'Produto', 'Item'], "PRODUTO SEM NOME")
            nome = str(nome_raw).strip()

            unidade_raw = extrair_coluna(row, ['UN', 'Unidade', 'Un', 'U.M.', 'UM'], "UN")
            unidade = str(unidade_raw).strip()

            estoque_raw = extrair_coluna(row, ['Estoque', 'Qtd', 'Quantidade', 'Saldo', 'Estoque Atual'], 0.0)
            try:
                estoque = float(str(estoque_raw).replace(",", "."))
            except (ValueError, TypeError):
                estoque = 0.0

            preco_raw = extrair_coluna(row, ['Vl. Últ. Ent.', 'Vl. Ult. Ent.', 'Preço', 'Preco', 'Valor', 'Vl. Unit.'], 0.0)
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
# PAINEL DE CONTROLE DE ARQUIVO E BANCO
# ---------------------------------------------------------------------
caminho_encontrado = localizar_planilha()

if caminho_encontrado:
    st.success(f"📌 Planilha localizada no servidor: `{caminho_encontrado}`")
else:
    st.warning("⚠️ O arquivo `planilha_estoque.xlsx` não foi localizado automaticamente nas pastas do projeto.")

col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1.5])

with col_btn1:
    if caminho_encontrado and st.button("🔄 Importar da Pasta 'dados'", type="primary", use_container_width=True):
        df_arq = pd.read_excel(caminho_encontrado)
        qtd = processar_dataframe(df_arq)
        if qtd > 0:
            st.success(f"✅ {qtd} produtos importados/atualizados com sucesso!")
            st.rerun()

with col_btn2:
    arq_up = st.file_uploader("Upload manual da planilha", type=["xlsx"], label_visibility="collapsed")
    if arq_up:
        df_up = pd.read_excel(arq_up)
        qtd = processar_dataframe(df_up)
        if qtd > 0:
            st.success(f"✅ {qtd} produtos importados via upload!")
            st.rerun()

with col_btn3:
    if st.button("🗑️ Zerar Banco de Dados", type="secondary", use_container_width=True):
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM produtos")
        conn.commit()
        conn.close()
        st.warning("Banco de dados zerado!")
        st.rerun()

st.markdown("---")

# ---------------------------------------------------------------------
# EXIBIÇÃO E BUSCA DE PRODUTOS
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
