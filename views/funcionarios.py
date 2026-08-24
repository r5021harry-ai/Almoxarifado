import streamlit as st
from database.db import get_connection

st.markdown("## 👷 Funcionários")

conn = get_connection()
c = conn.cursor()

# Cria a tabela caso não exista
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

# Formulário de Cadastro
with st.form("form_funcionario", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome")
    with col2:
        funcao = st.text_input("Função")
        
    btn_salvar = st.form_submit_button("➕ Adicionar Funcionário", use_container_width=True)

if btn_salvar:
    if nome.strip():
        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO funcionarios (nome, funcao, status) VALUES (?, ?, 'Ativo')", (nome.strip(), funcao.strip()))
            conn.commit()  # Salva permanentemente no banco
            st.success(f"Funcionário '{nome.strip()}' cadastrado com sucesso!")
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
    st.subheader(f"Quadro de Funcionários ({len(funcionarios)} cadastrados)")
    
    # Cabeçalho da Lista
    c_nome, c_func, c_stat, c_acoes = st.columns([3, 3, 2, 3])
    c_nome.markdown("**Nome**")
    c_func.markdown("**Função**")
    c_stat.markdown("**Status**")
    c_acoes.markdown("**Ações**")
    st.divider()

    for f in funcionarios:
        col_n, col_f, col_s, col_b = st.columns([3, 3, 2, 3])
        
        col_n.write(f"**{f['nome']}**")
        col_f.write(f["funcao"] or "-")
        
        status_atual = f.get('status', 'Ativo') or 'Ativo'
        col_s.write("🟢 Ativo" if status_atual == "Ativo" else "🔴 Inativo")
        
        # Botões de Ação (Alterar Status e Excluir)
        btn_col1, btn_col2 = col_b.columns(2)
        
        novo_status = "Inativo" if status_atual == "Ativo" else "Ativo"
        if btn_col1.button("Status", key=f"btn_st_func_{f['id']}", use_container_width=True):
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE funcionarios SET status = ? WHERE id = ?", (novo_status, f["id"]))
            conn.commit()
            conn.close()
            st.rerun()

        if btn_col2.button("🗑️ Excluir", key=f"btn_del_func_{f['id']}", use_container_width=True):
            conn = get_connection()
            c = conn.cursor()
            c.execute("DELETE FROM funcionarios WHERE id = ?", (f["id"],))
            conn.commit()
            conn.close()
            st.rerun()
else:
    st.info("Nenhum funcionário cadastrado no momento.")
