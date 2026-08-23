import io
import datetime as dt
import pandas as pd
import streamlit as st
from database.db import get_connection

st.markdown("## 📊 Relatórios e Exportação Excel")
st.caption("Gere relatórios agrupados de saídas com cálculo automático de valores totais.")

def gerar_excel_saidas(data_inicio, data_fim, titulo_periodo):
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Identifica as colunas disponíveis na tabela produtos
    c.execute("PRAGMA table_info(produtos)")
    cols_produtos = [col[1] for col in c.fetchall()]
    
    col_codigo = "codigo" if "codigo" in cols_produtos else "id"
    col_nome = "nome" if "nome" in cols_produtos else "descricao"
    
    # Procura a coluna de preço/valor unitário
    col_preco = next((k for k in ['valor_unitario', 'preco', 'valor', 'preco_unitario'] if k in cols_produtos), None)
    sql_preco = f"p.{col_preco}" if col_preco else "0"

    # 2. Busca movimentações de SAÍDA no período
    query = f"""
        SELECT 
            p.{col_codigo} AS "Código",
            p.{col_nome} AS "Nome do Produto",
            m.quantidade AS Qtd,
            COALESCE({sql_preco}, 0) AS "Valor Unitário (R$)",
            m.observacao,
            m.data_hora
        FROM movimentacoes m
        JOIN produtos p ON m.produto_id = p.id
        WHERE m.tipo = 'SAIDA'
          AND date(m.data_hora) BETWEEN date(?) AND date(?)
    """
    
    try:
        c.execute(query, (data_inicio, data_fim))
        rows = c.fetchall()
        
        if not rows:
            return None, None
            
        dados = [dict(r) for r in rows]
        df = pd.DataFrame(dados)
        
        # 3. Se o valor unitário for zero no cadastro, extrai o valor das saídas/entradas na observação
        for idx, row in df.iterrows():
            if float(row["Valor Unitário (R$)"]) == 0 and "Valor Un.: R$" in str(row["observacao"]):
                try:
                    val_str = str(row["observacao"]).split("Valor Un.: R$")[1].split("|")[0].strip()
                    df.at[idx, "Valor Unitário (R$)"] = float(val_str.replace(",", "."))
                except:
                    pass

        # Converte a coluna para numérico para evitar erros de soma
        df["Valor Unitário (R$)"] = pd.to_numeric(df["Valor Unitário (R$)"], errors="coerce").fillna(0.0)
        df["Qtd"] = pd.to_numeric(df["Qtd"], errors="coerce").fillna(0.0)

        # 4. Agrupa os dados por Código e Nome do Produto
        df_grouped = df.groupby(["Código", "Nome do Produto"], as_index=False).agg({
            "Qtd": "sum",
            "Valor Unitário (R$)": "max"
        })
        
        # 5. Calcula o Total = Quantidade * Valor Unitário
        df_grouped["Total (R$)"] = df_grouped["Qtd"] * df_grouped["Valor Unitário (R$)"]
        
        # 6. Adiciona a linha final com o TOTAL GERAL
        total_qtd = df_grouped["Qtd"].sum()
        total_valor = df_grouped["Total (R$)"].sum()
        
        linha_total = pd.DataFrame([{
            "Código": "TOTAL GERAL",
            "Nome do Produto": "---",
            "Qtd": total_qtd,
            "Valor Unitário (R$)": 0.0,
            "Total (R$)": total_valor
        }])
        
        df_final = pd.concat([df_grouped, linha_total], ignore_index=True)
        
        # 7. Gera o arquivo em buffer (.xlsx)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, sheet_name=titulo_periodo[:31], index=False)
            
        return output.getvalue(), df_final

    except Exception as e:
        st.error(f"Erro ao processar relatório: {e}")
        return None, None
    finally:
        conn.close()


# Interface de Abas
tab_diario, tab_semanal, tab_mensal, tab_custom = st.tabs(["Diário", "Semanal", "Mensal", "Personalizado"])

# ---------------------------------------------------------------------
# DIÁRIO
# ---------------------------------------------------------------------
with tab_diario:
    data_sel = st.date_input("Selecione a Data", dt.date.today(), key="diario_data")
    if st.button("📊 Gerar Relatório Diário", use_container_width=True):
        excel_bytes, df_preview = gerar_excel_saidas(data_sel, data_sel, f"Diario_{data_sel}")
        if excel_bytes:
            st.dataframe(df_preview, use_container_width=True)
            st.download_button(
                label="📥 Baixar Planilha Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"relatorio_saidas_diario_{data_sel}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("Nenhuma saída registrada para a data selecionada.")

# ---------------------------------------------------------------------
# SEMANAL
# ---------------------------------------------------------------------
with tab_semanal:
    data_fim_sem = dt.date.today()
    data_ini_sem = data_fim_sem - dt.timedelta(days=7)
    st.write(f"Período: **{data_ini_sem.strftime('%d/%m/%Y')}** até **{data_fim_sem.strftime('%d/%m/%Y')}**")
    if st.button("📊 Gerar Relatório Semanal", use_container_width=True):
        excel_bytes, df_preview = gerar_excel_saidas(data_ini_sem, data_fim_sem, "Semanal")
        if excel_bytes:
            st.dataframe(df_preview, use_container_width=True)
            st.download_button(
                label="📥 Baixar Planilha Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"relatorio_saidas_semanal_{data_ini_sem}_a_{data_fim_sem}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("Nenhuma saída registrada nos últimos 7 dias.")

# ---------------------------------------------------------------------
# MENSAL
# ---------------------------------------------------------------------
with tab_mensal:
    hoje = dt.date.today()
    data_ini_mes = hoje.replace(day=1)
    st.write(f"Mês Atual: **{data_ini_mes.strftime('%m/%Y')}**")
    if st.button("📊 Gerar Relatório Mensal", use_container_width=True):
        excel_bytes, df_preview = gerar_excel_saidas(data_ini_mes, hoje, f"Mensal_{hoje.strftime('%m_%Y')}")
        if excel_bytes:
            st.dataframe(df_preview, use_container_width=True)
            st.download_button(
                label="📥 Baixar Planilha Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"relatorio_saidas_mensal_{hoje.strftime('%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("Nenhuma saída registrada neste mês.")

# ---------------------------------------------------------------------
# PERSONALIZADO
# ---------------------------------------------------------------------
with tab_custom:
    col1, col2 = st.columns(2)
    with col1:
        dt_ini = st.date_input("Data Inicial", dt.date.today() - dt.timedelta(days=30))
    with col2:
        dt_fim = st.date_input("Data Final", dt.date.today())
        
    if st.button("📊 Gerar Relatório Personalizado", use_container_width=True):
        excel_bytes, df_preview = gerar_excel_saidas(dt_ini, dt_fim, "Personalizado")
        if excel_bytes:
            st.dataframe(df_preview, use_container_width=True)
            st.download_button(
                label="📥 Baixar Planilha Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"relatorio_saidas_{dt_ini}_a_{dt_fim}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("Nenhuma saída registrada no período selecionado.")
