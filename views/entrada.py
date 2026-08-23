import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from database.db import get_connection
from services.requisicao_service import registrar_entrada

if st.session_state.get("usuario") is None:
    st.warning("Faça login primeiro na página inicial.")
    st.stop()

usuario = st.session_state.usuario
st.title("📥 Nova Entrada")
st.caption("Entrada de material — disponível apenas no ambiente administrativo.")

conn = get_connection()
produtos = conn.execute("SELECT * FROM produtos WHERE status='Ativo' ORDER BY nome").fetchall()
conn.close()

if not produtos:
    st.warning("Nenhum produto cadastrado ainda.")
    st.stop()

nomes = [f"{p['nome']} ({p['codigo']}) — estoque atual: {p['estoque_atual']:g} {p['unidade']}" for p in produtos]
idx = st.selectbox("Produto", range(len(produtos)), format_func=lambda i: nomes[i], index=None,
                    placeholder="Buscar produto...")

if idx is not None:
    produto = dict(produtos[idx])
    with st.form("form_entrada"):
        quantidade = st.number_input(f"Quantidade recebida ({produto['unidade']})", min_value=0.01, step=1.0)
        fornecedor = st.text_input("Fornecedor")
        nota_fiscal = st.text_input("Nota fiscal")
        observacao = st.text_area("Observação", height=80)
        confirmar = st.form_submit_button("📥 Confirmar Entrada", type="primary", use_container_width=True)

    if confirmar:
        resultado = registrar_entrada(produto["id"], quantidade, usuario["id"], fornecedor, nota_fiscal, observacao)
        if resultado["sucesso"]:
            st.success(
                f"Entrada registrada! Estoque de **{produto['nome']}**: "
                f"{produto['estoque_atual']:g} → **{resultado['estoque_posterior']:g}** {produto['unidade']}"
            )
        else:
            st.error(f"Erro: {resultado['erro']}")

st.divider()
st.subheader("Últimas entradas")
conn = get_connection()
rows = conn.execute("""
    SELECT m.data, m.hora, p.nome AS produto, m.quantidade, m.fornecedor, m.nota_fiscal
    FROM movimentacoes m JOIN produtos p ON p.id = m.produto_id
    WHERE m.tipo = 'ENTRADA' ORDER BY m.id DESC LIMIT 15
""").fetchall()
conn.close()
if rows:
    import pandas as pd
    st.dataframe(pd.DataFrame([dict(r) for r in rows]), use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma entrada registrada ainda.")
