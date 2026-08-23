import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import streamlit as st
from database.db import get_connection
from services.qrcode_service import extrair_codigo
from services.requisicao_service import (
    buscar_produto_por_codigo, conferir_carrinho, confirmar_saida,
)

if st.session_state.get("usuario") is None:
    st.warning("Faça login primeiro na página inicial.")
    st.stop()

usuario = st.session_state.usuario

if "carrinho" not in st.session_state:
    st.session_state.carrinho = []          # itens da requisição em aberto
if "req_funcionario" not in st.session_state:
    st.session_state.req_funcionario = None
if "req_veiculo" not in st.session_state:
    st.session_state.req_veiculo = None

st.title("📱 Nova Saída")

conn = get_connection()
funcionarios = conn.execute("SELECT * FROM funcionarios WHERE status='Ativo' ORDER BY nome").fetchall()
veiculos = conn.execute("SELECT * FROM veiculos WHERE status='Ativo' ORDER BY placa").fetchall()
conn.close()

if not funcionarios or not veiculos:
    st.error("Cadastre ao menos um funcionário e um veículo antes de iniciar uma saída.")
    st.stop()

# ---------------------------------------------------------------------
# PASSO 1 e 2: Solicitante e Veículo
# ---------------------------------------------------------------------
col1, col2 = st.columns(2)
with col1:
    nomes_func = [f"{f['nome']} — {f['funcao']}" for f in funcionarios]
    idx_func = st.selectbox("👤 Solicitante", range(len(funcionarios)),
                             format_func=lambda i: nomes_func[i],
                             index=None, placeholder="Selecionar...")
with col2:
    placas = [v["placa"] for v in veiculos]
    idx_veic = st.selectbox("🚗 Veículo", range(len(veiculos)),
                             format_func=lambda i: placas[i],
                             index=None, placeholder="Selecionar...")

if idx_func is not None:
    st.session_state.req_funcionario = dict(funcionarios[idx_func])
if idx_veic is not None:
    st.session_state.req_veiculo = dict(veiculos[idx_veic])

pronto_para_ler = st.session_state.req_funcionario and st.session_state.req_veiculo

if not pronto_para_ler:
    st.info("Selecione o solicitante e o veículo para começar a adicionar materiais.")
    st.stop()

st.success(
    f"Solicitante: **{st.session_state.req_funcionario['nome']}** · "
    f"Veículo: **{st.session_state.req_veiculo['placa']}**"
)

# ---------------------------------------------------------------------
# PASSO 3: Ler QR Code (câmera) OU digitar código manualmente
# ---------------------------------------------------------------------
st.subheader("📷 Adicionar material")

tab_camera, tab_manual = st.tabs(["📷 Ler QR Code", "⌨️ Digitar código"])

produto_lido = None

with tab_camera:
    foto = st.camera_input("Aponte a câmera para o QR Code do produto", key="camera_qr")
    if foto is not None:
        try:
            import cv2
            bytes_data = foto.getvalue()
            img_array = np.frombuffer(bytes_data, dtype=np.uint8)
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            detector = cv2.QRCodeDetector()
            texto, _, _ = detector.detectAndDecode(img)
            if texto:
                codigo = extrair_codigo(texto)
                produto_lido = buscar_produto_por_codigo(codigo)
                if produto_lido is None:
                    st.error(f"QR Code lido ({codigo}) mas nenhum produto ativo encontrado com esse código.")
            else:
                st.warning("Não foi possível ler um QR Code nessa foto. Tente novamente, mais perto e com boa luz.")
        except Exception as e:
            st.error(f"Erro ao processar a imagem: {e}")

with tab_manual:
    codigo_manual = st.text_input("Código do produto")
    if st.button("Buscar", key="buscar_manual") and codigo_manual:
        produto_lido = buscar_produto_por_codigo(codigo_manual.strip())
        if produto_lido is None:
            st.error("Produto não encontrado ou inativo.")

if produto_lido is not None:
    p = dict(produto_lido)
    st.markdown("---")
    if p.get("foto_path") and os.path.exists(p["foto_path"]):
        st.image(p["foto_path"], width=180)
    st.markdown(f"### {p['nome']}")
    st.caption(f"Código: {p['codigo']}  ·  Estoque disponível: **{p['estoque_atual']:g} {p['unidade']}**")

    ja_no_carrinho = next((it for it in st.session_state.carrinho if it["produto_id"] == p["id"]), None)
    if ja_no_carrinho:
        st.warning(f"Este produto já foi adicionado. Quantidade atual: {ja_no_carrinho['quantidade']:g}.")

    qtd = st.number_input("Quantidade", min_value=0.0,
                           value=1.0 if not ja_no_carrinho else float(ja_no_carrinho["quantidade"]),
                           step=1.0, key=f"qtd_{p['id']}")

    if st.button("➕ ADICIONAR À REQUISIÇÃO", type="primary", use_container_width=True):
        if qtd <= 0:
            st.error("Informe uma quantidade maior que zero.")
        else:
            if ja_no_carrinho:
                ja_no_carrinho["quantidade"] = qtd
            else:
                st.session_state.carrinho.append({
                    "produto_id": p["id"], "codigo": p["codigo"], "nome": p["nome"],
                    "unidade": p["unidade"], "quantidade": qtd,
                })
            st.success(f"{p['nome']} adicionado. Aponte para o próximo QR Code.")
            st.rerun()

# ---------------------------------------------------------------------
# CARRINHO DA REQUISIÇÃO
# ---------------------------------------------------------------------
st.markdown("---")
st.subheader("🧾 Requisição em aberto")

if not st.session_state.carrinho:
    st.info("Nenhum material adicionado ainda.")
else:
    for i, item in enumerate(st.session_state.carrinho):
        c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
        c1.write(f"**{item['nome']}**  \n`{item['codigo']}`")
        nova_qtd = c2.number_input("Qtd.", min_value=0.0, value=float(item["quantidade"]),
                                    step=1.0, key=f"cart_qtd_{i}", label_visibility="collapsed")
        item["quantidade"] = nova_qtd
        c3.write(item["unidade"])
        if c4.button("🗑️", key=f"rm_{i}"):
            st.session_state.carrinho.pop(i)
            st.rerun()

    st.markdown(f"**Total de itens: {len(st.session_state.carrinho)}**")

    colA, colB = st.columns(2)
    if colA.button("❌ Cancelar requisição", use_container_width=True):
        st.session_state.carrinho = []
        st.session_state.req_funcionario = None
        st.session_state.req_veiculo = None
        st.rerun()

    if colB.button("✅ CONFIRMAR SAÍDA", type="primary", use_container_width=True):
        ok, problemas = conferir_carrinho(st.session_state.carrinho)
        if not ok:
            st.error("Não foi possível finalizar a requisição:")
            for prob in problemas:
                st.write(f"- **{prob['nome']}** ({prob['codigo']}): disponível {prob['disponivel']:g}, "
                         f"solicitado {prob['solicitado']:g}")
        else:
            resultado = confirmar_saida(
                st.session_state.carrinho,
                st.session_state.req_funcionario["id"],
                st.session_state.req_veiculo["id"],
                usuario["id"],
            )
            if resultado["sucesso"]:
                st.success(f"✅ Requisição **{resultado['numero']}** confirmada! Estoque atualizado.")
                st.balloons()
                st.session_state.carrinho = []
                st.session_state.req_funcionario = None
                st.session_state.req_veiculo = None
            else:
                st.error("Erro ao confirmar a saída. Nenhuma baixa foi realizada.")
                st.write(resultado["problemas"])
