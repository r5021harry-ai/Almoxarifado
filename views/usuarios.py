import streamlit as st
import secrets
from database.db import get_connection, hash_pin

st.markdown("## 🔐 Gestão de Usuários")

with st.form("form_usuario", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome Completo")
        username = st.text_input("Nome de Usuário (Login)")
    with col2:
        pin = st.text_input("PIN (Senha Numérica)", type="password")
        role = st.selectbox("Perfil de Acesso", ["almoxarife", "admin"])
        
    btn_salvar = st.form_submit_button("➕ Criar Usuário", use_container_width=True)

if btn_salvar:
    if nome.strip() and username.strip() and pin.strip():
        conn = get_connection()
        c = conn.cursor()
        
        # Criptografa o PIN
        salt = secrets.token_hex(8)
        pin_hashed = hash_pin(pin.strip(), salt)
        stored_hash = f"{salt}${pin_hashed}"
        
        try:
            c.execute(
                "INSERT INTO usuarios (nome, username, pin_hash, role, status) VALUES (?, ?, ?, ?, 'Ativo')",
                (nome.strip(), username.strip().lower(), stored_hash, role)
            )
            conn.commit()
            st.success(f"Usuário '{username}' cadastrado com sucesso!")
            st.rerun()
        except Exception as e:
            conn.rollback()
            if "UNIQUE" in str(e):
                st.error(f"O usuário '{username}' já existe. Escolha outro login.")
            else:
                st.error(f"Erro ao salvar usuário: {e}")
        finally:
            conn.close()
    else:
        st.warning("Preencha todos os campos do formulário.")

st.markdown("---")

# Listagem dos Usuários
conn = get_connection()
c = conn.cursor()
c.execute("SELECT id, nome, username, role, status FROM usuarios ORDER BY id DESC")
usuarios = [dict(r) for r in c.fetchall()]
conn.close()

if usuarios:
    for u in usuarios:
        col_n, col_u, col_r, col_s, col_b = st.columns([3, 2, 2, 2, 2])
        col_n.write(u["nome"])
        col_u.write(f"`{u['username']}`")
        col_r.write(u["role"])
        col_s.write(u["status"])
        
        novo_status = "Inativo" if u["status"] == "Ativo" else "Ativo"
        if col_b.button(f"Marcar {novo_status}", key=f"btn_usr_{u['id']}"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE usuarios SET status = ? WHERE id = ?", (novo_status, u["id"]))
            conn.commit()
            conn.close()
            st.rerun()
else:
    st.info("Nenhum usuário cadastrado.")
