-- 03_banco.sql — Banco relacional SQLite | Projeto Aplicado I | Schulz S.A.
-- Mesmo esquema criado por BancoDados.criar_tabelas() em 04_classes.py.
-- Execução: sqlite3 calibracao_schulz.db < 03_banco.sql

PRAGMA foreign_keys = ON;

-- Profissional calibrador (metrologista)
CREATE TABLE IF NOT EXISTS tecnicos (
    id_tecnico      INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula       TEXT NOT NULL UNIQUE,
    nome            TEXT NOT NULL,
    setor           TEXT NOT NULL
);

-- Instrumento ou dispositivo de medição calibrado
CREATE TABLE IF NOT EXISTS equipamentos (
    id_equipamento  INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_tag      TEXT NOT NULL UNIQUE,
    descricao       TEXT NOT NULL,
    fabricante      TEXT
);

-- Ensaio de calibração de um parâmetro (valores em milímetro)
CREATE TABLE IF NOT EXISTS medicoes (
    id_medicao           INTEGER PRIMARY KEY AUTOINCREMENT,
    id_equipamento       INTEGER NOT NULL REFERENCES equipamentos(id_equipamento),
    id_tecnico           INTEGER NOT NULL REFERENCES tecnicos(id_tecnico),
    parametro            TEXT NOT NULL,
    valor_nominal        REAL NOT NULL,
    tol_superior         REAL NOT NULL,
    tol_inferior         REAL NOT NULL,
    valor_obtido         REAL NOT NULL,
    incerteza_expandida  REAL NOT NULL DEFAULT 0,
    erro                 REAL NOT NULL,
    status               TEXT NOT NULL CHECK (status IN ('APROVADO', 'REPROVADO')),
    data_calibracao      TEXT NOT NULL
);
