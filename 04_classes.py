"""
04_classes.py — MVP Parte 1 (AV 03) | Projeto Aplicado I | Schulz S.A.

Classes de domínio (Tecnico, Equipamento, Medicao) e classe de conexão e
persistência (BancoDados) sobre SQLite, via módulo padrão `sqlite3`.

Decisões de projeto (ver 06_mvp_parte1.md):
  - Encapsulamento: atributos privados (_x) expostos por @property, com
    validação nos setters. Objeto inválido não chega a existir.
  - Separação de responsabilidades: as classes de domínio não conhecem SQL;
    somente BancoDados fala com o banco.
  - Valores dimensionais em milímetro, comparados com 7 casas decimais (RNF03).
  - Consultas sempre parametrizadas (?), nunca concatenadas.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

CASAS_DECIMAIS = 7          # RNF03: sete casas na base, três só na apresentação
APROVADO = "APROVADO"
REPROVADO = "REPROVADO"


# ---------------------------------------------------------------------------
# Exceção própria da camada de persistência
# ---------------------------------------------------------------------------
class ErroBancoDados(Exception):
    """Erro de acesso ao banco, traduzido a partir de sqlite3.Error."""


# ---------------------------------------------------------------------------
# Funções auxiliares de validação (reutilizadas pelas três classes)
# ---------------------------------------------------------------------------
def _texto_obrigatorio(valor, campo: str) -> str:
    """RH11: remove espaços das pontas e colapsa espaços internos."""
    if valor is None:
        raise ValueError(f"O campo '{campo}' é obrigatório.")
    texto = " ".join(str(valor).split())
    if not texto:
        raise ValueError(f"O campo '{campo}' é obrigatório.")
    return texto


def _numero(valor, campo: str) -> float:
    """Aceita número ou texto com vírgula decimal (RH18)."""
    try:
        if isinstance(valor, str):
            valor = valor.replace(",", ".")
        return round(float(valor), CASAS_DECIMAIS)
    except (TypeError, ValueError):
        raise ValueError(f"O campo '{campo}' deve ser numérico: {valor!r}.")


# ---------------------------------------------------------------------------
# Classe Tecnico
# ---------------------------------------------------------------------------
class Tecnico:
    """Profissional calibrador (metrologista)."""

    def __init__(self, matricula: str, nome: str, setor: str,
                 id_tecnico: Optional[int] = None):
        self._id_tecnico = id_tecnico
        self.matricula = matricula
        self.nome = nome
        self.setor = setor

    @property
    def id_tecnico(self) -> Optional[int]:
        return self._id_tecnico

    @id_tecnico.setter
    def id_tecnico(self, valor: int) -> None:
        self._id_tecnico = valor

    @property
    def matricula(self) -> str:
        return self._matricula

    @matricula.setter
    def matricula(self, valor: str) -> None:
        self._matricula = _texto_obrigatorio(valor, "matricula").upper()

    @property
    def nome(self) -> str:
        return self._nome

    @nome.setter
    def nome(self, valor: str) -> None:
        self._nome = _texto_obrigatorio(valor, "nome")

    @property
    def setor(self) -> str:
        return self._setor

    @setor.setter
    def setor(self, valor: str) -> None:
        self._setor = _texto_obrigatorio(valor, "setor")

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Tecnico":
        return cls(row["matricula"], row["nome"], row["setor"], row["id_tecnico"])

    def __str__(self) -> str:
        return f"Tecnico({self._matricula} - {self._nome}, setor {self._setor})"


# ---------------------------------------------------------------------------
# Classe Equipamento
# ---------------------------------------------------------------------------
class Equipamento:
    """Instrumento ou dispositivo de medição submetido à calibração."""

    FABRICANTE_PADRAO = "Não consta"

    def __init__(self, codigo_tag: str, descricao: str,
                 fabricante: Optional[str] = None,
                 id_equipamento: Optional[int] = None):
        self._id_equipamento = id_equipamento
        self.codigo_tag = codigo_tag
        self.descricao = descricao
        self.fabricante = fabricante

    @property
    def id_equipamento(self) -> Optional[int]:
        return self._id_equipamento

    @id_equipamento.setter
    def id_equipamento(self, valor: int) -> None:
        self._id_equipamento = valor

    @property
    def codigo_tag(self) -> str:
        return self._codigo_tag

    @codigo_tag.setter
    def codigo_tag(self, valor: str) -> None:
        self._codigo_tag = _texto_obrigatorio(valor, "codigo_tag").upper()

    @property
    def descricao(self) -> str:
        return self._descricao

    @descricao.setter
    def descricao(self, valor: str) -> None:
        self._descricao = _texto_obrigatorio(valor, "descricao")

    @property
    def fabricante(self) -> str:
        return self._fabricante

    @fabricante.setter
    def fabricante(self, valor: Optional[str]) -> None:
        # Fabricante é opcional: o certificado modelo traz "Não consta".
        try:
            self._fabricante = _texto_obrigatorio(valor, "fabricante")
        except ValueError:
            self._fabricante = self.FABRICANTE_PADRAO

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Equipamento":
        return cls(row["codigo_tag"], row["descricao"], row["fabricante"],
                   row["id_equipamento"])

    def __str__(self) -> str:
        return f"Equipamento({self._codigo_tag} - {self._descricao}, {self._fabricante})"


# ---------------------------------------------------------------------------
# Classe Medicao
# ---------------------------------------------------------------------------
class Medicao:
    """
    Ensaio de calibração de um parâmetro de um equipamento.

    Regras (AV 01):
      RN02  erro = valor obtido - valor nominal
      RN03  limite superior = nominal + tol_superior
            limite inferior = nominal + tol_inferior (tolerância inferior com sinal)
      RN04  REPROVADO quando (obtido + U) > limite superior
            ou (obtido - U) < limite inferior, sendo U a incerteza expandida.
            Com U = 0 a regra se reduz à comparação direta com a tolerância.
    """

    def __init__(self, id_equipamento: int, id_tecnico: int, parametro: str,
                 valor_nominal, tol_superior, tol_inferior, valor_obtido,
                 incerteza_expandida=0.0, data_calibracao: Optional[str] = None,
                 id_medicao: Optional[int] = None):
        self._id_medicao = id_medicao
        self._id_equipamento = id_equipamento
        self._id_tecnico = id_tecnico
        self.parametro = parametro
        self.valor_nominal = valor_nominal
        self.tol_superior = tol_superior
        self.tol_inferior = tol_inferior
        self.valor_obtido = valor_obtido
        self.incerteza_expandida = incerteza_expandida
        self.data_calibracao = data_calibracao or datetime.now().strftime("%Y-%m-%d")

    # --- identificadores ---------------------------------------------------
    @property
    def id_medicao(self) -> Optional[int]:
        return self._id_medicao

    @id_medicao.setter
    def id_medicao(self, valor: int) -> None:
        self._id_medicao = valor

    @property
    def id_equipamento(self) -> int:
        return self._id_equipamento

    @property
    def id_tecnico(self) -> int:
        return self._id_tecnico

    # --- atributos validados -----------------------------------------------
    @property
    def parametro(self) -> str:
        return self._parametro

    @parametro.setter
    def parametro(self, valor: str) -> None:
        self._parametro = _texto_obrigatorio(valor, "parametro").upper()   # RH14

    @property
    def valor_nominal(self) -> float:
        return self._valor_nominal

    @valor_nominal.setter
    def valor_nominal(self, valor) -> None:
        self._valor_nominal = _numero(valor, "valor_nominal")

    @property
    def tol_superior(self) -> float:
        return self._tol_superior

    @tol_superior.setter
    def tol_superior(self, valor) -> None:
        self._tol_superior = abs(_numero(valor, "tol_superior"))

    @property
    def tol_inferior(self) -> float:
        return self._tol_inferior

    @tol_inferior.setter
    def tol_inferior(self, valor) -> None:
        # RH20: a tolerância inferior é sempre armazenada com sinal negativo.
        numero = _numero(valor, "tol_inferior")
        self._tol_inferior = -abs(numero)

    @property
    def valor_obtido(self) -> float:
        return self._valor_obtido

    @valor_obtido.setter
    def valor_obtido(self, valor) -> None:
        self._valor_obtido = _numero(valor, "valor_obtido")

    @property
    def incerteza_expandida(self) -> float:
        return self._incerteza_expandida

    @incerteza_expandida.setter
    def incerteza_expandida(self, valor) -> None:
        numero = _numero(valor, "incerteza_expandida")
        if numero < 0:
            raise ValueError("A incerteza expandida não pode ser negativa.")
        self._incerteza_expandida = numero

    @property
    def data_calibracao(self) -> str:
        return self._data_calibracao

    @data_calibracao.setter
    def data_calibracao(self, valor: str) -> None:
        # RH22: datas em ISO 8601 no banco.
        try:
            datetime.strptime(valor, "%Y-%m-%d")
        except (TypeError, ValueError):
            raise ValueError(f"Data inválida (use AAAA-MM-DD): {valor!r}.")
        self._data_calibracao = valor

    # --- regras de negócio metrológicas -------------------------------------
    @property
    def limite_superior(self) -> float:
        return round(self._valor_nominal + self._tol_superior, CASAS_DECIMAIS)

    @property
    def limite_inferior(self) -> float:
        return round(self._valor_nominal + self._tol_inferior, CASAS_DECIMAIS)

    def calcular_erro(self) -> float:
        """RN02: erro recalculado a partir do valor obtido e do nominal."""
        return round(self._valor_obtido - self._valor_nominal, CASAS_DECIMAIS)

    def validar_status(self) -> str:
        """RN04: devolve 'APROVADO' ou 'REPROVADO'."""
        maximo = round(self._valor_obtido + self._incerteza_expandida, CASAS_DECIMAIS)
        minimo = round(self._valor_obtido - self._incerteza_expandida, CASAS_DECIMAIS)
        if maximo > self.limite_superior or minimo < self.limite_inferior:
            return REPROVADO
        return APROVADO

    @property
    def status(self) -> str:
        return self.validar_status()

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Medicao":
        return cls(row["id_equipamento"], row["id_tecnico"], row["parametro"],
                   row["valor_nominal"], row["tol_superior"], row["tol_inferior"],
                   row["valor_obtido"], row["incerteza_expandida"],
                   row["data_calibracao"], row["id_medicao"])

    def __str__(self) -> str:
        return (f"Medicao({self._parametro}: obtido {self._valor_obtido:.3f} "
                f"[{self.limite_inferior:.3f} ; {self.limite_superior:.3f}] -> {self.status})")


# ---------------------------------------------------------------------------
# Classe de conexão e persistência
# ---------------------------------------------------------------------------
class BancoDados:
    """Gerencia a conexão SQLite e executa INSERT, SELECT e UPDATE."""

    DDL = """
    CREATE TABLE IF NOT EXISTS tecnicos (
        id_tecnico      INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula       TEXT NOT NULL UNIQUE,
        nome            TEXT NOT NULL,
        setor           TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS equipamentos (
        id_equipamento  INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_tag      TEXT NOT NULL UNIQUE,
        descricao       TEXT NOT NULL,
        fabricante      TEXT
    );
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
    """

    def __init__(self, caminho: str = "calibracao_schulz.db"):
        self._caminho = caminho
        self._conn: Optional[sqlite3.Connection] = None

    # --- conexão -------------------------------------------------------------
    def conectar(self) -> None:
        try:
            self._conn = sqlite3.connect(self._caminho)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")   # SQLite não ativa FK sozinho
        except sqlite3.Error as e:
            raise ErroBancoDados(f"Não foi possível abrir o banco '{self._caminho}': {e}") from e

    def desconectar(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "BancoDados":
        self.conectar()
        return self

    def __exit__(self, *_exc) -> None:
        self.desconectar()

    # --- execução centralizada (transação + tradução de erros) -----------------
    def _executar(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        if self._conn is None:
            raise ErroBancoDados("Conexão não aberta. Chame conectar() antes.")
        try:
            with self._conn:                      # commit automático; rollback em exceção
                return self._conn.execute(sql, params)
        except sqlite3.IntegrityError as e:
            raise ErroBancoDados(f"Violação de integridade: {e}") from e
        except sqlite3.Error as e:
            raise ErroBancoDados(f"Erro SQL: {e}") from e

    def _consultar(self, sql: str, params: tuple = ()) -> List[sqlite3.Row]:
        if self._conn is None:
            raise ErroBancoDados("Conexão não aberta. Chame conectar() antes.")
        try:
            return self._conn.execute(sql, params).fetchall()
        except sqlite3.Error as e:
            raise ErroBancoDados(f"Erro na consulta: {e}") from e

    def criar_tabelas(self) -> None:
        if self._conn is None:
            raise ErroBancoDados("Conexão não aberta. Chame conectar() antes.")
        try:
            with self._conn:
                self._conn.executescript(self.DDL)
        except sqlite3.Error as e:
            raise ErroBancoDados(f"Erro ao criar as tabelas: {e}") from e

    # --- INSERT --------------------------------------------------------------
    def inserir_tecnico(self, t: Tecnico) -> Tecnico:
        cur = self._executar(
            "INSERT INTO tecnicos (matricula, nome, setor) VALUES (?, ?, ?)",
            (t.matricula, t.nome, t.setor))
        t.id_tecnico = cur.lastrowid
        return t

    def inserir_equipamento(self, e: Equipamento) -> Equipamento:
        cur = self._executar(
            "INSERT INTO equipamentos (codigo_tag, descricao, fabricante) VALUES (?, ?, ?)",
            (e.codigo_tag, e.descricao, e.fabricante))
        e.id_equipamento = cur.lastrowid
        return e

    def inserir_medicao(self, m: Medicao) -> Medicao:
        cur = self._executar(
            """INSERT INTO medicoes (id_equipamento, id_tecnico, parametro, valor_nominal,
                   tol_superior, tol_inferior, valor_obtido, incerteza_expandida,
                   erro, status, data_calibracao)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (m.id_equipamento, m.id_tecnico, m.parametro, m.valor_nominal,
             m.tol_superior, m.tol_inferior, m.valor_obtido, m.incerteza_expandida,
             m.calcular_erro(), m.validar_status(), m.data_calibracao))
        m.id_medicao = cur.lastrowid
        return m

    # --- SELECT --------------------------------------------------------------
    def buscar_tecnico_por_matricula(self, matricula: str) -> Optional[Tecnico]:
        linhas = self._consultar("SELECT * FROM tecnicos WHERE matricula = ?",
                                 (matricula.strip().upper(),))
        return Tecnico.from_row(linhas[0]) if linhas else None

    def buscar_equipamento_por_tag(self, codigo_tag: str) -> Optional[Equipamento]:
        linhas = self._consultar("SELECT * FROM equipamentos WHERE codigo_tag = ?",
                                 (codigo_tag.strip().upper(),))
        return Equipamento.from_row(linhas[0]) if linhas else None

    def listar_medicoes_do_equipamento(self, id_equipamento: int) -> List[Medicao]:
        linhas = self._consultar(
            "SELECT * FROM medicoes WHERE id_equipamento = ? ORDER BY id_medicao",
            (id_equipamento,))
        return [Medicao.from_row(l) for l in linhas]

    def relatorio_calibracao(self, codigo_tag: str) -> List[sqlite3.Row]:
        """Consulta relacional: medicoes JOIN equipamentos JOIN tecnicos."""
        return self._consultar(
            """SELECT e.codigo_tag, e.descricao, e.fabricante,
                      t.nome AS tecnico, t.matricula,
                      m.id_medicao, m.parametro, m.valor_nominal, m.tol_superior,
                      m.tol_inferior, m.valor_obtido, m.erro, m.status, m.data_calibracao
                 FROM medicoes m
                 JOIN equipamentos e ON e.id_equipamento = m.id_equipamento
                 JOIN tecnicos     t ON t.id_tecnico     = m.id_tecnico
                WHERE e.codigo_tag = ?
                ORDER BY m.id_medicao""",
            (codigo_tag.strip().upper(),))

    # --- UPDATE --------------------------------------------------------------
    def atualizar_tecnico(self, t: Tecnico) -> None:
        cur = self._executar(
            "UPDATE tecnicos SET matricula = ?, nome = ?, setor = ? WHERE id_tecnico = ?",
            (t.matricula, t.nome, t.setor, t.id_tecnico))
        if cur.rowcount == 0:
            raise ErroBancoDados(f"Técnico id={t.id_tecnico} não encontrado.")

    def atualizar_equipamento(self, e: Equipamento) -> None:
        cur = self._executar(
            "UPDATE equipamentos SET codigo_tag = ?, descricao = ?, fabricante = ? "
            "WHERE id_equipamento = ?",
            (e.codigo_tag, e.descricao, e.fabricante, e.id_equipamento))
        if cur.rowcount == 0:
            raise ErroBancoDados(f"Equipamento id={e.id_equipamento} não encontrado.")

    def atualizar_medicao(self, m: Medicao) -> None:
        """Regrava o valor obtido e recalcula erro e status (nunca confia no valor antigo)."""
        cur = self._executar(
            """UPDATE medicoes SET parametro = ?, valor_nominal = ?, tol_superior = ?,
                   tol_inferior = ?, valor_obtido = ?, incerteza_expandida = ?,
                   erro = ?, status = ?, data_calibracao = ?
               WHERE id_medicao = ?""",
            (m.parametro, m.valor_nominal, m.tol_superior, m.tol_inferior,
             m.valor_obtido, m.incerteza_expandida, m.calcular_erro(),
             m.validar_status(), m.data_calibracao, m.id_medicao))
        if cur.rowcount == 0:
            raise ErroBancoDados(f"Medição id={m.id_medicao} não encontrada.")
