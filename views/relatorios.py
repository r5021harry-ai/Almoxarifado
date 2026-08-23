import streamlit as st
import pandas as pd
from database.db import get_connection

st.markdown("## 📊 Relatórios e Exportação")
st.caption("Gere relatórios agrupados de saídas com cálculo automático de valores totais.")

tab_diario, tab_semanal, tab_mensal, tab_custom = st.tabs(["Diário", "Semanal", "Mensal", "Personalizado"])

def buscar_relatorio(data_inicio, data_fim=None):
    conn = get_connection()
    c = conn.cursor()
    
    query = """
        SELECT 
            r.numero AS 'Nº Requisição',
            r.data AS 'Data',
            r.hora AS 'Hora',
            f.nome AS 'Solicitante',
            v.placa AS 'Veículo',
            p.codigo AS 'Código Item',
            p.nome AS 'Produto',
            ri.quantidade AS 'Quantidade',
            p.unidade AS 'Unidade',
            u.nome AS 'Almoxarife'
        FROM requisicoes r
        JOIN funcionarios f ON r.funcionario_id = f.id
        JOIN veiculos v ON r.veiculo_id = v.id
        JOIN usuarios u ON r.almoxarife_id = u.id
        JOIN requisicao_itens ri ON r.id = ri.requisicao_id
        JOIN produtos p ON ri.produto_id = p.id
        WHERE r.status = 'Confirmada'
    """
    
    if data_fim:
        query += " AND r.data BETWEEN ? AND ? ORDER BY r.id DESC"
        c.execute(query, (str(data_inicio), str(data_fim)))
    else:
        query += " AND r.data = ? ORDER BY r.id DESC"
        c.execute(query, (str(data_inicio),))
        
    dados = [dict(r) for r in c.fetchall()]
    conn.close()
    return pd.DataFrame(dados)

def exibir_tabela_e_download(df, nome_arquivo):
    if df.empty:
        st.info("Nenhuma saída registrada para o período selecionado.")
    else:
        st.dataframe(df, use_container_width=True)
        
        # 'sep=;' separa em colunas no Excel em português
        # 'utf-8-sig' garante que acentos e caracteres especiais não fiquem corrompidos
        csv_data = df.to_csv(index=False, sep=';', encoding='utf-8-sig')
        
        st.download_button(
            label="📥 Baixar Planilha para Excel (.csv)",
            data=csv_data,
            file_name=f"{nome_arquivo}.csv",
            mime="text/csv",
            type="primary"
        )

# 1. ABA DIÁRIO
with tab_diario:
    data_sel = st.date_input("Selecione a Data", key="dt_diario")
    if st.button("📊 Gerar Relatório Diário", key="btn_diario"):
        df_diario = buscar_relatorio(data_sel)
        exibir_tabela_e_download(df_diario, f"relatorio_diario_{data_sel}")

# 2. ABA SEMANAL
with tab_semanal:
    col_i, col_f = st.columns(2)
    with col_i:
        dt_inicio = st.date_input("Data Inicial", key="dt_sem_i")
    with col_f:
        dt_fim = st.date_input("Data Final", key="dt_sem_f")
        
    if st.button("📊 Gerar Relatório Semanal", key="btn_semanal"):
        df_sem = buscar_relatorio(dt_inicio, dt_fim)
        exibir_tabela_e_download(df_sem, f"relatorio_semanal_{dt_inicio}_a_{dt_fim}")

# 3. ABA MENSAL
with tab_mensal:
    col_m, col_a = st.columns(2)
    with col_m:
        mes = st.selectbox("Mês", list(range(1, 13)), index=0)
    with col_a:
        ano = st.number_input("Ano", min_value=2020, max_value=2030, value=2026)
        
    if st.button("📊 Gerar Relatório Mensal", key="btn_mensal"):
        data_ini = f"{ano}-{mes:02d}-01"
        import calendar
        _, ultimo_dia = calendar.monthrange(ano, mes)
        data_fim = f"{ano}-{mes:02d}-{ultimo_dia:02d}"
        
        df_mensal = buscar_relatorio(data_ini, data_fim)
        exibir_tabela_e_download(df_mensal, f"relatorio_mensal_{mes:02d}_{ano}")

# 4. ABA PERSONALIZADO
with tab_custom:
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p_inicio = st.date_input("Início", key="p_ini")
    with col_p2:
        p_fim = st.date_input("Fim", key="p_fim")
        
    if st.button("📊 Gerar Relatório Personalizado", key="btn_custom"):
        df_custom = buscar_relatorio(p_inicio, p_fim)
        exibir_tabela_e_download(df_custom, f"relatorio_custom_{p_inicio}_a_{p_fim}")
