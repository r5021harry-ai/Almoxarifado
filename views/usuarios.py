import streamlit as st
import pandas as pd
from database.db import get_connection

usuario_logado = st.session_state.get("usuario", {})

# Proteção adicional de acesso (apenas Administrador)
if usuario_logado.get("role") != "admin":
    st.error("⛔ Acesso negado. Apenas administradores podem gerenciar usuários.")
    st.stop()

st.markdown("## 🔐 Gerenciamento de Usuários")

tab_listar, tab_cadastrar = st.tabs(["📋 Usuários Cadastrados", "➕ Novo Usuário"])

# ---------------------------------------------------------------------
# ABA 1: LISTAR E EXCLUIR USUÁRIOS
# ---------------------------------------------------------------------
with tab_listar:
    conn = get_connection()
    df_usuarios = pd.read_sql_query("SELECT id, username, nome, role FROM usuarios ORDER BY nome", conn)
    conn.close()

    if df_usuarios.empty:
        st.info("Nenhum usuário encontrado.")
    else:
        st.markdown("### Lista de Usuários do Sistema")
        
        # Cabeçalho da tabela
        col_hdr = st.columns([1.5, 3, 2, 1])
        col_hdr[0].markdown("**Usuário**")
        col_hdr[1].markdown("**Nome Completo**")
        col_hdr[2].markdown("**Perfil / Permissão**")
        col_hdr[3].markdown("**Ação**")

        st.divider()

        for user in df_usuarios.to_dict('records'):
            cols = st.columns([1.5, 3, 2, 1])
            cols[0].write(f"`{user['username']}`")
            cols[1].write(user['nome'])
            cols[2].write("⚙️ Administrador" if user['role'] == "admin" else "👤 Operador")

            # Evita que o admin apague a própria conta em uso
            if user['username'] == usuario_logado.get('username'):
                cols[3].caption("Conta Atual")
            else:
                if cols[3].button("🗑️ Excluir", key=f"btn_del_user_{user['id']}", help="Excluir usuário"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM usuarios WHERE id = ?", (user['id'],))
                    conn.commit()
                    conn.close()
                    st.toast(f"Usuário '{user['username']}' excluído com sucesso!", icon="🗑️")
                    st.rerun()

# ---------------------------------------------------------------------
# ABA 2: CADASTRAR NOVO USUÁRIO
# ---------------------------------------------------------------------
with tab_cadastrar:
    st.markdown("### Cadastrar Novo Acesso")
    with st.form("form_novo_usuario"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome Completo *")
            username = st.text_input("Nome de Usuário (Login) *")
        with col2:
            pin = st.text_input("PIN (Senha numéricas/texto) *", type="password")
            role = st.selectbox("Perfil de Acesso", ["operador", "admin"], format_func=lambda x: "⚙️ Administrador" if x == "admin" else "👤 Operador")

        salvar_usr = st.form_submit_button("💾 Salvar Usuário", use_container_width=True)

        if salvar_usr:
            if not nome.strip() or not username.strip() or not pin.strip():
                st.error("Todos os campos obrigatórios devem ser preenchidos.")
            else:
                conn = get_connection()
                c = conn.cursor()
                try:
                    c.execute("""
                        INSERT INTO usuarios (username, nome, pin, role)
                        VALUES (?, ?, ?, ?)
                    """, (username.strip(), nome.strip(), pin.strip(), role))
                    conn.commit()
                    st.success(f"Usuário '{username.strip()}' criado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar usuário (o nome de usuário já pode existir): {e}")
                finally:
                    conn.close()
