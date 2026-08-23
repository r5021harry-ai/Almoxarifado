import io
import streamlit as st
import pandas as pd
import qrcode
from database.db import get_connection

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ⚠️ ALTERE AQUI PARA O IP DA SUA MÁQUINA NA REDE OU LINK WEB
# Exemplo Local: "http://192.168.1.50:8501"
# Exemplo Nuvem: "https://meualmoxarifado.streamlit.app"
URL_BASE_SISTEMA = "http://192.168.1.50:8501"

st.markdown("## 🏷️ Gerenciar QR Codes")

conn = get_connection()
df_produtos = pd.read_sql_query("SELECT id, codigo, nome, estoque_atual, unidade FROM produtos WHERE status='Ativo' ORDER BY nome", conn)
conn.close()

if df_produtos.empty:
    st.info("Nenhum produto cadastrado para gerar QR Code.")
    st.stop()

busca = st.text_input("🔍 Buscar produto", placeholder="Digite o nome ou código...")

if busca:
    df_filtrado = df_produtos[
        df_produtos['nome'].str.contains(busca, case=False, na=False) | 
        df_produtos['codigo'].astype(str).str.contains(busca, case=False, na=False)
    ]
else:
    df_filtrado = df_produtos

st.caption(f"{len(df_filtrado)} produto(s) encontrado(s)")

col_a, col_b, _ = st.columns([1.5, 1.5, 3])

if col_a.button("✅ Selecionar Todos"):
    for prod in df_filtrado.to_dict('records'):
        st.session_state[f"qr_{prod['id']}"] = True
    st.rerun()

if col_b.button("❌ Desmarcar Todos"):
    for prod in df_filtrado.to_dict('records'):
        st.session_state[f"qr_{prod['id']}"] = False
    st.rerun()

produtos_selecionados = []
cols = st.columns(4)

for i, row in enumerate(df_filtrado.to_dict('records')):
    col_idx = i % 4
    key_name = f"qr_{row['id']}"
    
    if key_name not in st.session_state:
        st.session_state[key_name] = False

    marcado = cols[col_idx].checkbox(
        f"{row['nome']} ({row['codigo']})", 
        key=key_name
    )
    
    if marcado:
        produtos_selecionados.append(row)

st.markdown("---")

def gerar_pdf_etiquetas(lista_produtos):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura_pagina, altura_pagina = A4

    colunas = 3
    largura_etiqueta = 60 * mm
    altura_etiqueta = 35 * mm
    margem_x = 10 * mm
    margem_y = 15 * mm
    espaco_x = 5 * mm
    espaco_y = 3 * mm

    col_atual = 0
    linha_atual = 0

    styles = getSampleStyleSheet()
    estilo_produto = ParagraphStyle(
        'EstiloProduto',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.5,
        leading=8,
        textColor='black'
    )

    for prod in lista_produtos:
        x = margem_x + col_atual * (largura_etiqueta + espaco_x)
        y = altura_pagina - margem_y - (linha_atual + 1) * (altura_etiqueta + espaco_y)

        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        c.roundRect(x, y, largura_etiqueta, altura_etiqueta, 3*mm, stroke=1, fill=0)

        # 1. TÍTULO SUPERIOR
        c.setFillColorRGB(0.1, 0.1, 0.1)
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(x + (largura_etiqueta / 2), y + altura_etiqueta - 4.5*mm, "Almoxarifado - Oficina")

        c.setStrokeColorRGB(0.9, 0.9, 0.9)
        c.line(x + 2*mm, y + altura_etiqueta - 6*mm, x + largura_etiqueta - 2*mm, y + altura_etiqueta - 6*mm)

        # 2. GERAR QR CODE COM A URL
        link_produto = f"{URL_BASE_SISTEMA}/?p={prod['codigo']}"
        
        qr = qrcode.QRCode(box_size=3, border=1)
        qr.add_data(link_produto)
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")
        
        img_buffer = io.BytesIO()
        img_qr.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        
        reader = ImageReader(img_buffer)
        c.drawImage(reader, x + 2*mm, y + 2*mm, width=24*mm, height=24*mm)

        # 3. NOME DO PRODUTO
        p_nome = Paragraph(prod['nome'], estilo_produto)
        p_nome.wrapOn(c, 31*mm, 16*mm)
        p_nome.drawOn(c, x + 27*mm, y + 10*mm)

        # 4. CÓDIGO
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 7.5)
        c.drawString(x + 27*mm, y + 4*mm, f"Cód: {prod['codigo']}")

        col_atual += 1
        if col_atual >= colunas:
            col_atual = 0
            linha_atual += 1

        if linha_atual >= 7:
            c.showPage()
            col_atual = 0
            linha_atual = 0

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

if produtos_selecionados:
    pdf_data = gerar_pdf_etiquetas(produtos_selecionados)
    
    st.download_button(
        label=f"🖨️ Imprimir {len(produtos_selecionados)} QR Code(s) em PDF",
        data=pdf_data,
        file_name="etiquetas_qrcodes.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True
    )
else:
    st.warning("Selecione ao menos um produto para gerar a folha de impressão.")
