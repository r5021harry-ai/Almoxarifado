import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from database.db import get_connection

if st.session_state.get("usuario") is None:
    st.warning("Faça login primeiro na página inicial.")
    st.stop()

st.title("👷 Funcionários")

conn = get_connection()

with st.form("novo_func"):
    c1, c2 = st.columns(2)
    nome = c1.text_input("Nome")
    funcao = c2.text_input("Função")
    add = st.form_submit_button("➕ Adicionar", type="primary")

if add:
    if nome:
        conn.execute("INSERT INTO funcionarios (nome, funcao, status) VALUES (?,?,'Ativo')", (nome, funcao))
        conn.commit()
        st.success(f"{nome} cadastrado.")
        st.rerun()
    else:
        st.error("Informe o nome.")

st.divider()
funcionarios = conn.execute("SELECT * FROM funcionarios ORDER BY nome").fetchall()
for f in funcionarios:
    c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
    c1.write(f["nome"])
    c2.write(f["funcao"])
    c3.write(f["status"])
    novo_status = "Inativo" if f["status"] == "Ativo" else "Ativo"
    if c4.button(f"Marcar {novo_status}", key=f"func_{f['id']}"):
        conn.execute("UPDATE funcionarios SET status=? WHERE id=?", (novo_status, f["id"]))
        conn.commit()
        st.rerun()

conn.close()
