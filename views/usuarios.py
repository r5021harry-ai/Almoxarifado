import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import secrets
import streamlit as st
from database.db import get_connection, hash_pin

if st.session_state.get("usuario") is None:
    st.warning("Faça login primeiro na página inicial.")
    st.stop()

if st.session_state.usuario["role"] != "admin":
    st.error("Apenas administradores podem gerenciar usuários.")
    st.stop()

st.title("🔐 Usuários")

conn = get_connection()

with st.form("novo_usuario"):
    c1, c2 = st.columns(2)
    nome = c1.text_input("Nome")
    username = c2.text_input("Usuário (login)")
    c3, c4 = st.columns(2)
    pin = c3.text_input("PIN", type="password")
    role = c4.selectbox("Perfil", ["almoxarife", "admin"])
    criar = st.form_submit_button("➕ Criar usuário", type="primary")

if criar:
    if not (nome and username and pin):
        st.error("Preencha todos os campos.")
    else:
        existe = conn.execute("SELECT id FROM usuarios WHERE username=?", (username,)).fetchone()
        if existe:
            st.error("Já existe um usuário com esse login.")
        else:
            salt = secrets.token_hex(8)
            pin_hash = hash_pin(pin, salt)
            conn.execute(
                "INSERT INTO usuarios (nome, username, pin_hash, role, status) VALUES (?,?,?,?,'Ativo')",
                (nome, username, f"{salt}${pin_hash}", role),
            )
            conn.commit()
            st.success(f"Usuário {username} criado.")
            st.rerun()

st.divider()
usuarios = conn.execute("SELECT * FROM usuarios ORDER BY nome").fetchall()
for u in usuarios:
    c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
    c1.write(f"{u['nome']} ({u['username']})")
    c2.write(u["role"])
    c3.write(u["status"])
    if u["username"] != "admin":
        novo_status = "Inativo" if u["status"] == "Ativo" else "Ativo"
        if c4.button(f"Marcar {novo_status}", key=f"user_{u['id']}"):
            conn.execute("UPDATE usuarios SET status=? WHERE id=?", (novo_status, u["id"]))
            conn.commit()
            st.rerun()

conn.close()
