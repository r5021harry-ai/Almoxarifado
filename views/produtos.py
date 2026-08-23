import io
import streamlit as st
import pandas as pd
from database.db import get_connection

st.markdown("## 📦 Gestão de Produtos")

# Recupera as informações do usuário logado na sessão
usuario_logado = st.session_state.get("usuario", {})
is_admin = usuario_logado.get("role") == "admin"

tab_listar, tab_cadastrar, tab_importar = st.tabs(["📋 Lista de Produtos", "➕ Cadastrar Produto", "📥 Importar Excel"])

# ---------------------------------------------------------------------
# ABA 1: LISTAR E EXCLUIR PRODUTOS
# ---------------------------------------------------------------------
with tab_listar:
    conn = get_connection()
    df_produtos = pd.read_sql_query("SELECT * FROM produtos ORDER BY nome", conn)
    conn.close()

    if df_produtos.empty:
        st.info("Nenhum produto cadastrado.")
    else:
        busca = st.text_input("🔍 Pesquisar produto por nome ou código...", key="busca_prod")
        if busca:
            df_exibir = df_produtos[
                df_produtos['nome'].str.contains(busca, case=False, na=False) |
                df_produtos['codigo'].astype(str).str.contains(busca, case=False, na=False)
            ]
        else:
            df_exibir = df_produtos

        # EXCLUSÃO EM MASSA / SELEÇÃO (EXCLUSIVO ADMIN)
        if is_admin:
            st.markdown("---")
            col_sel1, col_sel2, _ = st.columns([1.5, 1.5, 3])
            
            if col_sel1.button("✅ Selecionar Todos para Ação"):
                for prod_id in df_exibir['id']:
                    st.session_state[f"del_prod_{prod_id}"] = True
                st.rerun()

            if col_sel2.button("❌ Desmarcar Todos"):
                for prod_id in df_exibir['id']:
                    st.session_state[f"del_prod_{prod_id}"] = False
                st.rerun()

            st.write("")

        # CABEÇALHO DA TABELA
        if is_admin:
            col_hdr = st.columns([0.6, 1.2, 3, 1.5, 1.2, 1, 1.5, 1])
            col_hdr[0].markdown("**Excluir**")
            col_hdr[1].markdown("**Código**")
            col_hdr[2].markdown("**Nome do Produto**")
            col_hdr[3].markdown("**Categoria**")
            col_hdr[4].markdown("**Estoque**")
            col_hdr[5].markdown("**UN**")
            col_hdr[6].markdown("**Preço Un. (R$)**")
            col_hdr[7].markdown("**Ação**")
        else:
            col_hdr = st.columns([1.2, 3, 1.5, 1.2, 1, 1.5])
            col_hdr[0].markdown("**Código**")
            col_hdr[1].markdown("**Nome do Produto**")
            col_hdr[2].markdown("**Categoria**")
            col_hdr[3].markdown("**Estoque**")
            col_hdr[4].markdown("**UN**")
            col_hdr[5].markdown("**Preço Un. (R$)**")

        st.divider()

        produtos_para_excluir = []

        for row in df_exibir.to_dict('records'):
            prod_id = row['id']
            if is_admin:
                cols = st.columns([0.6, 1.2, 3, 1.5, 1.2, 1, 1.5, 1])
                
                key_chk = f"del_prod_{prod_id}"
                if key_chk not in st.session_state:
                    st.session_state[key_chk] = False
                
                marcado = cols[0].checkbox("", key=key_chk, label_visibility="collapsed")
                if marcado:
                    produtos_para_excluir.append(prod_id)

                cols[1].write(row['codigo'])
                cols[2].write(row['nome'])
                cols[3].write(row['categoria'] or "-")
                cols[4].write(f"{row['estoque_atual']}")
                cols[5].write(row['unidade'])
                cols[6].write(f"R$ {row['preco_unitario']:.2f}")

                # Botão Excluir individual
                if cols[7].button("🗑️", key=f"btn_del_ind_{prod_id}", help="Excluir este produto"):
                    conn = get_connection()
                    c = conn.cursor()
                    c.execute("DELETE FROM produtos WHERE id = ?", (prod_id,))
                    conn.commit()
                    conn.close()
                    st.toast(f"Produto '{row['nome']}' excluído com sucesso!", icon="🗑️")
                    st.rerun()
            else:
                cols = st.columns([1.2, 3, 1.5, 1.2, 1, 1.5])
                cols[0].write(row['codigo'])
                cols[1].write(row['nome'])
                cols[2].write(row['categoria'] or "-")
                cols[3].write(f"{row['estoque_atual']}")
                cols[4].write(row['unidade'])
                cols[5].write(f"R$ {row['preco_unitario']:.2f}")

        # BOTÃO PARA APAGAR SELECIONADOS EM MASSA (ADMIN)
        if is_admin and produtos_para_excluir:
            st.divider()
            st.warning(f"⚠️ **{len(produtos_para_excluir)}** produto(s) selecionado(s) para exclusão.")
            if st.button(f"🚨 Excluir os {len(produtos_para_excluir)} Produto(s) Selecionados", type="primary"):
                conn = get_connection()
                c = conn.cursor()
                c.executemany("DELETE FROM produtos WHERE id = ?", [(pid,) for pid in produtos_para_excluir])
                conn.commit()
                conn.close()

                # Limpa do session state
                for pid in produtos_para_excluir:
                    st.session_state.pop(f"del_prod_{pid}", None)

                st.success(f"{len(produtos_para_excluir)} produto(s) excluído(s) com sucesso!")
                st.rerun()

