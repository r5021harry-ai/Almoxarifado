import sys, os, sqlite3, openpyxl, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from database.db import init_db, verify_pin, DB_PATH, get_connection

st.set_page_config(page_title="Almoxarifado", page_icon="📦", layout="wide")

if not os.path.exists(DB_PATH):
    init_db()

# ---------------------------------------------------------------------
# CARREGAMENTO E ATUALIZAÇÃO DAS BASES (PRODUTOS E FROTA)
# ---------------------------------------------------------------------
def atualizar_bases_dados():
    if not os.path.exists(DB_PATH):
        return
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. ATUALIZAR PRODUTOS (Remove a base antiga e cadastra o novo PDF 286.pdf)
    pdf_path = os.path.join("dados", "286.pdf")
    if os.path.exists(pdf_path):
        try:
            import pypdf
            # Apaga toda a base antiga de produtos
            c.execute("DELETE FROM produtos;")
            
            reader = pypdf.PdfReader(pdf_path)
            for page in reader.pages:
                texto = page.extract_text()
                if texto:
                    for line in texto.splitlines():
                        m = re.match(r'^(\d{2,6})(.+?)\s+(\d+UN|\d+BL|\d+PT|\d+LT|\d+KG|1|UN|BL|PT|KG|LT|1 PT)\s+([\d\.\,]+)\s+([\d\.\,]+)\s*(UN|BL|PT|KG|LT)?\s*2$', line.strip())
                        if m:
                            codigo = m.group(1).strip()
                            nome = m.group(2).strip()
                            estoque = float(m.group(4).replace('.','').replace(',','.'))
                            preco = float(m.group(5).replace('.','').replace(',','.'))
                            unidade = m.group(6) or "UN"
                            
                            c.execute("""
                                INSERT INTO produtos (codigo, nome, estoque_atual, preco_unitario, unidade)
                                VALUES (?, ?, ?, ?, ?)
                            """, (codigo, nome, estoque, preco, unidade))
        except Exception as e:
            print(f"Erro ao importar PDF de produtos: {e}")

    # 2. ATUALIZAR VEÍCULOS (Lê exatamente o layout do arquivo FROTA.xlsx)
    excel_path = os.path.join("dados", "FROTA.xlsx")
    if os.path.exists(excel_path):
        try:
            wb = openpyxl.load_workbook(excel_path)
            sheet = wb.active
            for row in sheet.iter_rows(min_row=2, values_only=True):
                # Estrutura: Col 0: PLACA | Col 1: PROPRIEDADE | Col 2: RENAVAM | Col 3: CHASSI | Col 4: MODELO
                if row and row[0]:
                    placa = str(row[0]).strip().upper()
                    propriedade = str(row[1] or '').strip()
                    renavam = str(row[2] or '').strip()
                    chassi = str(row[3] or '').strip()
                    modelo = str(row[4] or '').strip()
                    
                    c.execute("""
                        INSERT OR REPLACE INTO veiculos (placa, modelo, renavam, chassi, propriedade, status)
                        VALUES (?, ?, ?, ?, ?, 'Ativo')
                    """, (placa, modelo, renavam, chassi, propriedade))
        except Exception as e:
            print(f"Erro ao importar Excel da frota: {e}")
            
    conn.commit()
    conn.close()

# Executa o carregamento das bases
atualizar_bases_dados()

# ---------------------------------------------------------------------
# CONSULTA PÚBLICA VIA QR CODE
# ---------------------------------------------------------------------
query_params = st.query_params

if "p" in query_params:
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    codigo_prod = str(query_params["p"]).strip()
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT codigo, nome, estoque_atual, unidade, preco_unitario FROM produtos WHERE CAST(codigo AS TEXT) = ?", (codigo_prod,))
    produto = c.fetchone()
    conn.close()

    st.title("📦 Consulta de Estoque")
    st.caption("Almoxarifado - Oficina")
    st.divider()
    
    if produto:
        st.success("✅ Produto Encontrado")
        st.subheader(f"**{produto['nome']}**")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Código do Produto", value=produto["codigo"])
            st.metric(label="Estoque Disponível", value=f"{produto['estoque_atual']} {produto['unidade']}")
        with col2:
            val_un = produto['preco_unitario'] if produto['preco_unitario'] else 0.0
            st.metric(label="Valor Unitário", value=f"R$ {val_un:.2f}")
    else:
        st.error(f"❌ Produto com o código '{codigo_prod}' não foi localizado.")
    st.stop()

# ---------------------------------------------------------------------
# ESTILIZAÇÃO DA INTERFACE
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
        .login-header {
            text-align: center;
            margin-bottom: 24px;
        }
        .login-header h1 {
            font-size: 2.2rem;
            margin-bottom: 4px;
        }
        .login-header p {
            color: #94a3b8;
            font-size: 1rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------------------
# AUTENTICAÇÃO E LOGIN
# ---------------------------------------------------------------------
if "usuario" not in st.session_state:
    st.session_state.usuario = None

if st.session_state.usuario is None:
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    st.write("")
    st.write("")
    
    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    
    with col_center:
        st.markdown(
            """
            <div class="login-header">
                <h1>📦 Almoxarifado</h1>
                <p>Acesso ao Sistema</p>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
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
# BARRA LATERAL
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
# NAVEGAÇÃO E ROTAS
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

caminho_arquivo = mapa_arquivos.get(opcao_selecionada)

if caminho_arquivo and os.path.exists(caminho_arquivo):
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        codigo = f.read()
    exec(compile(codigo, caminho_arquivo, "exec"))
else:
    st.error(f"O arquivo `{caminho_arquivo}` não foi encontrado na pasta `views/`.")
