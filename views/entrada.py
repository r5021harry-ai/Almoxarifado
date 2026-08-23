import datetime as dt
import streamlit as st
from database.db import get_connection

st.markdown("## 📥 Nova Entrada")
st.caption("Entrada de material — disponível apenas no ambiente administrativo.")

conn = get_connection()
c = conn.cursor()

# Busca todos os produtos do banco
try:
    c.execute("SELECT * FROM produtos ORDER BY nome ASC")
    rows = c.fetchall()
    # Converte os registros para dicionários padronizados independente do driver SQLite
    produtos = [dict(row) for row in rows]
except Exception as e:
    produtos = []
    st.error(f"Erro ao carregar produtos: {e}")
finally:
    conn.close()

if not produtos:
    st.warning("Nenhum produto cadastrado para dar entrada.")
    st.stop()

# Identifica dinamicamente os nomes das colunas no seu banco
primeiro_prod = produtos[0]
col_qtd = next((k for k in ['quantidade', 'estoque', 'qtd'] if k in primeiro_prod), None)
col_unidade = next((k for k in ['unidade', 'un'] if k in primeiro_prod), None)

# Monta o dicionário de opções para o dropdown
opcoes_produtos = {}
for p in produtos:
    nome = p.get('nome', 'Sem nome')
    codigo = p.get('codigo') or 'S/C'
    qtd = p.get(col_qtd, 0) if col_qtd else 0
    unidade = p.get(col_unidade, 'UN') if col_unidade else 'UN'
    
    label = f"{nome} ({codigo}) — estoque atual: {qtd} {unidade}"
    opcoes_produtos[label] = p['id']

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

    # Monta o histórico na observação com o Valor Unitário e Fornecedor
    obs_completa = f"Fornecedor: {fornecedor.strip()} | Valor Un.: R$ {valor_unitario:.2f}"
    if observacao.strip():
        obs_completa += f" | Obs: {observacao.strip()}"

    conn = get_connection()
    c = conn.cursor()

    try:
        # Atualiza a quantidade do estoque dinamicamente
        c.execute(f"UPDATE produtos SET {col_qtd} = {col_qtd} + ? WHERE id = ?", (quantidade, produto_id))
        
        # Registra a movimentação de ENTRADA
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
