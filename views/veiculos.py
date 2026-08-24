import streamlit as st
import os, openpyxl
from database.db import get_connection

st.markdown("## 🚗 Veículos e Frota")

# ---------------------------------------------------------------------
# LOCALIZADOR AUTOMÁTICO DA PLANILHA
# ---------------------------------------------------------------------
def encontrar_arquivo_frota():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for pasta_atual, _, arquivos in os.walk(raiz):
        for arquivo in arquivos:
            if "frota" in arquivo.lower() and arquivo.lower().endswith(".xlsx"):
                return os.path.join(pasta_atual, arquivo)
    return None

# ---------------------------------------------------------------------
# FUNÇÃO DE IMPORTAÇÃO SEGUINDO A ORDEM DA PLANILHA:
# [0]: PLACA | [1]: PROPRIEDADE | [2]: RENAVAM | [3]: CHASSI | [4]: MODELO
# ---------------------------------------------------------------------
def processar_excel_frota(arquivo_ou_caminho):
    try:
        wb = openpyxl.load_workbook(arquivo_ou_caminho)
        sheet = wb.active
        conn = get_connection()
        c = conn.cursor()
        
        inseridos = 0
        for row in sheet.iter_rows(min_row=2, values_only=True):
            if row and row[0]:
                placa = str(row[0]).strip().upper()
                propriedade = str(row[1] or '').strip() if len(row) > 1 else ''
                renavam = str(row[2] or '').strip() if len(row) > 2 else ''
                chassi = str(row[3] or '').strip() if len(row) > 3 else ''
                modelo = str(row[4] or '').strip() if len(row) > 4 else ''
                
                c.execute("""
                    INSERT INTO veiculos (placa, propriedade, renavam, chassi, modelo, status)
                    VALUES (?, ?, ?, ?, ?, 'Ativo')
                    ON CONFLICT(placa) DO UPDATE SET
                        propriedade=excluded.propriedade,
                        renavam=excluded.renavam,
                        chassi=excluded.chassi,
                        modelo=excluded.modelo
                """, (placa, propriedade, renavam, chassi, modelo))
                inseridos += 1
                
        conn.commit()
        conn.close()
        return inseridos
    except Exception as e:
        st.error(f"Erro ao processar planilha de frota: {e}")
        return 0

# Tenta carregar automaticamente se o banco estiver sem registros
conn = get_connection()
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM veiculos")
total_veiculos = c.fetchone()[0]
conn.close()

if total_veiculos == 0:
    caminho_frota = encontrar_arquivo_frota()
    if caminho_frota:
        qtd = processar_excel_frota(caminho_frota)
        if qtd > 0:
            st.success(f"✅ {qtd} veículos importados com sucesso!")
            st.rerun()

# ---------------------------------------------------------------------
# IMPORTAÇÃO MANUAL VIA UPLOAD
# ---------------------------------------------------------------------
with st.expander("📥 Importar Planilha de Frota (Upload Manual)", expanded=(total_veiculos == 0)):
    st.write("Envie a planilha `FROTA.xlsx` organizada nas colunas: **PLACA | PROPRIEDADE | RENAVAM | CHASSI | MODELO**")
    file_upload = st.file_uploader("Selecione o arquivo Excel", type=["xlsx", "xls"], key="uploader_frota")
    if file_upload is not None:
        if st.button("Confirmar Importação", use_container_width=True):
            qtd = processar_excel_frota(file_upload)
            if qtd > 0:
                st.success(f"✅ {qtd} veículos cadastrados com sucesso!")
                st.rerun()

# ---------------------------------------------------------------------
# FORMULÁRIO DE CADASTRO MANUAL
# ---------------------------------------------------------------------
with st.form("form_veiculo", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    with col_a:
        placa = st.text_input("Placa / Identificação")
        propriedade = st.text_input("Propriedade (ex: Próprio, Locado)")
        renavam = st.text_input("Renavam")
    with col_b:
        chassi = st.text_input("Chassi")
        modelo = st.text_input("Modelo / Descrição")
        
    btn_salvar = st.form_submit_button("➕ Adicionar Veículo", use_container_width=True)

if btn_salvar:
    placa_limpa = placa.strip().upper()
    if placa_limpa:
        conn = get_connection()
        c = conn.cursor()
        try:
            c.execute("""
                INSERT INTO veiculos (placa, propriedade, renavam, chassi, modelo, status) 
                VALUES (?, ?, ?, ?, ?, 'Ativo')
            """, (placa_limpa, propriedade.strip(), renavam.strip(), chassi.strip(), modelo.strip()))
            conn.commit()
            st.success(f"Veículo '{placa_limpa}' cadastrado com sucesso!")
            st.rerun()
        except Exception as e:
            conn.rollback()
            if "UNIQUE" in str(e):
                st.error(f"A placa '{placa_limpa}' já está cadastrada.")
            else:
                st.error(f"Erro ao salvar veículo: {e}")
        finally:
            conn.close()
    else:
        st.warning("Preencha ao menos a Placa do veículo.")

st.markdown("---")

# ---------------------------------------------------------------------
# LISTAGEM DA FROTA (NA MESMA ORDEM DA PLANILHA)
# ---------------------------------------------------------------------
conn = get_connection()
c = conn.cursor()
c.execute("SELECT * FROM veiculos ORDER BY id DESC")
veiculos = [dict(r) for r in c.fetchall()]
conn.close()

if veiculos:
    st.subheader(f"Frota Cadastrada ({len(veiculos)} veículos)")
    
    # Cabeçalho baseado na planilha
    c_placa, c_prop, c_ren, c_cha, c_mod, c_stat, c_act = st.columns([2, 2, 2, 2, 3, 1, 2])
    c_placa.markdown("**Placa**")
    c_prop.markdown("**Propriedade**")
    c_ren.markdown("**Renavam**")
    c_cha.markdown("**Chassi**")
    c_mod.markdown("**Modelo**")
    c_stat.markdown("**Status**")
    c_act.markdown("**Ações**")
    st.divider()

    for v in veiculos:
        col_p, col_pr, col_r, col_c, col_m, col_s, col_b = st.columns([2, 2, 2, 2, 3, 1, 2])
        
        col_p.write(f"**{v.get('placa', '')}**")
        col_pr.write(v.get('propriedade', '-') or '-')
        col_r.write(v.get('renavam', '-') or '-')
        col_c.write(v.get('chassi', '-') or '-')
        col_m.write(v.get('modelo', '-') or '-')
        
        status_atual = v.get('status', 'Ativo') or 'Ativo'
        col_s.write("🟢" if status_atual == "Ativo" else "🔴")
        
        btn_col1, btn_col2 = col_b.columns(2)
        novo_status = "Inativo" if status_atual == "Ativo" else "Ativo"
        
        if btn_col1.button("🔄", key=f"btn_st_{v['id']}", help="Alterar Status"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("UPDATE veiculos SET status = ? WHERE id = ?", (novo_status, v["id"]))
            conn.commit()
            conn.close()
            st.rerun()

        if btn_col2.button("🗑️", key=f"btn_del_{v['id']}", help="Excluir Veículo"):
            conn = get_connection()
            c = conn.cursor()
            c.execute("DELETE FROM veiculos WHERE id = ?", (v["id"],))
            conn.commit()
            conn.close()
            st.rerun()
else:
    st.info("Nenhum veículo cadastrado no momento.")
