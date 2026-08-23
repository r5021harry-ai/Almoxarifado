import streamlit as st
from database.db import get_connection

st.markdown("## 👷 Funcionários")

conn = get_connection()
c = conn.cursor()

# Cria a tabela se não existir
c.execute("""
    CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        funcao TEXT,
        status TEXT DEFAULT 'Ativo'
    )
""")
conn.commit()
conn.close()

# Formuário de Cadastro
with st.form("form_funcionario", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome")
    with col2:
        funcao = st.text_input("Função")
        
    btn_salvar = st.form_submit_button("➕ Adicionar", use_container_width=False)

if btn_salvar:
    if nome.strip():
        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO funcionarios (nome, funcao, status) VALUES (?, ?, 'Ativo')", (nome.strip(), funcao.strip()))
            conn.commit()  # Persiste a alteração no disco
            st.success(f"Funcionário '{nome}' adicionado com sucesso!")
            st.rerun()
        except Exception as e:
            conn.rollback()
            st.error(f"Erro ao salvar: {e}")
        finally:
            conn.close()
    else:
        st.warning("Preencha o campo Nome.")

st.markdown("---")

# Listagem dos Funcionários
conn = get_connection()
c = conn.cursor()
c.execute("SELECT * FROM funcionarios ORDER BY id DESC")
funcionarios = [dict(r) for r in c.fetchall()]
conn.close()

if funcionarios:
    for f in funcionarios:
        col_n, col_f, col_s, col_b = st.columns([3, 3, 2, 2])
        col_n.write(f["nome"])
        col_f.write(f["funcao"] or "-")
        col_s.write(f["status"])
        
        novo_status = "Inativo" if f["status"] == "Ativo" else "Ativo"
        if col_b.button(f"Marcar {novo_status}", key=f"btn_func_{f['id']}"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE funcionarios SET status = ? WHERE id = ?", (novo_status, f["id"]))
            conn.commit()
            conn.close()
            st.rerun()
else:
    st.info("Nenhum funcionário cadastrado.")
