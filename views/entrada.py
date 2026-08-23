import datetime as dt
import streamlit as st
from database.db import get_connection

st.markdown("## 📥 Nova Entrada")
st.caption("Entrada de material — disponível apenas no ambiente administrativo.")

conn = get_connection()
c = conn.cursor()

# Descobre quais colunas existem na tabela 'produtos' para evitar erros de SQL
c.execute("PRAGMA table_info(produtos)")
colunas = [col[1] for col in c.fetchall()]

col_qtd = "estoque" if "estoque" in colunas else ("qtd" if "qtd" in colunas else "quantidade")
col_unidade = "unidade" if "unidade" in colunas else "un"

# Busca os produtos com a coluna correta
try:
    c.execute(f"SELECT id, codigo, nome, {col_unidade}, {col_qtd} FROM produtos ORDER BY nome ASC")
    produtos = c.fetchall()
except Exception as e:
    produtos = []
    st.error(f"Erro ao carregar produtos: {e}")

conn.close()

if not produtos:
    st.warning("Nenhum produto cadastrado para dar entrada.")
    st.stop()

# Monta as opções para o dropdown
opcoes_produtos = {
    f"{p['nome']} ({p['codigo'] or 'S/C'}) — estoque atual: {p[col_qtd]} {p[col_unidade] or 'UN'}": p['id']
    for p in produtos
}

produto_selecionado = st.selectbox("Produto", list(opcoes_produtos.keys()))

with st.form("form_entrada"):
    quantidade = st.number_input("Quantidade recebida", min_value=0.01, step=1.0, value=1.0)
    fornecedor = st.text_input("Fornecedor")
    valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, step=0.01, value=0.0, format="%.2f")
    observacao = st.text_input("Observação")
    
    btn_confirmar = st.form_submit_button("📥 Confirmar Entrada", use_container_width=True)

if btn_confirmar:
    produto_id = opcoes_produtos[produto_selecionado]
    data_hora = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usuario_nome = st.session_state.usuario.get("nome", "Administrador") if st.session_state.get("usuario") else "Sistema"

    # Junta fornecedor e valor unitário na observação da movimentação
    obs_completa = f"Fornecedor: {fornecedor.strip()} | Valor Un.: R$ {valor_unitario:.2f}"
    if observacao.strip():
        obs_completa += f" | Obs: {observacao.strip()}"

    conn = get_connection()
    c = conn.cursor()

    try:
        # Atualiza a quantidade do produto no banco usando o nome correto da coluna
        c.execute(f"UPDATE produtos SET {col_qtd} = {col_qtd} + ? WHERE id = ?", (quantidade, produto_id))
        
        # Registra a movimentação
        c.execute("""
            INSERT INTO movimentacoes (produto_id, tipo, quantidade, usuario, observacao, data_hora)
            VALUES (?, 'ENTRADA', ?, ?, ?, ?)
        """, (produto_id, quantidade, usuario_nome, obs_completa, data_hora))
        
        conn.commit()
        st.success("Entrada de estoque registrada com sucesso!")
        st.rerun()
    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao registrar entrada: {e}")
    finally:
        conn.close()
