-- Schema do Almoxarifado

CREATE TABLE IF NOT EXISTS produtos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo TEXT UNIQUE NOT NULL,
    nome TEXT NOT NULL,
    descricao TEXT,
    categoria TEXT,
    secao TEXT,
    fabricante TEXT,
    numero_peca TEXT,
    unidade TEXT DEFAULT 'UN',
    localizacao TEXT,
    estoque_atual REAL NOT NULL DEFAULT 0,
    estoque_minimo REAL NOT NULL DEFAULT 0,
    estoque_maximo REAL NOT NULL DEFAULT 0,
    foto_path TEXT,
    qrcode_path TEXT,
    status TEXT NOT NULL DEFAULT 'Ativo',
    criado_em TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS funcionarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    funcao TEXT,
    status TEXT NOT NULL DEFAULT 'Ativo'
);

CREATE TABLE IF NOT EXISTS veiculos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    placa TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL DEFAULT 'Ativo'
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    username TEXT UNIQUE NOT NULL,
    pin_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'almoxarife', -- 'admin' ou 'almoxarife'
    status TEXT NOT NULL DEFAULT 'Ativo'
);

CREATE TABLE IF NOT EXISTS requisicoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT UNIQUE NOT NULL,
    data TEXT NOT NULL,
    hora TEXT NOT NULL,
    funcionario_id INTEGER NOT NULL REFERENCES funcionarios(id),
    veiculo_id INTEGER NOT NULL REFERENCES veiculos(id),
    almoxarife_id INTEGER NOT NULL REFERENCES usuarios(id),
    status TEXT NOT NULL DEFAULT 'Confirmada' -- Confirmada / Cancelada
);

CREATE TABLE IF NOT EXISTS requisicao_itens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requisicao_id INTEGER NOT NULL REFERENCES requisicoes(id),
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    quantidade REAL NOT NULL,
    estoque_anterior REAL NOT NULL,
    estoque_posterior REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    hora TEXT NOT NULL,
    produto_id INTEGER NOT NULL REFERENCES produtos(id),
    tipo TEXT NOT NULL, -- ENTRADA / SAIDA / AJUSTE
    quantidade REAL NOT NULL,
    estoque_anterior REAL NOT NULL,
    estoque_posterior REAL NOT NULL,
    requisicao_id INTEGER REFERENCES requisicoes(id),
    usuario_id INTEGER REFERENCES usuarios(id),
    fornecedor TEXT,
    nota_fiscal TEXT,
    observacao TEXT
);

CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER REFERENCES usuarios(id),
    data TEXT NOT NULL,
    hora TEXT NOT NULL,
    operacao TEXT NOT NULL,
    produto_id INTEGER REFERENCES produtos(id),
    quantidade REAL,
    estoque_anterior REAL,
    estoque_posterior REAL,
    motivo TEXT
);

CREATE INDEX IF NOT EXISTS idx_produtos_codigo ON produtos(codigo);
CREATE INDEX IF NOT EXISTS idx_produtos_secao ON produtos(secao);
CREATE INDEX IF NOT EXISTS idx_mov_produto ON movimentacoes(produto_id);
CREATE INDEX IF NOT EXISTS idx_mov_data ON movimentacoes(data);
CREATE INDEX IF NOT EXISTS idx_req_data ON requisicoes(data);
CREATE INDEX IF NOT EXISTS idx_req_itens_req ON requisicao_itens(requisicao_id);
