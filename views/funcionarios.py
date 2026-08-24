import streamlit as st
import pandas as pd
from pathlib import Path
from database.db import get_connection

st.markdown("## 👷 Funcionários")

# ---------------------------------------------------------------------
# GARANTIA DA TABELA DE FUNCIONÁRIOS
# ---------------------------------------------------------------------
def garantir_tabela_funcionarios():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            funcao TEXT DEFAULT 'OPERADOR'
        )
    """)
    conn.commit()
    conn.close()

garantir_tabela_funcionarios()

# ---------------------------------------------------------------------
# BUSCA E CARGA NATIVA AUTOMÁTICA DA PLANILHA DE FUNCIONÁRIOS
# ---------------------------------------------------------------------
def localizar_planilha_funcionarios():
    raiz_projeto = Path(__file__).resolve().parents[1]
    for arquivo in raiz_projeto.rglob("*.xlsx"):
        if "funcionario" in arquivo.name.lower() or "func" in arquivo.name.lower():
            return str(arquivo)
    return None

def sincronizar_funcionarios_nativamente():
    caminho = localizar_planilha_funcionarios()
    if not caminho:
        return

    try:
        conn = get_connection()
        c = conn.cursor()
        
        # Verifica se o banco já possui registros
        c.execute("SELECT COUNT(*) FROM funcionarios")
        total = c.fetchone()[0]

        df = pd.read_excel(caminho)
        df.columns = [str(col).strip().lower() for col in df.columns]

        # Se o banco estiver vazio ou desatualizado em relação à planilha, repopula
        if total == 0 or total != len(df):
            c.execute("DELETE FROM funcionarios")
            
            for _, row in df.iterrows():
                # Tenta pegar coluna Nome / Funcionario
                nome = None
                for col in row.index:
                    if col in ['nome', 'funcionario', 'colaborador']:
                        nome = row[col]
                        break
                
                # Tenta pegar coluna Função / Cargo
                funcao = "OPERADOR"
                for col in row.index:
                    if col in ['funcao', 'função', 'cargo', 'ofício']:
                        if pd.notnull(row[col]):
                            funcao = row[col]
                        break

                if nome and pd.notnull(nome) and str(nome).strip():
                    c.execute("""
                        INSERT OR IGNORE INTO funcionarios (nome, funcao)
                        VALUES (?, ?)
                    """, (str(nome).strip(), str(funcao).strip()))

            conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Erro ao carregar funcionários nativamente: {e}")

sincronizar_funcionarios_nativamente()

# ---------------------------------------------------------------------
# FORMULÁRIO PARA ADICIONAR FUNCIONÁRIO MANUALMENTE
# ---------------------------------------------------------------------
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        novo_nome = st.text_input("Nome", key="input_nome_func")
    with col2:
        nova_funcao = st.text_input("Função", key="input_funcao_func")
        
    if st.button("➕ Adicionar Funcionário", use_container_width=True, type="primary"):
        if novo_nome.strip():
            conn = get_connection()
            c = conn.cursor()
            try:
                c.execute("INSERT INTO funcionarios (nome, funcao) VALUES (?, ?)", 
                          (novo_nome.strip(), nova_funcao.strip() if nova_funcao.strip() else "OPERADOR"))
                conn.commit()
                st.success(f"Funcionário '{novo_nome}' cadastrado!")
                st.rerun()
            except Exception:
                st.error("Funcionário já cadastrado com este nome.")
            finally:
                conn.close()
        else:
            st.warning("Preencha o nome do funcionário.")

st.markdown("---")

# ---------------------------------------------------------------------
# LISTAGEM E EXCLUSÃO DE FUNCIONÁRIOS
# ---------------------------------------------------------------------
conn = get_connection()
c = conn.cursor()
c.execute("SELECT * FROM funcionarios ORDER BY nome ASC")
funcionarios = [dict(r) for r in c.fetchall()]
conn.close()

if funcionarios:
    st.subheader(f"Lista de Funcionários ({len(funcionarios)} cadastrados)")
    
    col_n, col_f, col_a = st.columns([4, 4, 1])
    col_n.markdown("**Nome**")
    col_f.markdown("**Função**")
    col_a.markdown("**Ação**")
    st.divider()

    for func in funcionarios:
        c1, c2, c3 = st.columns([4, 4, 1])
        c1.write(f"**{func['nome']}**")
        c2.write(func.get('funcao', 'OPERADOR'))
        if c3.button("🗑️", key=f"del_func_{func['id']}"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("DELETE FROM funcionarios WHERE id = ?", (func['id'],))
            conn.commit()
            conn.close()
            st.rerun()
else:
    st.info("Nenhum funcionário cadastrado no momento.")
