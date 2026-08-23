import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database.db import init_db, verify_pin, DB_PATH

st.set_page_config(page_title="Almoxarifado", page_icon="📦", layout="wide")

if not os.path.exists(DB_PATH):
    init_db()

# CSS para esconder a sidebar nativa e criar o menu superior
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        div[role="radiogroup"] { flex-direction: row !important; justify-content: flex-start; }
        div[role="radiogroup"] label {
            background-color: #1e293b;
            padding: 8px 16px;
            border-radius: 6px;
            margin-right: 8px;
            border: 1px solid #334155;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------
# LOGIN
# ---------------------------------------------------------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.title("📦 Almoxarifado")
        st.subheader("Acesso ao Sistema")
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
    st.stop()

# ---------------------------------------------------------------------
# LOGADO - BARRA LATERAL (LOGOUT) E MENU SUPERIOR DE OPÇÕES
# ---------------------------------------------------------------------
usuario = st.session_state.usuario

with st.sidebar:
    st.markdown("### 📦 **Almoxarifado**")
    st.divider()
    st.markdown(f"**Conectado como:**")
    st.markdown(f"### `{usuario.get('nome', 'Usuário')}`")
    st.caption(f"Perfil: {usuario.get('role', 'user')}")
    st.write("")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario = None
        st.rerun()

# Lista de opções do menu superior
opcoes = [
    "🏠 Dashboard", "📱 Nova Saída", "📥 Nova Entrada", 
    "📦 Produtos", "👷 Funcionários", "🚗 Veículos", 
    "📋 Requisições", "📊 Relatórios", "🏷️ QR Codes"
]

if usuario.get("role") == "admin":
    opcoes.append("🔐 Usuários")

# Menu de Seleção em Botões Superiores
opcao_selecionada = st.radio("Navegação", opcoes, label_visibility="collapsed")

st.divider()

# ---------------------------------------------------------------------
# CARREGAMENTO DA VIEW SELECIONADA
# ---------------------------------------------------------------------
from views import (
    dashboard, nova_saida, entrada, produtos,
    funcionarios, veiculos, requisicoes, relatorios, qrcodes
)

try:
    from views import usuarios
except ImportError:
    usuarios = None

def renderizar(modulo):
    if hasattr(modulo, 'render'):
        modulo.render()
    elif hasattr(modulo, 'main'):
        modulo.main()

if opcao_selecionada == "🏠 Dashboard":
    renderizar(dashboard)
elif opcao_selecionada == "📱 Nova Saída":
    renderizar(nova_saida)
elif opcao_selecionada == "📥 Nova Entrada":
    renderizar(entrada)
elif opcao_selecionada == "📦 Produtos":
    renderizar(produtos)
elif opcao_selecionada == "👷 Funcionários":
    renderizar(funcionarios)
elif opcao_selecionada == "🚗 Veículos":
    renderizar(veiculos)
elif opcao_selecionada == "📋 Requisições":
    renderizar(requisicoes)
elif opcao_selecionada == "📊 Relatórios":
    renderizar(relatorios)
elif opcao_selecionada == "🏷️ QR Codes":
    renderizar(qrcodes)
elif opcao_selecionada == "🔐 Usuários" and usuarios:
    renderizar(usuarios)
