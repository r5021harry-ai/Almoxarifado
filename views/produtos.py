import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from database.db import get_connection
from services.qrcode_service import gerar_qrcode_produto

if st.session_state.get("usuario") is None:
    st.warning("Faça login primeiro na página inicial.")
    st.stop()

st.title("📦 Produtos")

tab_lista, tab_cadastro = st.tabs(["📋 Consultar / Editar", "➕ Novo Produto"])

conn = get_connection()

with tab_lista:
    secoes = [r["secao"] for r in conn.execute("SELECT DISTINCT secao FROM produtos ORDER BY secao").fetchall()]
    col1, col2 = st.columns([2, 1])
    busca = col1.text_input("Buscar por nome ou código")
    secao_filtro = col2.selectbox("Seção", ["Todas"] + secoes)

    sql = "SELECT * FROM produtos WHERE 1=1"
    params = []
    if busca:
        sql += " AND (nome LIKE ? OR codigo LIKE ?)"
        params += [f"%{busca}%", f"%{busca}%"]
    if secao_filtro != "Todas":
        sql += " AND secao = ?"
        params.append(secao_filtro)
    sql += " ORDER BY secao, nome"
    produtos = conn.execute(sql, params).fetchall()

    st.caption(f"{len(produtos)} produto(s) encontrado(s)")

    df = pd.DataFrame([{
        "Status": "🔴" if p["estoque_atual"] <= 0 else ("🟡" if p["estoque_minimo"] > 0 and p["estoque_atual"] < p["estoque_minimo"] else "🟢"),
        "Código": p["codigo"], "Nome": p["nome"], "Seção": p["secao"],
        "Unidade": p["unidade"], "Estoque": p["estoque_atual"],
        "Mínimo": p["estoque_minimo"],
    } for p in produtos])
    st.dataframe(df, use_container_width=True, hide_index=True, height=400)

    st.divider()
    st.subheader("✏️ Editar produto")
    codigos = [p["codigo"] for p in produtos]
    codigo_edit = st.selectbox("Selecione pelo código", [""] + codigos)
    if codigo_edit:
        p = conn.execute("SELECT * FROM produtos WHERE codigo=?", (codigo_edit,)).fetchone()
        p = dict(p)
        with st.form("edit_form"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome", value=p["nome"])
            secao = c2.text_input("Seção", value=p["secao"] or "")
            c3, c4, c5 = st.columns(3)
            unidade = c3.text_input("Unidade", value=p["unidade"] or "UN")
            estoque_min = c4.number_input("Estoque mínimo", value=float(p["estoque_minimo"] or 0), step=1.0)
            estoque_max = c5.number_input("Estoque máximo", value=float(p["estoque_maximo"] or 0), step=1.0)
            c6, c7 = st.columns(2)
            localizacao = c6.text_input("Localização", value=p["localizacao"] or "")
            numero_peca = c7.text_input("Número da peça", value=p["numero_peca"] or "")
            status = st.selectbox("Status", ["Ativo", "Inativo"], index=0 if p["status"] == "Ativo" else 1)
            foto = st.file_uploader("Foto do produto", type=["png", "jpg", "jpeg"])
            salvar = st.form_submit_button("💾 Salvar alterações", type="primary")

        if salvar:
            foto_path = p["foto_path"]
            if foto is not None:
                uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "produtos")
                os.makedirs(uploads_dir, exist_ok=True)
                foto_path = os.path.join(uploads_dir, f"{p['codigo']}.png")
                with open(foto_path, "wb") as f:
                    f.write(foto.getbuffer())
            conn.execute("""
                UPDATE produtos SET nome=?, secao=?, unidade=?, estoque_minimo=?, estoque_maximo=?,
                       localizacao=?, numero_peca=?, status=?, foto_path=? WHERE id=?
            """, (nome, secao, unidade, estoque_min, estoque_max, localizacao, numero_peca, status, foto_path, p["id"]))
            conn.commit()
            st.success("Produto atualizado!")
            st.rerun()

with tab_cadastro:
    with st.form("novo_produto_form"):
        c1, c2 = st.columns(2)
        codigo = c1.text_input("Código *")
        nome = c2.text_input("Nome *")
        c3, c4 = st.columns(2)
        secao = c3.text_input("Seção", value="Geral")
        unidade = c4.text_input("Unidade", value="UN")
        c5, c6, c7 = st.columns(3)
        estoque_inicial = c5.number_input("Estoque inicial", min_value=0.0, step=1.0)
        estoque_min = c6.number_input("Estoque mínimo", min_value=0.0, step=1.0)
        estoque_max = c7.number_input("Estoque máximo", min_value=0.0, step=1.0)
        descricao = st.text_area("Descrição")
        criar = st.form_submit_button("➕ Cadastrar produto", type="primary")

    if criar:
        if not codigo or not nome:
            st.error("Código e nome são obrigatórios.")
        else:
            existe = conn.execute("SELECT id FROM produtos WHERE codigo=?", (codigo,)).fetchone()
            if existe:
                st.error("Já existe um produto com esse código.")
            else:
                conn.execute("""
                    INSERT INTO produtos (codigo, nome, descricao, secao, unidade, estoque_atual,
                                           estoque_minimo, estoque_maximo, status)
                    VALUES (?,?,?,?,?,?,?,?, 'Ativo')
                """, (codigo, nome, descricao, secao, unidade, estoque_inicial, estoque_min, estoque_max))
                conn.commit()
                gerar_qrcode_produto(codigo)
                st.success(f"Produto {nome} cadastrado com QR Code gerado!")
                st.rerun()

conn.close()
