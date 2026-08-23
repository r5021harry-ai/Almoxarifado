import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import datetime as dt
from database.db import get_connection

if st.session_state.get("usuario") is None:
    st.warning("Faça login primeiro na página inicial.")
    st.stop()

st.title("📋 Requisições")

conn = get_connection()

c1, c2 = st.columns(2)
data_inicio = c1.date_input("De", value=dt.date.today())
data_fim = c2.date_input("Até", value=dt.date.today())

reqs = conn.execute("""
    SELECT r.id, r.numero, r.data, r.hora, f.nome AS solicitante, f.funcao,
           v.placa AS veiculo, u.nome AS almoxarife, r.status,
           (SELECT COUNT(*) FROM requisicao_itens WHERE requisicao_id = r.id) AS n_itens
    FROM requisicoes r
    JOIN funcionarios f ON f.id = r.funcionario_id
    JOIN veiculos v ON v.id = r.veiculo_id
    JOIN usuarios u ON u.id = r.almoxarife_id
    WHERE r.data BETWEEN ? AND ?
    ORDER BY r.data DESC, r.hora DESC
""", (data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"))).fetchall()

st.caption(f"{len(reqs)} requisição(ões) no período")
df = pd.DataFrame([dict(r) for r in reqs])
if not df.empty:
    st.dataframe(df.drop(columns=["id"]), use_container_width=True, hide_index=True)

st.divider()
st.subheader("🔎 Detalhar requisição")
numeros = [r["numero"] for r in reqs]
num_sel = st.selectbox("Número da requisição", [""] + numeros)

if num_sel:
    req = conn.execute("""
        SELECT r.*, f.nome AS solicitante, f.funcao, v.placa AS veiculo, u.nome AS almoxarife
        FROM requisicoes r
        JOIN funcionarios f ON f.id = r.funcionario_id
        JOIN veiculos v ON v.id = r.veiculo_id
        JOIN usuarios u ON u.id = r.almoxarife_id
        WHERE r.numero = ?
    """, (num_sel,)).fetchone()
    itens = conn.execute("""
        SELECT p.codigo, p.nome, ri.quantidade, p.unidade
        FROM requisicao_itens ri JOIN produtos p ON p.id = ri.produto_id
        WHERE ri.requisicao_id = ?
    """, (req["id"],)).fetchall()

    st.markdown(f"### REQUISIÇÃO {req['numero']}")
    st.write(f"**Data:** {req['data']}  **Hora:** {req['hora']}")
    st.write(f"**Solicitante:** {req['solicitante']} — {req['funcao']}")
    st.write(f"**Veículo:** {req['veiculo']}")
    st.write(f"**Almoxarife:** {req['almoxarife']}")
    st.write(f"**Status:** {req['status']}")

    df_itens = pd.DataFrame([dict(i) for i in itens])
    st.table(df_itens)

    if req["status"] == "Confirmada" and st.session_state.usuario["role"] == "admin":
        st.warning("Cancelar uma requisição finalizada exige autorização administrativa e fica registrado em auditoria.")
        motivo = st.text_input("Motivo do cancelamento")
        if st.button("❌ Cancelar requisição (devolve estoque)"):
            if not motivo:
                st.error("Informe o motivo.")
            else:
                agora = dt.datetime.now()
                for i in itens:
                    conn.execute(
                        "UPDATE produtos SET estoque_atual = estoque_atual + ? WHERE codigo = ?",
                        (i["quantidade"], i["codigo"]),
                    )
                conn.execute("UPDATE requisicoes SET status='Cancelada' WHERE id=?", (req["id"],))
                conn.execute(
                    "INSERT INTO auditoria (usuario_id, data, hora, operacao, motivo) VALUES (?,?,?,?,?)",
                    (st.session_state.usuario["id"], agora.strftime("%Y-%m-%d"), agora.strftime("%H:%M:%S"),
                     f"CANCELAMENTO_REQ_{req['numero']}", motivo),
                )
                conn.commit()
                st.success("Requisição cancelada e estoque devolvido.")
                st.rerun()

conn.close()
