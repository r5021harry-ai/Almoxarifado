"""
Regras de negócio: requisições (saída), entrada de material e ajustes de estoque.
O "carrinho" da requisição em aberto vive em st.session_state (não no banco),
conforme a regra: nada é baixado até a confirmação final.
"""
import datetime as dt
from database.db import get_connection


def buscar_produto_por_codigo(codigo: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM produtos WHERE codigo = ? AND status='Ativo'", (codigo,)).fetchone()
    conn.close()
    return row


def gerar_numero_requisicao(conn) -> str:
    ano = dt.datetime.now().year
    cur = conn.execute(
        "SELECT COUNT(*) AS n FROM requisicoes WHERE numero LIKE ?", (f"REQ-{ano}-%",)
    )
    n = cur.fetchone()["n"] + 1
    return f"REQ-{ano}-{n:06d}"


def conferir_carrinho(carrinho: list):
    """
    Confere se todos os itens do carrinho têm estoque suficiente AGORA (dados frescos do banco).
    Retorna (ok: bool, problemas: list[dict]) sem alterar nada no banco.
    carrinho = [{"produto_id":.., "codigo":.., "nome":.., "quantidade":..}, ...]
    """
    conn = get_connection()
    problemas = []
    for item in carrinho:
        row = conn.execute("SELECT estoque_atual FROM produtos WHERE id = ?", (item["produto_id"],)).fetchone()
        disponivel = row["estoque_atual"] if row else 0
        if disponivel < item["quantidade"]:
            problemas.append({
                "codigo": item["codigo"],
                "nome": item["nome"],
                "disponivel": disponivel,
                "solicitado": item["quantidade"],
            })
    conn.close()
    return (len(problemas) == 0), problemas


def confirmar_saida(carrinho: list, funcionario_id: int, veiculo_id: int, almoxarife_id: int):
    """
    Confirma a saída de forma transacional:
    - reconfere estoque
    - se algo insuficiente, NÃO baixa nada e retorna erro
    - senão, cria requisição + itens + movimentações e baixa o estoque
    """
    ok, problemas = conferir_carrinho(carrinho)
    if not ok:
        return {"sucesso": False, "problemas": problemas, "numero": None}

    conn = get_connection()
    try:
        numero = gerar_numero_requisicao(conn)
        agora = dt.datetime.now()
        data_str = agora.strftime("%Y-%m-%d")
        hora_str = agora.strftime("%H:%M:%S")

        cur = conn.execute(
            "INSERT INTO requisicoes (numero, data, hora, funcionario_id, veiculo_id, almoxarife_id, status) "
            "VALUES (?,?,?,?,?,?,'Confirmada')",
            (numero, data_str, hora_str, funcionario_id, veiculo_id, almoxarife_id),
        )
        requisicao_id = cur.lastrowid

        for item in carrinho:
            row = conn.execute("SELECT estoque_atual FROM produtos WHERE id = ?", (item["produto_id"],)).fetchone()
            estoque_anterior = row["estoque_atual"]
            estoque_posterior = estoque_anterior - item["quantidade"]
            if estoque_posterior < 0:
                raise ValueError(f"Estoque insuficiente para {item['nome']} durante a confirmação.")

            conn.execute(
                "UPDATE produtos SET estoque_atual = ? WHERE id = ?",
                (estoque_posterior, item["produto_id"]),
            )
            conn.execute(
                "INSERT INTO requisicao_itens (requisicao_id, produto_id, quantidade, estoque_anterior, estoque_posterior) "
                "VALUES (?,?,?,?,?)",
                (requisicao_id, item["produto_id"], item["quantidade"], estoque_anterior, estoque_posterior),
            )
            conn.execute(
                "INSERT INTO movimentacoes (data, hora, produto_id, tipo, quantidade, estoque_anterior, "
                "estoque_posterior, requisicao_id, usuario_id) VALUES (?,?,?,?,?,?,?,?,?)",
                (data_str, hora_str, item["produto_id"], "SAIDA", item["quantidade"],
                 estoque_anterior, estoque_posterior, requisicao_id, almoxarife_id),
            )

        conn.commit()
        return {"sucesso": True, "problemas": [], "numero": numero, "requisicao_id": requisicao_id}
    except Exception as e:
        conn.rollback()
        return {"sucesso": False, "problemas": [{"erro": str(e)}], "numero": None}
    finally:
        conn.close()


def registrar_entrada(produto_id: int, quantidade: float, usuario_id: int,
                       fornecedor: str = "", nota_fiscal: str = "", observacao: str = ""):
    conn = get_connection()
    try:
        row = conn.execute("SELECT estoque_atual FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        if row is None:
            raise ValueError("Produto não encontrado.")
        estoque_anterior = row["estoque_atual"]
        estoque_posterior = estoque_anterior + quantidade

        conn.execute("UPDATE produtos SET estoque_atual = ? WHERE id = ?", (estoque_posterior, produto_id))

        agora = dt.datetime.now()
        conn.execute(
            "INSERT INTO movimentacoes (data, hora, produto_id, tipo, quantidade, estoque_anterior, "
            "estoque_posterior, usuario_id, fornecedor, nota_fiscal, observacao) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (agora.strftime("%Y-%m-%d"), agora.strftime("%H:%M:%S"), produto_id, "ENTRADA",
             quantidade, estoque_anterior, estoque_posterior, usuario_id, fornecedor, nota_fiscal, observacao),
        )
        conn.commit()
        return {"sucesso": True, "estoque_posterior": estoque_posterior}
    except Exception as e:
        conn.rollback()
        return {"sucesso": False, "erro": str(e)}
    finally:
        conn.close()


def ajuste_manual(produto_id: int, novo_estoque: float, usuario_id: int, motivo: str):
    """Ajuste excepcional de estoque - somente administrador (checar role antes de chamar)."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT estoque_atual FROM produtos WHERE id = ?", (produto_id,)).fetchone()
        estoque_anterior = row["estoque_atual"]

        conn.execute("UPDATE produtos SET estoque_atual = ? WHERE id = ?", (novo_estoque, produto_id))

        agora = dt.datetime.now()
        conn.execute(
            "INSERT INTO movimentacoes (data, hora, produto_id, tipo, quantidade, estoque_anterior, "
            "estoque_posterior, usuario_id, observacao) VALUES (?,?,?,?,?,?,?,?,?)",
            (agora.strftime("%Y-%m-%d"), agora.strftime("%H:%M:%S"), produto_id, "AJUSTE",
             novo_estoque - estoque_anterior, estoque_anterior, novo_estoque, usuario_id, motivo),
        )
        conn.execute(
            "INSERT INTO auditoria (usuario_id, data, hora, operacao, produto_id, quantidade, "
            "estoque_anterior, estoque_posterior, motivo) VALUES (?,?,?,?,?,?,?,?,?)",
            (usuario_id, agora.strftime("%Y-%m-%d"), agora.strftime("%H:%M:%S"), "AJUSTE_MANUAL",
             produto_id, novo_estoque - estoque_anterior, estoque_anterior, novo_estoque, motivo),
        )
        conn.commit()
        return {"sucesso": True}
    except Exception as e:
        conn.rollback()
        return {"sucesso": False, "erro": str(e)}
    finally:
        conn.close()
