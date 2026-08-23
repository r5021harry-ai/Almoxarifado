import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from database.db import get_connection

if st.session_state.get("usuario") is None:
    st.warning("Faça login primeiro na página inicial.")
    st.stop()

st.title("🚗 Veículos")

conn = get_connection()

tab_cadastro, tab_historico = st.tabs(["📋 Cadastro", "📜 Histórico por placa"])

with tab_cadastro:
    with st.form("novo_veic"):
        placa = st.text_input("Placa")
        add = st.form_submit_button("➕ Adicionar", type="primary")
    if add:
        if placa:
            existe = conn.execute("SELECT id FROM veiculos WHERE placa=?", (placa.upper(),)).fetchone()
            if existe:
                st.error("Placa já cadastrada.")
            else:
                conn.execute("INSERT INTO veiculos (placa, status) VALUES (?,'Ativo')", (placa.upper(),))
                conn.commit()
                st.success(f"{placa.upper()} cadastrada.")
                st.rerun()
        else:
            st.error("Informe a placa.")

    st.divider()
    veiculos = conn.execute("SELECT * FROM veiculos ORDER BY placa").fetchall()
    for v in veiculos:
        c1, c2, c3 = st.columns([4, 2, 2])
        c1.write(v["placa"])
        c2.write(v["status"])
        novo_status = "Inativo" if v["status"] == "Ativo" else "Ativo"
        if c3.button(f"Marcar {novo_status}", key=f"veic_{v['id']}"):
            conn.execute("UPDATE veiculos SET status=? WHERE id=?", (novo_status, v["id"]))
            conn.commit()
            st.rerun()

with tab_historico:
    veiculos = conn.execute("SELECT * FROM veiculos ORDER BY placa").fetchall()
    placas = [v["placa"] for v in veiculos]
    placa_sel = st.selectbox("Placa", [""] + placas)
    if placa_sel:
        rows = conn.execute("""
            SELECT r.numero, r.data, r.hora, p.nome AS produto, ri.quantidade, p.unidade,
                   f.nome AS solicitante
            FROM requisicoes r
            JOIN veiculos v ON v.id = r.veiculo_id
            JOIN requisicao_itens ri ON ri.requisicao_id = r.id
            JOIN produtos p ON p.id = ri.produto_id
            JOIN funcionarios f ON f.id = r.funcionario_id
            WHERE v.placa = ? AND r.status = 'Confirmada'
            ORDER BY r.data DESC, r.hora DESC
        """, (placa_sel,)).fetchall()

        if rows:
            df = pd.DataFrame([dict(r) for r in rows])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.metric("Total de itens retirados", df["quantidade"].sum())
        else:
            st.info("Nenhuma retirada registrada para esta placa ainda.")

conn.close()
