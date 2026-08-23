import streamlit as st
import pandas as pd
from database.db import get_connection

st.markdown("## 📦 Produtos")

tab_consultar, tab_novo = st.tabs(["📄 Consultar / Editar", "➕ Novo Produto"])

# ---------------------------------------------------------------------
# TAB 1: CONSULTAR / EDITAR
# ---------------------------------------------------------------------
with tab_consultar:
    conn = get_connection()
    df_produtos = pd.read_sql_query("SELECT * FROM produtos ORDER BY nome", conn)
    conn.close()

    if df_produtos.empty:
        st.info("Nenhum produto cadastrado.")
    else:
        st.dataframe(df_produtos, use_container_width=True)

# ---------------------------------------------------------------------
# TAB 2: NOVO PRODUTO
# ---------------------------------------------------------------------
with tab_novo:
    with st.form("form_novo_produto", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            codigo = st.text_input("Código *")
        with col2:
            nome = st.text_input("Nome *")

        col3, col4, col5 = st.columns([2, 2, 2])
        with col3:
            secao = st.text_input("Seção", value="Geral")
        with col4:
            unidade = st.selectbox(
                "Unidade *", 
                ["UN", "LT (Litro)", "PCT (Pacote)", "KG (Quilograma)", "CX (Caixa)", "M (Metro)", "M²", "M³", "Outros"]
            )
        with col5:
            preco_unitario = st.number_input(
                "Valor Unitário (R$)", 
                min_value=0.0, 
                value=0.0, 
                step=0.50, 
                format="%.2f"
            )

        col6, col7, col8 = st.columns(3)
        with col6:
            estoque_inicial = st.number_input("Estoque inicial", min_value=0.0, value=0.0, step=1.0)
        with col7:
            estoque_minimo = st.number_input("Estoque mínimo", min_value=0.0, value=0.0, step=1.0)
        with col8:
            estoque_maximo = st.number_input("Estoque máximo", min_value=0.0, value=0.0, step=1.0)

        descricao = st.text_area("Descrição")

        btn_cadastrar = st.form_submit_button("➕ Cadastrar produto", type="primary")

        if btn_cadastrar:
            if not codigo or not nome:
                st.error("Preencha todos os campos obrigatórios (*).")
            else:
                try:
                    # Trata a sigla da unidade caso venha do selectbox (ex: "LT (Litro)" -> "LT")
                    sigla_unidade = unidade.split(" ")[0]

                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("""
                        INSERT INTO produtos (
                            codigo, nome, secao, unidade, preco_unitario,
                            estoque_atual, estoque_minimo, estoque_maximo, descricao, status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Ativo')
                    """, (
                        codigo.strip(), 
                        nome.strip(), 
                        secao.strip(), 
                        sigla_unidade, 
                        preco_unitario,
                        estoque_inicial, 
                        estoque_minimo, 
                        estoque_maximo, 
                        descricao.strip()
                    ))
                    conn.commit()
                    conn.close()
                    
                    st.success(f"Produto **{nome}** cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar produto: {e}")
