import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import datetime as dt
from services import excel_export as xls

if st.session_state.get("usuario") is None:
    st.warning("Faça login primeiro na página inicial.")
    st.stop()

st.title("📊 Relatórios e Exportação Excel")

tab_diario, tab_semanal, tab_mensal, tab_periodo, tab_estoque, tab_fat = st.tabs(
    ["Diário", "Semanal", "Mensal", "Personalizado", "Estoque Atual", "Faturamento (dia)"]
)

def _oferecer_download(path, label):
    with open(path, "rb") as f:
        st.download_button(f"⬇️ Baixar {os.path.basename(path)}", f, file_name=os.path.basename(path),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab_diario:
    data = st.date_input("Data", value=dt.date.today(), key="diario_data")
    if st.button("Gerar relatório diário", type="primary"):
        path, n = xls.exportar_diario(data.strftime("%Y-%m-%d"))
        st.success(f"{n} linha(s) exportada(s).")
        _oferecer_download(path, "diario")

with tab_semanal:
    c1, c2 = st.columns(2)
    inicio = c1.date_input("De", value=dt.date.today() - dt.timedelta(days=6), key="sem_ini")
    fim = c2.date_input("Até", value=dt.date.today(), key="sem_fim")
    if st.button("Gerar relatório semanal", type="primary"):
        path, n = xls.exportar_semanal(inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d"))
        st.success(f"{n} linha(s) exportada(s).")
        _oferecer_download(path, "semanal")

with tab_mensal:
    c1, c2 = st.columns(2)
    ano = c1.number_input("Ano", min_value=2020, max_value=2100, value=dt.date.today().year)
    mes = c2.selectbox("Mês", list(range(1, 13)), index=dt.date.today().month - 1,
                        format_func=lambda m: ["Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho",
                                                "Agosto","Setembro","Outubro","Novembro","Dezembro"][m-1])
    if st.button("Gerar relatório mensal", type="primary"):
        path, n = xls.exportar_mensal(int(ano), int(mes))
        st.success(f"{n} linha(s) exportada(s).")
        _oferecer_download(path, "mensal")

with tab_periodo:
    c1, c2 = st.columns(2)
    inicio = c1.date_input("Data inicial", value=dt.date.today() - dt.timedelta(days=30), key="per_ini")
    fim = c2.date_input("Data final", value=dt.date.today(), key="per_fim")
    st.caption("Filtros opcionais:")
    from database.db import get_connection
    conn = get_connection()
    solicitantes = [r["nome"] for r in conn.execute("SELECT nome FROM funcionarios ORDER BY nome").fetchall()]
    placas = [r["placa"] for r in conn.execute("SELECT placa FROM veiculos ORDER BY placa").fetchall()]
    conn.close()
    c3, c4 = st.columns(2)
    solicitante_f = c3.selectbox("Solicitante", [""] + solicitantes)
    veiculo_f = c4.selectbox("Veículo", [""] + placas)
    produto_f = st.text_input("Produto contém")
    if st.button("Gerar relatório personalizado", type="primary"):
        filtros = {"solicitante": solicitante_f or None, "veiculo": veiculo_f or None, "produto": produto_f or None}
        nome_arquivo = f"Requisicoes_Periodo_{inicio.strftime('%Y%m%d')}_a_{fim.strftime('%Y%m%d')}.xlsx"
        path, n = xls.exportar_requisicoes(inicio.strftime("%Y-%m-%d"), fim.strftime("%Y-%m-%d"), nome_arquivo, filtros)
        st.success(f"{n} linha(s) exportada(s).")
        _oferecer_download(path, "periodo")

with tab_estoque:
    if st.button("Gerar planilha de estoque atual", type="primary"):
        path, n = xls.exportar_estoque_atual()
        st.success(f"{n} produto(s) exportado(s).")
        _oferecer_download(path, "estoque")

with tab_fat:
    st.caption("Planilha simplificada para o setor de faturamento: uma linha por item retirado no dia.")
    data_fat = st.date_input("Data", value=dt.date.today(), key="fat_data")
    if st.button("Gerar Excel de faturamento", type="primary"):
        path, n = xls.exportar_faturamento_diario(data_fat.strftime("%Y-%m-%d"))
        st.success(f"{n} linha(s) exportada(s).")
        _oferecer_download(path, "faturamento")
