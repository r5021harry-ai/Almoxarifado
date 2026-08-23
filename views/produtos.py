import io
import streamlit as st
import pandas as pd
from database.db import get_connection

st.markdown("## 📦 Gestão de Produtos")

tab_listar, tab_cadastrar, tab_importar = st.tabs(["📋 Lista de Produtos", "➕ Cadastrar Produto", "📥 Importar Excel"])

# ---------------------------------------------------------------------
# ABA 1: LISTAR PRODUTOS
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

        st.dataframe(
            df_exibir,
            use_container_width=True,
            column_config={
                "id": "ID",
                "codigo": "Código",
                "nome": "Nome do Produto",
                "categoria": "Categoria",
                "estoque_atual": "Estoque",
                "unidade": "UN",
                "preco_unitario": st.column_config.NumberColumn("Preço Un. (R$)", format="R$ %.2f"),
                "minimo": "Estoque Mín.",
                "status": "Status"
            },
            hide_index=True
        )

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

    # Botão para baixar modelo de planilha de exemplo
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
            
            # Normaliza os nomes das colunas para minúsculo
            df_import.columns = [str(col).strip().lower() for col in df_import.columns]
            
            # Validação de colunas obrigatórias
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
                            # Tenta inserir, se já existir o código atualiza (UPSERT)
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
                        except Exception as ex:
                            # Caso a tabela não tenha restrição UNIQUE em codigo no SQLite, faz busca manual
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
