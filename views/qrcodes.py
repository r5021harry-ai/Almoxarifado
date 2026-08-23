import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import zipfile
import streamlit as st
from database.db import get_connection
from services.qrcode_service import gerar_qrcode_produto, gerar_etiqueta

if st.session_state.get("usuario") is None:
    st.warning("Faça login primeiro na página inicial.")
    st.stop()

st.title("🏷️ Gerenciar QR Codes")

conn = get_connection()
produtos = conn.execute("SELECT * FROM produtos WHERE status='Ativo' ORDER BY nome").fetchall()
conn.close()

busca = st.text_input("🔎 Buscar produto")
lista = [p for p in produtos if busca.lower() in p["nome"].lower() or busca.lower() in p["codigo"].lower()] if busca else produtos

st.caption(f"{len(lista)} produto(s)")
selecionados = []
cols = st.columns(4)
for i, p in enumerate(lista):
    with cols[i % 4]:
        marcado = st.checkbox(f"{p['nome']} ({p['codigo']})", key=f"qr_{p['id']}")
        if marcado:
            selecionados.append(p)

st.divider()
col1, col2 = st.columns(2)

if col1.button("🖨️ Gerar etiquetas dos SELECIONADOS", type="primary", disabled=not selecionados):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for p in selecionados:
            etiqueta_path = gerar_etiqueta(p["codigo"], p["nome"], p["numero_peca"] or "", p["localizacao"] or "")
            zf.write(etiqueta_path, arcname=os.path.basename(etiqueta_path))
    buf.seek(0)
    st.download_button("⬇️ Baixar etiquetas selecionadas (.zip)", buf, file_name="etiquetas_selecionadas.zip",
                        mime="application/zip")

if col2.button("🖨️ Gerar etiquetas de TODOS os produtos ativos"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for p in produtos:
            etiqueta_path = gerar_etiqueta(p["codigo"], p["nome"], p["numero_peca"] or "", p["localizacao"] or "")
            zf.write(etiqueta_path, arcname=os.path.basename(etiqueta_path))
    buf.seek(0)
    st.download_button("⬇️ Baixar TODAS as etiquetas (.zip)", buf, file_name="etiquetas_todas.zip",
                        mime="application/zip")

st.info("Cada etiqueta contém o QR Code, nome do produto, código, número da peça (se houver) e localização. "
        "A quantidade em estoque nunca é impressa na etiqueta — o QR Code só guarda a identificação do produto; "
        "o estoque é sempre consultado no banco no momento da leitura.")
