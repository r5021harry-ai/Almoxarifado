import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import datetime as dt
import streamlit as st
from database.db import get_connection

if st.session_state.get("usuario") is None:
    st.warning("Faça login primeiro na página inicial.")
    st.stop()

st.title("📦 Dashboard")

conn = get_connection()
hoje = dt.date.today().strftime("%Y-%m-%d")

col1, col2, col3, col4 = st.columns(4)
total_produtos = conn.execute("SELECT COUNT(*) n FROM produtos WHERE status='Ativo'").fetchone()["n"]
sem_estoque = conn.execute("SELECT COUNT(*) n FROM produtos WHERE status='Ativo' AND estoque_atual<=0").fetchone()["n"]
abaixo_minimo = conn.execute(
    "SELECT COUNT(*) n FROM produtos WHERE status='Ativo' AND estoque_minimo>0 AND estoque_atual<estoque_minimo"
).fetchone()["n"]
saidas_hoje = conn.execute(
    "SELECT COUNT(*) n FROM movimentacoes WHERE tipo='SAIDA' AND data=?", (hoje,)
).fetchone()["n"]

col1.metric("Produtos cadastrados", total_produtos)
col2.metric("Sem estoque", sem_estoque)
col3.metric("Abaixo do mínimo", abaixo_minimo)
col4.metric("Saídas hoje (itens)", saidas_hoje)

st.divider()
st.subheader("Últimas movimentações")
rows = conn.execute("""
    SELECT m.data, m.hora, p.nome AS produto, m.tipo, m.quantidade
    FROM movimentacoes m JOIN produtos p ON p.id = m.produto_id
    ORDER BY m.id DESC LIMIT 15
""").fetchall()
if rows:
    import pandas as pd
    df = pd.DataFrame([dict(r) for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Nenhuma movimentação registrada ainda.")

conn.close()

st.divider()
st.info(
    "📱 **Dica:** no celular, acesse este mesmo endereço pela rede Wi-Fi e use "
    "diretamente **Nova Saída** para retiradas rápidas com QR Code."
)
