import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database.db import init_db, verify_pin, DB_PATH, get_connection

st.set_page_config(page_title="Almoxarifado", page_icon="📦", layout="wide")

if not os.path.exists(DB_PATH):
    init_db()

# ---------------------------------------------------------------------
# CONSULTA PÚBLICA VIA QR CODE (SEM NECESSIDADE DE LOGIN)
# ---------------------------------------------------------------------
query_params = st.query_params

if "p" in query_params:
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    codigo_prod = query_params["p"]
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT codigo, nome, estoque_atual, unidade, preco_unitario FROM produtos WHERE codigo = ?", (codigo_prod,))
    produto = c.fetchone()
    conn.close()

    st.title("📦 Consulta de Estoque")
    st.caption("Almoxarifado - Oficina")
    st.divider()
    
    if produto:
        st.success("✅ Produto Localizado")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Nome do Produto", value=produto["nome"])
            st.metric(label="Código", value=produto["codigo"])
        with col2:
            st.metric(label="Estoque Disponível", value=f"{produto['estoque_atual']} {produto['unidade']}")
            
            # Exibe o valor unitário caso exista
            if "preco_unitario" in produto.keys() and produto["preco_unitario"]:
                st.metric(label="Valor Unitário", value=f"R$ {produto['preco_unitario']:.2f}")
    else:
        st.error(f"❌ Produto com código '{codigo_prod}' não foi encontrado no sistema.")
    
    st.stop()  # Interrompe a execução para não exibir o painel do sistema

# ---------------------------------------------------------------------
# ESTILIZAÇÃO DO MENU SUPERIOR (ABAS)
# ---------------------------------------------------------------------
st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none !important; }
        
        div[role="radiogroup"] {
            flex-direction: row !important;
            flex-wrap: wrap;
            gap: 8px;
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
# BARRA LATERAL (USUÁRIO E LOGOUT)
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

# ---------------------------------------------------------------------
# MENU SUPERIOR EM ABAS
# ---------------------------------------------------------------------
opcoes_menu = [
    "🏠 Dashboard", "📱 Nova Saída", "📥 Nova Entrada", 
    "📦 Produtos", "👷 Funcionários", "🚗 Veículos", 
    "📋 Requisições", "📊 Relatórios", "🏷️ QR Codes"
]

if usuario.get("role") == "admin":
    opcoes_menu.append("🔐 Usuários")

opcao_selecionada = st.radio("Navegação", opcoes_menu, label_visibility="collapsed")
st.divider()

# Mapeamento do nome do botão para o caminho exato do arquivo na pasta views
mapa_arquivos = {
    "🏠 Dashboard": "views/dashboard.py",
    "📱 Nova Saída": "views/nova_saida.py",
    "📥 Nova Entrada": "views/entrada.py",
    "📦 Produtos": "views/produtos.py",
    "👷 Funcionários": "views/funcionarios.py",
    "🚗 Veículos": "views/veiculos.py",
    "📋 Requisições": "views/requisicoes.py",
    "📊 Relatórios": "views/relatorios.py",
    "🏷️ QR Codes": "views/qrcodes.py",
    "🔐 Usuários": "views/usuarios.py"
}

# ---------------------------------------------------------------------
# EXECUÇÃO DIRETA DO ARQUIVO SELECIONADO
# ---------------------------------------------------------------------
caminho_arquivo = mapa_arquivos.get(opcao_selecionada)

if caminho_arquivo and os.path.exists(caminho_arquivo):
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        codigo = f.read()
    
    # Executa o arquivo da view dentro do contexto do app principal
    exec(compile(codigo, caminho_arquivo, "exec"))
else:
    st.error(f"O arquivo `{caminho_arquivo}` não foi encontrado na pasta `views/`.")