# ---------------------------------------------------------------------
# ABA 2: CADASTRAR PRODUTO MANUALMENTE
# ---------------------------------------------------------------------
with tab_cadastrar:
    with st.form("form_cadastrar_produto"):
        col1, col2 = st.columns(2)
        with col1:
            codigo = st.text_input("Código do Produto *")
            nome = st.text_input("Nome do Produto *")
            categoria = st.text_input("Categoria")
        with col2:
            unidade = st.selectbox("Unidade", ["UN", "KG", "L", "M", "CX", "PAR", "PC"], index=0)
            estoque_atual = st.number_input("Estoque Inicial", min_value=0.0, step=1.0, value=0.0)
            preco_unitario = st.number_input("Preço Unitário (R$)", min_value=0.0, step=0.01, value=0.0)
            minimo = st.number_input("Estoque Mínimo", min_value=0.0, step=1.0, value=0.0)

        salvar = st.form_submit_button("💾 Salvar Produto", use_container_width=True)

        if salvar:
            if not codigo.strip() or not nome.strip():
                st.error("Campos Código e Nome são obrigatórios.")
            else:
                conn = get_connection()
                c = conn.cursor()
                try:
                    c.execute("""
                        INSERT INTO produtos (codigo, nome, categoria, unidade, estoque_atual, preco_unitario, minimo, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Ativo')
                    """, (codigo.strip(), nome.strip(), categoria.strip(), unidade, estoque_atual, preco_unitario, minimo))
                    conn.commit()
                    st.success(f"Produto '{nome}' cadastrado com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao cadastrar produto (código pode já existir): {e}")
                finally:
                    conn.close()

