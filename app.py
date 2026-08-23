import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database.db import init_db, verify_pin, DB_PATH

# Importa as views diretamente
from views import (
    dashboard, nova_saida, entrada, produtos,
    funcionarios, veiculos, requisicoes, relatorios, qrcodes
)

# Tenta importar usuários se existir
try:
    from views import usuarios
except ImportError:
    usuarios = None

st.set_page_config(page_title="Almoxarifado", page_icon="📦", layout="wide")

if not os.path.exists(DB_PATH):
    init_db()

# Esconde o menu nativo do Streamlit na barra lateral
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {
            display: none !important;
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
# BARRA LATERAL (APENAS PERFIL E LOGOUT)
# ---------------------------------------------------------------------
usuario = st.session_state.usuario

with st.sidebar:
    st.markdown(f"**{usuario['nome']}**")
    st.caption(f"Perfil: {usuario['role']}")
    if st.button("Sair", use_container_width=True):
        st.session_state.usuario = None
        st.rerun()

# ---------------------------------------------------------------------
# NAVEGAÇÃO SUPERIOR EM ABAS
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

# Roteamento dos arquivos das views nas abas
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
