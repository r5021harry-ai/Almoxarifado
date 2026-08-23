import streamlit as st
from database.db import get_connection

st.markdown("## 🚗 Veículos")

# Formulário de Cadastro (Apenas Placa)
with st.form("form_veiculo", clear_on_submit=True):
    placa = st.text_input("Placa / Identificação")
    btn_salvar = st.form_submit_button("➕ Adicionar Veículo", use_container_width=True)

if btn_salvar:
    placa_limpa = placa.strip().upper()
    if placa_limpa:
        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO veiculos (placa, status) VALUES (?, 'Ativo')", (placa_limpa,))
            conn.commit()
            st.success(f"Veículo '{placa_limpa}' cadastrado com sucesso!")
            st.rerun()
        except Exception as e:
            conn.rollback()
            if "UNIQUE" in str(e):
                st.error(f"A placa '{placa_limpa}' já está cadastrada no sistema.")
            else:
                st.error(f"Erro ao salvar veículo: {e}")
        finally:
            conn.close()
    else:
        st.warning("Preencha a Placa do veículo.")

st.markdown("---")

# Listagem dos Veículos
conn = get_connection()
c = conn.cursor()
c.execute("SELECT * FROM veiculos ORDER BY id DESC")
veiculos = [dict(r) for r in c.fetchall()]
conn.close()

if veiculos:
    for v in veiculos:
        col_p, col_s, col_b = st.columns([4, 3, 3])
        col_p.write(v["placa"])
        col_s.write(v["status"])
        
        novo_status = "Inativo" if v["status"] == "Ativo" else "Ativo"
        if col_b.button(f"Marcar {novo_status}", key=f"btn_veic_{v['id']}"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE veiculos SET status = ? WHERE id = ?", (novo_status, v["id"]))
            conn.commit()
            conn.close()
            st.rerun()
else:
    st.info("Nenhum veículo cadastrado.")
