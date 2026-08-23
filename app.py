import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database.db import init_db, verify_pin, DB_PATH

st.set_page_config(page_title="Almoxarifado", page_icon="📦", layout="wide")

if not os.path.exists(DB_PATH):
    init_db()

# ---------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.title("📦 Almoxarifado")
    st.subheader("Entrar")
    with st.form("login_form"):
        username = st.text_input("Usuário")
        pin = st.text_input("PIN", type="password")
        entrar = st.form_submit_button("Entrar", use_container_width=True)
    if entrar:
        user = verify_pin(username.strip(), pin.strip())
        if user:
            st.session_state.usuario = dict(user)
            st.rerun()
        else:
            st.error("Usuário ou PIN inválido.")
    st.caption("Usuário padrão: admin / PIN: 1234 (troque depois em Usuários).")
    st.stop()

# ---------------------------------------------------------------------
# LOGADO — monta a navegação (views) e roteia
# ---------------------------------------------------------------------
usuario = st.session_state.usuario

with st.sidebar:
    st.markdown(f"**{usuario['nome']}**")
    st.caption(f"Perfil: {usuario['role']}")
    if st.button("Sair", use_container_width=True):
        st.session_state.usuario = None
        st.rerun()
    st.divider()

paginas = [
    st.Page("views/dashboard.py", title="Dashboard", icon="🏠", default=True),
    st.Page("views/nova_saida.py", title="Nova Saída", icon="📱"),
    st.Page("views/entrada.py", title="Nova Entrada", icon="📥"),
    st.Page("views/produtos.py", title="Produtos", icon="📦"),
    st.Page("views/funcionarios.py", title="Funcionários", icon="👷"),
    st.Page("views/veiculos.py", title="Veículos", icon="🚗"),
    st.Page("views/requisicoes.py", title="Requisições", icon="📋"),
    st.Page("views/relatorios.py", title="Relatórios / Excel", icon="📊"),
    st.Page("views/qrcodes.py", title="QR Codes", icon="🏷️"),
]
if usuario["role"] == "admin":
    paginas.append(st.Page("views/usuarios.py", title="Usuários", icon="🔐"))

pg = st.navigation(paginas)
pg.run()
