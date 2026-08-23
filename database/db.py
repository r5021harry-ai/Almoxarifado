"""
Conexão com o banco SQLite + inicialização do schema + usuário admin padrão.
"""
import os
import sqlite3
import hashlib
import secrets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database", "estoque.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_pin(pin: str, salt: str) -> str:
    return hashlib.sha256((salt + pin).encode("utf-8")).hexdigest()


def init_db(reset: bool = False):
    """Cria o schema. Se reset=True, apaga o banco existente antes."""
    if reset and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()

    # Cria usuário administrador padrão se não existir nenhum usuário
    cur = conn.execute("SELECT COUNT(*) AS n FROM usuarios")
    if cur.fetchone()["n"] == 0:
        salt = secrets.token_hex(8)
        pin_hash = hash_pin("1234", salt)
        conn.execute(
            "INSERT INTO usuarios (nome, username, pin_hash, role, status) VALUES (?,?,?,?,?)",
            ("Administrador", "admin", f"{salt}${pin_hash}", "admin", "Ativo"),
        )
        conn.commit()
        print("Usuário padrão criado -> usuário: admin | PIN: 1234 (TROQUE DEPOIS)")

    conn.close()


def verify_pin(username: str, pin: str):
    """Retorna a linha do usuário se username+pin forem válidos, senão None."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM usuarios WHERE username = ? AND status = 'Ativo'", (username,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    try:
        salt, stored_hash = row["pin_hash"].split("$", 1)
    except ValueError:
        return None
    if hash_pin(pin, salt) == stored_hash:
        return row
    return None


if __name__ == "__main__":
    init_db()
    print(f"Banco inicializado em: {DB_PATH}")
