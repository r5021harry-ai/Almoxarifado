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
    
    try:
        # 1. Mapeia colunas da tabela 'produtos'
        c.execute("PRAGMA table_info(produtos)")
        cols_produtos = [col[1] for col in c.fetchall()]
        col_prod_codigo = "codigo" if "codigo" in cols_produtos else "id"
        col_prod_nome = "nome" if "nome" in cols_produtos else "descricao"
        col_prod_preco = next((k for k in ['valor_unitario', 'preco', 'valor', 'preco_unitario'] if k in cols_produtos), None)

        # 2. Mapeia colunas da tabela 'movimentacoes'
        c.execute("PRAGMA table_info(movimentacoes)")
        cols_mov = [col[1] for col in c.fetchall()]
        col_mov_data = next((k for k in ['data_hora', 'data', 'created_at', 'timestamp'] if k in cols_mov), None)
        col_mov_tipo = "tipo" if "tipo" in cols_mov else "tipo_movimentacao"
        col_mov_qtd = "quantidade" if "quantidade" in cols_mov else "qtd"
        col_mov_obs = "observacao" if "observacao" in cols_mov else "obs"

        # Preço do produto no SQL
        sql_preco = f"p.{col_prod_preco}" if col_prod_preco else "0"

        # Busca movimentações de SAÍDA
        query = f"""
            SELECT 
                p.{col_prod_codigo} AS "Código",
                p.{col_prod_nome} AS "Nome do Produto",
                m.{col_mov_qtd} AS Qtd,
                COALESCE({sql_preco}, 0) AS "Valor Unitário (R$)",
                m.{col_mov_obs} AS observacao,
                m.{col_mov_data} AS data_registro
            FROM movimentacoes m
            JOIN produtos p ON m.produto_id = p.id
            WHERE UPPER(m.{col_mov_tipo}) = 'SAIDA'
        """
        
        c.execute(query)
        rows = c.fetchall()
        
        if not rows:
            return None, None
            
        dados = [dict(r) for r in rows]
        df = pd.DataFrame(dados)

        # Converte e filtra as datas no Pandas para evitar falhas do SQL date()
        df["data_registro"] = pd.to_datetime(df["data_registro"]).dt.date
        df = df[(df["data_registro"] >= data_inicio) & (df["data_registro"] <= data_fim)]

        if df.empty:
            return None, None

        # 3. Extrai valor unitário da observação se o cadastro estiver zerado
        for idx, row in df.iterrows():
            if float(row["Valor Unitário (R$)"]) == 0 and "Valor Un.: R$" in str(row["observacao"]):
                try:
                    val_str = str(row["observacao"]).split("Valor Un.: R$")[1].split("|")[0].strip()
                    df.at[idx, "Valor Unitário (R$)"] = float(val_str.replace(",", "."))
                except:
                    pass

        df["Valor Unitário (R$)"] = pd.to_numeric(df["Valor Unitário (R$)"], errors="coerce").fillna(0.0)
        df["Qtd"] = pd.to_numeric(df["Qtd"], errors="coerce").fillna(0.0)

        # 4. Agrupa por Código e Produto
        df_grouped = df.groupby(["Código", "Nome do Produto"], as_index=False).agg({
            "Qtd": "sum",
            "Valor Unitário (R$)": "max"
        })
        
        # 5. Calcula Total por Produto (Qtd x Valor Unitário)
        df_grouped["Total (R$)"] = df_grouped["Qtd"] * df_grouped["Valor Unitário (R$)"]
        
        # 6. Soma Totais Gerais
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
        
        # Formatadores para exibição
        df_display = df_final.copy()
        df_display["Valor Unitário (R$)"] = df_display["Valor Unitário (R$)"].apply(lambda x: f"R$ {x:,.2f}" if x > 0 else "-")
        df_display["Total (R$)"] = df_display["Total (R$)"].apply(lambda x: f"R$ {x:,.2f}")

        # 7. Gera buffer do arquivo Excel (.xlsx)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final.to_excel(writer, sheet_name=titulo_periodo[:31], index=False)
            
        return output.getvalue(), df_display

    except Exception as e:
        st.error(f"Erro ao processar relatório: {e}")
        return None, None
    finally:
        conn.close()


# Abas da Interface
tab_diario, tab_semanal, tab_mensal, tab_custom = st.tabs(["Diário", "Semanal", "Mensal", "Personalizado"])

# DIÁRIO
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

# SEMANAL
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

# MENSAL
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

# PERSONALIZADO
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
