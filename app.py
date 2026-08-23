import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database.db import init_db, verify_pin, DB_PATH

st.set_page_config(page_title="Almoxarifado", page_icon="📦", layout="wide")

if not os.path.exists(DB_PATH):
    init_db()

# Customização Visual das Abas no Topo
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        
        /* Modifica o radio button para parecer abas / botões */
        div[role="radiogroup"] {
            flex-direction: row !important;
            flex-wrap: wrap;
            gap: 10px;
        }
        div[role="radiogroup"] label {
            background-color: #1e293b !important;
            padding: 8px 16px !important;
            border-radius: 8px !important;
            border: 1px solid #334155 !important;
            cursor: pointer;
        }
        div[role="radiogroup"] label:hover {
            border-color: #60a5fa !important;
        }
        /* Esconde o círculo do radio button */
        div[role="radiogroup"] label div[data-testid="stMarkdownContainer"] {
            font-weight: 500;
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
# BARRA LATERAL & MÓDULOS
# ---------------------------------------------------------------------
usuario = st.session_state.usuario

with st.sidebar:
    st.markdown("### 📦 **Almoxarifado**")
    st.divider()
    st.markdown("**Conectado como:**")
    st.markdown(f"### `{usuario.get('nome', 'Administrador')}`")
    st.caption(f"Perfil: {usuario.get('role', 'admin')}")
    st.write("")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario = None
        st.rerun()

opcoes_menu = [
    "🏠 Dashboard", "📱 Nova Saída", "📥 Nova Entrada", 
    "📦 Produtos", "👷 Funcionários", "🚗 Veículos", 
    "📋 Requisições", "📊 Relatórios", "🏷️ QR Codes"
]

if usuario.get("role") == "admin":
    opcoes_menu.append("🔐 Usuários")

# Renderização do Menu Superior
opcao_selecionada = st.radio("Navegação", opcoes_menu, label_visibility="collapsed")
st.divider()

# ---------------------------------------------------------------------
# EXECUÇÃO DA VIEW SELECIONADA
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

mapa_views = {
    "🏠 Dashboard": dashboard,
    "📱 Nova Saída": nova_saida,
    "📥 Nova Entrada": entrada,
    "📦 Produtos": produtos,
    "👷 Funcionários": funcionarios,
    "🚗 Veículos": veiculos,
    "📋 Requisições": requisicoes,
    "📊 Relatórios": relatorios,
    "🏷️ QR Codes": qrcodes,
    "🔐 Usuários": usuarios
}

if opcao_selecionada in mapa_views and mapa_views[opcao_selecionada]:
    renderizar(mapa_views[opcao_selecionada])
