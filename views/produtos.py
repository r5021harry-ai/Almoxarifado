import streamlit as st
import os, re
import pdfplumber
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
            categoria TEXT,
            estoque REAL DEFAULT 0,
            unidade TEXT DEFAULT 'UN',
            preco REAL DEFAULT 0.0
        )
    """)
    conn.commit()
    conn.close()

garantir_tabela_produtos()

# ---------------------------------------------------------------------
# LOCALIZADOR AUTOMÁTICO DO PDF "286"
# ---------------------------------------------------------------------
def encontrar_pdf_286():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_dados = os.path.join(raiz, "dados")
    
    if os.path.exists(pasta_dados):
        for arq in os.listdir(pasta_dados):
            if "286" in arq and arq.lower().endswith(".pdf"):
                return os.path.join(pasta_dados, arq)
                
    # Busca secundária por todo o diretório se não achar direto na pasta dados
    for pasta_atual, _, arquivos in os.walk(raiz):
        for arq in arquivos:
            if "286" in arq and arq.lower().endswith(".pdf"):
                return os.path.join(pasta_atual, arq)
    return None

# ---------------------------------------------------------------------
# PROCESSADOR DO PDF (EXTRAÇÃO DE DADOS)
# ---------------------------------------------------------------------
def processar_pdf_produtos(caminho_pdf):
    try:
        conn = get_connection()
        c = conn.cursor()
        inseridos = 0

        with pdfplumber.open(caminho_pdf) as pdf:
            for page in pdf.pages:
                # Tenta extrair como tabela
                tabelas = page.extract_tables()
                for tabela in tabelas:
                    for linha in tabela:
                        if not linha or len(linha) < 2:
                            continue
                        
                        # Limpeza de texto
                        texto_linha = [str(cell).strip() if cell else "" for cell in linha]
                        
                        # Tenta identificar código, nome e estoque
                        # Padrão comum: [CÓDIGO, NOME/DESCRIÇÃO, UNIDADE, ESTOQUE, PREÇO]
                        codigo = texto_linha[0]
                        if not codigo.isdigit() and len(codigo) < 2:
                            continue  # Pula cabeçalhos
                            
                        nome = texto_linha[1] if len(texto_linha) > 1 else "PRODUTO SEM NOME"
                        unidade = texto_linha[2] if len(texto_linha) > 2 and len(texto_linha[2]) <= 3 else "UN"
                        
                        # Tenta converter estoque para número
                        qtd = 0.0
                        for val in texto_linha[2:]:
                            val_limpo = val.replace(".", "").replace(",", ".")
                            try:
                                qtd = float(val_limpo)
                                break
                            except ValueError:
                                continue

                        c.execute("""
                            INSERT INTO produtos (codigo, nome, categoria, estoque, unidade, preco)
                            VALUES (?, ?, 'Geral', ?, ?, 0.0)
                            ON CONFLICT(codigo) DO UPDATE SET
                                nome=excluded.nome,
                                estoque=excluded.estoque,
                                unidade=excluded.unidade
                        """, (codigo, nome, qtd, unidade))
                        inseridos += 1
                        
        conn.commit()
        conn.close()
        return inseridos
    except Exception as e:
        st.error(f"Erro ao ler PDF: {e}")
        return 0

# ---------------------------------------------------------------------
# BOTÃO DE IMPORTAÇÃO E PROCESSAMENTO
# ---------------------------------------------------------------------
caminho_pdf = encontrar_pdf_286()

col_imp1, col_imp2 = st.columns([3, 1])
with col_imp1:
    if caminho_pdf:
        st.info(f"📄 Arquivo localizado: `{os.path.basename(caminho_pdf)}`")
    else:
        st.warning("⚠️ Nenhum arquivo PDF contendo '286' foi encontrado na pasta `dados`.")

with col_imp2:
    if caminho_pdf and st.button("🔄 Importar do PDF 286", use_container_width=True):
        qtd = processar_pdf_produtos(caminho_pdf)
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
    
    # Busca/Filtro
    pesquisa = st.text_input("🔍 Pesquisar produto por nome ou código...", "")
    
    # Cabeçalho
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
            col_ct.write(p.get('categoria', 'Geral'))
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