# ---------------------------------------------------------------------
# ABA 3: IMPORTAR PRODUTOS VIA EXCEL
# ---------------------------------------------------------------------
with tab_importar:
    st.markdown("### 📥 Importação em Lote via Planilha Excel")
    st.info("""
    **Instruções para importação:**
    1. A planilha deve conter as colunas obrigatórias: **`codigo`** e **`nome`**.
    2. Outras colunas aceitas: **`estoque_atual`**, **`unidade`**, **`preco_unitario`**, **`categoria`**, **`minimo`**.
    3. Caso o código do produto já exista no banco de dados, os dados desse produto serão **atualizados**.
    """)

    modelo_df = pd.DataFrame([{
        "codigo": "9794",
        "nome": "TERMINAL DIRECAO CAMINHAO VW F12000 - LD",
        "categoria": "Peças",
        "unidade": "UN",
        "estoque_atual": 10.0,
        "preco_unitario": 120.00,
        "minimo": 2.0
    }])
    
    buffer_modelo = io.BytesIO()
    with pd.ExcelWriter(buffer_modelo, engine='openpyxl') as writer:
        modelo_df.to_excel(writer, index=False, sheet_name='Modelo')
    buffer_modelo.seek(0)

    st.download_button(
        label="📄 Baixar Planilha Modelo de Exemplo (.xlsx)",
        data=buffer_modelo,
        file_name="modelo_importacao_produtos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.divider()

    arquivo_excel = st.file_uploader("Selecione o arquivo Excel (.xlsx ou .xls)", type=["xlsx", "xls"])

    if arquivo_excel is not None:
        try:
            df_import = pd.read_excel(arquivo_excel)
            df_import.columns = [str(col).strip().lower() for col in df_import.columns]
            
            colunas_obrigatorias = {"codigo", "nome"}
            if not colunas_obrigatorias.issubset(df_import.columns):
                st.error("❌ A planilha precisa conter pelo menos as colunas **codigo** e **nome**.")
            else:
                st.subheader("Pré-visualização dos dados a importar:")
                st.dataframe(df_import.head(10), use_container_width=True)

                if st.button("🚀 Confirmar Importação", type="primary", use_container_width=True):
                    conn = get_connection()
                    c = conn.cursor()

                    sucessos = 0
                    erros = 0

                    for _, row in df_import.iterrows():
                        cod = str(row.get("codigo", "")).strip()
                        nm = str(row.get("nome", "")).strip()

                        if not cod or not nm or pd.isna(row.get("codigo")) or pd.isna(row.get("nome")):
                            erros += 1
                            continue

                        est_atual = float(row.get("estoque_atual", 0)) if pd.notna(row.get("estoque_atual")) else 0.0
                        un = str(row.get("unidade", "UN")).strip() if pd.notna(row.get("unidade")) else "UN"
                        prc = float(row.get("preco_unitario", 0.0)) if pd.notna(row.get("preco_unitario")) else 0.0
                        cat = str(row.get("categoria", "")).strip() if pd.notna(row.get("categoria")) else ""
                        mn = float(row.get("minimo", 0)) if pd.notna(row.get("minimo")) else 0.0

                        try:
                            c.execute("""
                                INSERT INTO produtos (codigo, nome, categoria, unidade, estoque_atual, preco_unitario, minimo, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, 'Ativo')
                                ON CONFLICT(codigo) DO UPDATE SET
                                    nome = excluded.nome,
                                    categoria = excluded.categoria,
                                    unidade = excluded.unidade,
                                    estoque_atual = excluded.estoque_atual,
                                    preco_unitario = excluded.preco_unitario,
                                    minimo = excluded.minimo,
                                    status = 'Ativo'
                            """, (cod, nm, cat, un, est_atual, prc, mn))
                            sucessos += 1
                        except Exception:
                            c.execute("SELECT id FROM produtos WHERE codigo = ?", (cod,))
                            prod_existente = c.fetchone()

                            if prod_existente:
                                c.execute("""
                                    UPDATE produtos 
                                    SET nome=?, categoria=?, unidade=?, estoque_atual=?, preco_unitario=?, minimo=?, status='Ativo'
                                    WHERE codigo=?
                                """, (nm, cat, un, est_atual, prc, mn, cod))
                                sucessos += 1
                            else:
                                erros += 1

                    conn.commit()
                    conn.close()

                    st.success(f"🎉 Importação concluída! {sucessos} produto(s) processado(s) com sucesso.")
                    if erros > 0:
                        st.warning(f"⚠️ {erros} linha(s) foram ignoradas por falta de código ou nome.")

        except Exception as e:
            st.error(f"Erro ao ler a planilha Excel: {e}")
