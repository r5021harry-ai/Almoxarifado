"""
Importa a lista de 394 produtos (Estoque.xlsx / relatório 286) para o banco.
Classifica automaticamente a SEÇÃO de cada produto por palavras-chave.
Pode ser reexecutado: atualiza produtos existentes (por código) e insere novos.
"""
import csv
import re
import sqlite3
import sys
import os

RAW_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "produtos_raw.txt")
CSV_OUT = os.path.join(os.path.dirname(__file__), "..", "data", "produtos.csv")
DB_FILE = os.path.join(os.path.dirname(__file__), "..", "database", "estoque.db")

# ---------------------------------------------------------------------
# REGRAS DE CLASSIFICAÇÃO POR SEÇÃO (editável)
# A ordem importa: a primeira regra que bater define a seção.
# Adicione/edite palavras-chave livremente conforme a realidade da oficina.
# ---------------------------------------------------------------------
REGRAS_SECAO = [
    ("Thermo King", [
        "THERMO KING", "THERMOKING", " TK ", "TK3", "TK370", "EVAPORADOR",
        "CONTROLADOR EVERY", "R-404A", "R404A", "GAS R22", "GAS R 22",
        "GAS R141B", "COMPRESSOR", "BITZER", "SPRING BRAKE", "SOLENOIDE MOTOR PARTIDA",
    ]),
    ("Elétrica", [
        "LAMPADA", "LANTERNA", "FUSIVEL", "RELE ", "RELE4", "SOLENOIDE",
        "SENSOR", "BATERIA", "CHICOTE", "TERMINAL ELETRICO", "TERMINAL ISOLADO",
        "TERMINAL OLHAL", "BUZINA", "PLACA ELET", "FITA ISOLANTE", "ELETROV",
        "ELETROVENTILADOR", "FAROL", "PISCA", "MOTOR DE PARTIDA", "MOTOR DO LIMPADOR",
        "BOBINA", "CONECTOR", "BOTAO PARTIDA", "BOTAO DE PARTIDA", "CONTROLADOR DIGITAL",
        "TRANSDUTOR", "INTERRUPTOR",
    ]),
    ("Ferramentas", [
        "CHAVE ", "CHAVE COMBINADA", "CHAVE DE L", "CHAVE ALLEN", "CHAVE CANHAO",
        "CHAVE CATRACA", "CHAVE GRIFO", "CHAVE INGLESA", "CHAVE AJUSTAVEL",
        "MARRETA", "ALICATE", "LIXA", "LIXADEIRA", "FURADEIRA", "ESMERILHADEIRA",
        "MACACO HIDRAULICO", "MACACO HIDRULICO", "JOGO DE CHAVE", "JOGO SOQUETE",
        "SOQUETE", "RETIFICA", "ESTOJO CHAVE", "CAIXA FERRAMENTA", "FERRO DE SOLDA",
        "TALHADEIRA", "KIT MARTELETE", "PROPULSORA PNEUMATICA", "PISTOLA DE PINTURA",
        "PISTOLA PNEUMATICA", "PISTOLA P/ PINTURA", "MAQUINA DE POLIR", "ESCADA",
        "CALIBRADOR", "MEDIDOR DE DESGASTE", "ALICATE REBITADOR", "ALICATE AMPERIMETRO",
        "MACARICO", "CINTA LISA", "CHAVE CORRENTE", "SACA POLIA", "SACA FILTRO",
        "ESPATULA", "FLANGEADOR", "CHAVE CINTA", "CHAVE GARRAS", "CHAVE SEXTAVADA",
        "CHAVE DE RODA", "CHAVE DE FENDA", "CHAVE DE PHILIPS", "CHAVE ESTRELA",
        "CHAVE RODA", "CHAVE LONGA",
    ]),
    ("EPI / Segurança", [
        "CINTO DE SEGURANCA", "TALABARTE", "CAPACETE", "LUVA ALTA TENSAO",
        "LUVA COBERTURA", "COLETE",
    ]),
    ("Pneus e Rodas", [
        "PNEU ", "CALIBRADOR DE PNEUS", "REFIL AUTOMOVEL PNEU", "ESPATULA PARA PNEUS",
        "KIT ESPATULA TRUCK",
    ]),
    ("Freio e Suspensão", [
        "FREIO", "LONA", "PATIM", "CUICA", "DIAFRAGMA", "AMORTECEDOR", "MOLA ",
        "FEIXE DE MOLA", "CATRACA DE FREIO", "CATRACA FREIO",
    ]),
    ("Motor e Transmissão", [
        "FILTRO", "OLEO", "CORREIA", "RETENTOR", "JUNTA ", "EMBUCHAMENTO",
        "ROLAMENTO", "EMBREAGEM", "CAMISA DO CILINDRO", "BIELA", "PISTAO",
        "TERMOSTATO", "BOMBA AGUA", "BOMBA D'AGUA", "BOMBA DIRECAO",
        "CARTER", "ANEIS PISTAO", "ADITIVO RADIADOR", "TAMPA RESERVATORIO RADIADOR",
        "VEDA VAZAMENTO RADIADOR", "ARLA", "DIESEL",
    ]),
    ("Direção e Cabine", [
        "DIRECAO", "MACANETA", "FECHADURA", "VIDRO", "RETROVISOR", "ESPELHO",
        "TRAVA ARANHA", "TRAVA ROLETE", "COXIM", "CAPO", "PORTA ESCOVA",
        "MANIVELA LEVANTAR VIDRO", "TRINCO",
    ]),
    ("Fixação e Diversos (parafusos, arruelas, etc.)", [
        "PARAFUSO", "PORCA", "ARRUELA", "REBITE", "ANILHA", "PINO ", "CONTRA PINO",
        "GRAXEIRA", "INSERT", "INSERTO", "CONEXAO", "PLUG BLOCO", "GUIA DE VALVULA",
        "ESPACADOR", "CASQUILHO", "BRONZINA",
    ]),
    ("Pintura e Química", [
        "TINTA", "BRASILUX", "THINNER", "SILICONE", "ENDURECEDOR", "COLA ",
        "DETERGENTE", "DESENGRAXANTE", "METAZIL", "LIMPA CONTATOS", "LIMPA CARTER",
        "LIMPA PARABRISA", "FLUIDO DE FREIO",
    ]),
]

