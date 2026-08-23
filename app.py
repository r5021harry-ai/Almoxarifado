import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database.db import init_db, verify_pin, DB_PATH

# Configuração da página
st.set_page_config(page_title="Almoxarifado", page_icon="📦", layout="wide")

if not os.path.exists(DB_PATH):
    init_db()

# Esconde qualquer menu automático da barra lateral
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
        }
        .block-container {
            padding-top: 2rem !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------
# GERENCIAMENTO DE SESSÃO / LOGIN
# ---------------------------------------------------------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

# SE NÃO ESTIVER LOGADO, MOSTRA APENAS A TELA DE LOGIN
if st.session_state.usuario is None:
    # Oculta a sidebar na tela de login
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
    
    # Interrompe a execução para impedir exibição das abas sem autenticação
    st.stop()

# ---------------------------------------------------------------------
# USUÁRIO LOGADO — IMPORTS DAS VIEWS
# ---------------------------------------------------------------------
from views import (
    dashboard, nova_saida, entrada, produtos,
    funcionarios, veiculos, requisicoes, relatorios, qrcodes
)

try:
    from views import usuarios
except ImportError:
    usuarios = None

usuario = st.session_state.usuario

# Barra Lateral (Apenas Perfil e Logout)
with st.sidebar:
    st.markdown("### 📦 **Almoxarifado**")
    st.divider()
    st.markdown("**Conectado como:**")
    st.markdown(f"### `{usuario.get('nome', 'Usuário')}`")
    st.caption(f"Perfil: {usuario.get('role', 'user')}")
    st.write("")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.usuario = None
        st.rerun()

# ---------------------------------------------------------------------
# PAINEL PRINCIPAL COM NAVEGAÇÃO EM ABAS
# ---------------------------------------------------------------------
titulos_abas = [
    "🏠 Dashboard",
    "📱 Nova Saída",
    "📥 Nova Entrada",
    "📦 Produtos",
    "👷 Funcionários",
    "🚗 Veículos",
    "📋 Requisições",
    "📊 Relatórios / Excel",
    "🏷️ QR Codes"
]

is_admin = usuario.get("role") == "admin"
if is_admin:
    titulos_abas.append("🔐 Usuários")

abas = st.tabs(titulos_abas)

def executar_view(modulo):
    if hasattr(modulo, 'render'):
        modulo.render()
    elif hasattr(modulo, 'main'):
        modulo.main()

with abas[0]:
    executar_view(dashboard)

with abas[1]:
    executar_view(nova_saida)

with abas[2]:
    executar_view(entrada)

with abas[3]:
    executar_view(produtos)

with abas[4]:
    executar_view(funcionarios)

with abas[5]:
    executar_view(veiculos)

with abas[6]:
    executar_view(requisicoes)

with abas[7]:
    executar_view(relatorios)

with abas[8]:
    executar_view(qrcodes)

if is_admin and len(abas) > 9:
    with abas[9]:
        if usuarios:
            executar_view(usuarios)
