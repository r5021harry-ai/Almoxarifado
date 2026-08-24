import streamlit as st
from database.db import get_connection

st.markdown("## 🚗 Veículos e Frota")

# Formulário de Cadastro Manual Completo
with st.form("form_veiculo", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    with col_a:
        placa = st.text_input("Placa / Identificação")
        modelo = st.text_input("Modelo / Descrição")
        propriedade = st.text_input("Propriedade (ex: Próprio, Locado)")
    with col_b:
        renavam = st.text_input("Renavam")
        chassi = st.text_input("Chassi")
        
    btn_salvar = st.form_submit_button("➕ Adicionar Veículo", use_container_width=True)

if btn_salvar:
    placa_limpa = placa.strip().upper()
    if placa_limpa:
        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO veiculos (placa, modelo, renavam, chassi, propriedade, status) 
                VALUES (?, ?, ?, ?, ?, 'Ativo')
            """, (placa_limpa, modelo.strip(), renavam.strip(), chassi.strip(), propriedade.strip()))
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
        st.warning("Preencha ao menos a Placa do veículo.")

st.markdown("---")

# Listagem dos Veículos Cadastrados no Banco de Dados
conn = get_connection()
c = conn.cursor()

# Busca todas as colunas disponíveis no banco
c.execute("SELECT * FROM veiculos ORDER BY id DESC")
veiculos = [dict(r) for r in c.fetchall()]
conn.close()

if veiculos:
    st.subheader(f"Frota Cadastrada ({len(veiculos)} veículos)")
    
    # Cabeçalho da Tabela
    c_placa, c_mod, c_prop, c_stat, c_acoes = st.columns([2, 3, 2, 2, 3])
    c_placa.markdown("**Placa**")
    c_mod.markdown("**Modelo**")
    c_prop.markdown("**Propriedade**")
    c_stat.markdown("**Status**")
    c_acoes.markdown("**Ações**")
    st.divider()

    for v in veiculos:
        col_p, col_m, col_pr, col_s, col_b = st.columns([2, 3, 2, 2, 3])
        
        col_p.write(f"**{v.get('placa', '')}**")
        col_m.write(v.get('modelo', '-') or '-')
        col_pr.write(v.get('propriedade', '-') or '-')
        
        status_atual = v.get('status', 'Ativo') or 'Ativo'
        col_s.write("🟢 Ativo" if status_atual == "Ativo" else "🔴 Inativo")
        
        # Botões de Ação
        btn_col1, btn_col2 = col_b.columns(2)
        
        novo_status = "Inativo" if status_atual == "Ativo" else "Ativo"
        if btn_col1.button("Alterar Status", key=f"btn_st_{v['id']}", use_container_width=True):
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE veiculos SET status = ? WHERE id = ?", (novo_status, v["id"]))
            conn.commit()
            conn.close()
            st.rerun()

        if btn_col2.button("🗑️ Excluir", key=f"btn_del_{v['id']}", use_container_width=True):
            conn = get_connection()
            c = conn.cursor()
            c.execute("DELETE FROM veiculos WHERE id = ?", (v["id"],))
            conn.commit()
            conn.close()
            st.rerun()
else:
    st.info("Nenhum veículo cadastrado no banco de dados.")