DEFAULT_SECAO = "Geral"


def classificar_secao(descricao: str) -> str:
    desc = f" {descricao.upper()} "
    for secao, palavras in REGRAS_SECAO:
        for p in palavras:
            if p in desc:
                return secao
    return DEFAULT_SECAO


LINE_RE = re.compile(
    r"^\s*\d+\s+(?P<codigo>\d+)\s+(?P<descricao>.+?)\s+"
    r"(?P<emb>\S+)\s+(?P<un>\S+)\s+(?P<estoque>[\d\.]+,\d{2})\s*$"
)


def parse_raw(path):
    produtos = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.rstrip("\n")
            if not line.strip():
                continue
            m = LINE_RE.match(line)
            if not m:
                print(f"[AVISO] linha {lineno} não reconhecida: {line!r}", file=sys.stderr)
                continue
            codigo = m.group("codigo")
            descricao = m.group("descricao").strip()
            unidade = m.group("un").strip()
            estoque_str = m.group("estoque").replace(".", "").replace(",", ".")
            estoque = float(estoque_str)
            secao = classificar_secao(descricao)
            produtos.append({
                "codigo": codigo,
                "nome": descricao,
                "descricao": descricao,
                "categoria": "",
                "secao": secao,
                "fabricante": "",
                "numero_peca": "",
                "unidade": unidade,
                "localizacao": "",
                "estoque_atual": estoque,
                "estoque_minimo": 0,
                "estoque_maximo": 0,
                "status": "Ativo",
            })
    return produtos


def write_csv(produtos, path):
    campos = ["codigo", "nome", "descricao", "categoria", "secao", "fabricante",
              "numero_peca", "unidade", "localizacao", "estoque_atual",
              "estoque_minimo", "estoque_maximo", "status"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for p in produtos:
            w.writerow(p)


def import_to_db(produtos, db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    novos, atualizados = 0, 0
    for p in produtos:
        cur.execute("SELECT id, estoque_atual FROM produtos WHERE codigo = ?", (p["codigo"],))
        row = cur.fetchone()
        if row is None:
            cur.execute("""
                INSERT INTO produtos
                (codigo, nome, descricao, categoria, secao, fabricante, numero_peca,
                 unidade, localizacao, estoque_atual, estoque_minimo, estoque_maximo, status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (p["codigo"], p["nome"], p["descricao"], p["categoria"], p["secao"],
                  p["fabricante"], p["numero_peca"], p["unidade"], p["localizacao"],
                  p["estoque_atual"], p["estoque_minimo"], p["estoque_maximo"], p["status"]))
            novos += 1
        else:
            # Mantém o estoque atual já existente no banco (não sobrescreve retiradas feitas
            # no sistema); apenas atualiza dados cadastrais e seção.
            cur.execute("""
                UPDATE produtos SET nome=?, descricao=?, secao=?, unidade=?
                WHERE codigo=?
            """, (p["nome"], p["descricao"], p["secao"], p["unidade"], p["codigo"]))
            atualizados += 1
    conn.commit()
    conn.close()
    return novos, atualizados


if __name__ == "__main__":
    produtos = parse_raw(RAW_FILE)
    print(f"Produtos lidos do arquivo bruto: {len(produtos)}")
    write_csv(produtos, CSV_OUT)
    print(f"CSV gerado em: {CSV_OUT}")

    # resumo por seção
    from collections import Counter
    c = Counter(p["secao"] for p in produtos)
    print("\nResumo por seção:")
    for secao, qtd in c.most_common():
        print(f"  {secao:45s} {qtd:4d}")

    if os.path.exists(DB_FILE):
        novos, atualizados = import_to_db(produtos, DB_FILE)
        print(f"\nBanco atualizado: {novos} novos, {atualizados} atualizados.")
    else:
        print(f"\n[INFO] Banco {DB_FILE} ainda não existe. Rode database/init_db.py primeiro.")
