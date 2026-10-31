# MVP Parte 1 — Classes de Domínio e Persistência em SQLite

**Unidade curricular:** Projeto Aplicado I — UniSENAI/SC
**Empresa parceira:** Schulz S.A. — Laboratório de Metrologia
**Docentes:** Prof. MSc. Hugo Menezes Barra e Prof. Rodrigo Losina
**Equipe:** Carolin Roberta Bueno, Emanuelly Luize Marchi Freitas, Gabriel de Morais Teixeira e Victor Fernandes Guedes
**Entrega:** AV 03 (Tema 03) — prazo 03/11/2026
**Linguagem:** Python 3 (módulo padrão `sqlite3`, sem dependências externas)

---

## 1. Objetivo e escopo

Esta etapa transforma a modelagem da AV 02 (tabelas `tecnicos`, `equipamentos` e `medicoes`) em código executável. O MVP Parte 1 entrega:

- três classes de domínio (`Tecnico`, `Equipamento`, `Medicao`), com validação própria;
- a validação metrológica `APROVADO`/`REPROVADO` dentro de `Medicao`;
- uma classe de conexão e persistência (`BancoDados`) com INSERT, SELECT, UPDATE e DELETE (CRUD);
- um script de demonstração (`05_main.py`) com inserção, consulta com JOIN e relatório no terminal.

Ficam para a Parte 2: leitura do relatório da MMC (Excel), regras de higienização (RH01–RH30), cálculo completo da incerteza (EA-4/02) e geração do PDF do certificado.

## 2. Arquivos e execução

| Arquivo | Função |
|---|---|
| `04_classes.py` | Classes `Tecnico`, `Equipamento`, `Medicao`, `BancoDados` e a exceção `ErroBancoDados` |
| `05_main.py` | Demonstração do fluxo completo no terminal |
| `06_mvp_parte1.md` | Esta documentação |

Para executar, basta ter o Python 3 instalado e rodar, na pasta dos arquivos:

```
python 05_main.py
```

O script recria o arquivo `calibracao_schulz.db` a cada execução, para que a demonstração seja repetível. Como o nome `04_classes.py` começa com número, o `05_main.py` o importa com `importlib.import_module("04_classes")`.

## 3. Padrões de POO utilizados

**Encapsulamento.** Todos os atributos são privados por convenção (`_nome`) e expostos por `@property`. A validação fica nos setters, então um objeto inválido nunca chega a existir. Exemplo: `Medicao.valor_obtido = "abc"` levanta `ValueError` antes de qualquer acesso ao banco.

**Normalização no próprio setter.** As regras de higienização da AV 02 que dependem de um único campo foram aplicadas na entrada de dados:

| Regra | Onde é aplicada |
|---|---|
| RH11 — remover espaços extras | `_texto_obrigatorio()`, usada por todos os campos de texto |
| RH14 — parâmetro em caixa alta | setter de `Medicao.parametro` |
| RH18 — vírgula decimal | `_numero()`, usada por todos os campos numéricos |
| RH20 — tolerância inferior sempre com sinal negativo | setter de `Medicao.tol_inferior` |
| RH22 — data em ISO 8601 | setter de `Medicao.data_calibracao` |

**Separação de responsabilidades.** As classes de domínio não contêm SQL. Somente `BancoDados` conhece o banco. Se a Schulz trocar o SQLite por outro banco, as classes de domínio não mudam.

**Método de fábrica.** Cada classe de domínio tem `from_row()`, que reconstrói o objeto a partir de uma linha do banco (`sqlite3.Row`). Isso evita montar objetos manualmente em cada consulta.

**Gerenciador de contexto.** `BancoDados` implementa `__enter__` e `__exit__`, e por isso é usado com `with`. A conexão é sempre fechada, mesmo quando ocorre erro.

**Exceção própria.** `ErroBancoDados` traduz os erros do `sqlite3` para uma mensagem legível, sem expor a camada de baixo nível ao restante do sistema.

**Valores derivados calculados pelo sistema.** `erro` e `status` nunca são digitados pelo usuário: `BancoDados` os calcula por `calcular_erro()` e `validar_status()` no momento do INSERT e do UPDATE. Isso evita o problema detectado na AV 01, em que a coluna *Deviation* do relatório divergia da diferença real entre valor obtido e nominal (RN02).

## 4. Diagrama de classes (UML textual)

```
+-------------------------------+        +----------------------------------+
| Tecnico                       |        | Equipamento                      |
+-------------------------------+        +----------------------------------+
| - _id_tecnico : int           |        | - _id_equipamento : int          |
| - _matricula : str            |        | - _codigo_tag : str              |
| - _nome : str                 |        | - _descricao : str               |
| - _setor : str                |        | - _fabricante : str              |
+-------------------------------+        +----------------------------------+
| + from_row(row) : Tecnico     |        | + from_row(row) : Equipamento    |
| + __str__() : str             |        | + __str__() : str                |
+---------------+---------------+        +-----------------+----------------+
                | 1                                        | 1
                |                                          |
                | N                                        | N
        +-------+------------------------------------------+-------+
        | Medicao                                                  |
        +----------------------------------------------------------+
        | - _id_medicao : int                                      |
        | - _id_equipamento : int   (FK)                           |
        | - _id_tecnico : int       (FK)                           |
        | - _parametro : str                                       |
        | - _valor_nominal, _tol_superior, _tol_inferior : float   |
        | - _valor_obtido, _incerteza_expandida : float            |
        | - _data_calibracao : str  (AAAA-MM-DD)                   |
        +----------------------------------------------------------+
        | + limite_superior : float   (propriedade)                |
        | + limite_inferior : float   (propriedade)                |
        | + calcular_erro() : float                                |
        | + validar_status() : str    ('APROVADO' | 'REPROVADO')  |
        | + from_row(row) : Medicao                                |
        +----------------------------+-----------------------------+
                                     ^
                                     | usa (persiste e consulta)
        +----------------------------+-----------------------------+
        | BancoDados                                               |
        +----------------------------------------------------------+
        | - _caminho : str                                         |
        | - _conn : sqlite3.Connection                             |
        +----------------------------------------------------------+
        | + conectar() / desconectar()                             |
        | + __enter__() / __exit__()                               |
        | + criar_tabelas()                                        |
        | + inserir_tecnico / inserir_equipamento / inserir_medicao|
        | + buscar_tecnico_por_matricula(matricula)                |
        | + buscar_equipamento_por_tag(tag)                        |
        | + listar_medicoes_do_equipamento(id)                     |
        | + relatorio_calibracao(tag) : JOIN das 3 tabelas         |
        | + atualizar_tecnico / atualizar_equipamento /            |
        |   atualizar_medicao                                      |
        | + excluir_tecnico / excluir_equipamento / excluir_medicao|
        | - _executar(sql, params) / _consultar(sql, params)       |
        +----------------------------------------------------------+
        ErroBancoDados (Exception) é levantada por BancoDados.
```

**Relacionamentos.** Um técnico executa muitas medições (1:N). Um equipamento recebe muitas medições (1:N). Uma `Medicao` guarda apenas os ids das duas chaves estrangeiras, e a ligação com os nomes é feita pelo JOIN no banco.

## 5. Modelo relacional implementado

```sql
CREATE TABLE tecnicos (
    id_tecnico      INTEGER PRIMARY KEY AUTOINCREMENT,
    matricula       TEXT NOT NULL UNIQUE,
    nome            TEXT NOT NULL,
    setor           TEXT NOT NULL
);
CREATE TABLE equipamentos (
    id_equipamento  INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_tag      TEXT NOT NULL UNIQUE,
    descricao       TEXT NOT NULL,
    fabricante      TEXT
);
CREATE TABLE medicoes (
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
```

Duas garantias merecem destaque. O SQLite não ativa chaves estrangeiras por padrão, por isso `BancoDados.conectar()` executa `PRAGMA foreign_keys = ON`. E o `CHECK` em `status` impede que um valor fora de `APROVADO`/`REPROVADO` seja gravado, mesmo por acesso direto ao banco.


## 6. Regras de negócio implementadas em `Medicao`

Todas vêm da especificação da AV 01.

| Regra | Implementação |
|---|---|
| **RN02** — erro = valor obtido − valor nominal, sempre recalculado | `calcular_erro()` |
| **RN03** — limite superior = nominal + tol. superior; limite inferior = nominal + tol. inferior (com sinal) | propriedades `limite_superior` e `limite_inferior` |
| **RN04** — reprovado quando obtido + U > limite superior ou obtido − U < limite inferior | `validar_status()` |
| **RNF03** — sete casas decimais na base | constante `CASAS_DECIMAIS = 7` aplicada em todos os cálculos |

O parâmetro `incerteza_expandida` (U) é opcional e vale zero por padrão, o que reduz a regra à comparação direta entre valor obtido e tolerância, como pede o roteiro. Na demonstração usamos U = 0,002 mm, valor do certificado modelo nº 00091/2026. O arredondamento a sete casas antes de comparar evita erros de ponto flutuante nas fronteiras da tolerância.

## 7. Tratamento de erros

Há duas camadas.

**Validação de dados (`ValueError`)**, antes de qualquer acesso ao banco:

| Situação | Resultado |
|---|---|
| Valor numérico inválido (`"abc"`) | `ValueError: O campo 'valor_obtido' deve ser numérico` |
| Campo de texto vazio ou só com espaços | `ValueError: O campo 'parametro' é obrigatório` |
| Data fora do padrão AAAA-MM-DD | `ValueError: Data inválida` |
| Incerteza negativa | `ValueError` |

**Erros SQL (`ErroBancoDados`)**, traduzidos em `BancoDados._executar()`:

| Situação | Origem no SQLite | Tratamento |
|---|---|---|
| TAG ou matrícula duplicada | `IntegrityError` (UNIQUE) | `ErroBancoDados: Violação de integridade` |
| Equipamento ou técnico inexistente | `IntegrityError` (FOREIGN KEY) | `ErroBancoDados: Violação de integridade` |
| UPDATE ou DELETE em id que não existe | `rowcount == 0` | `ErroBancoDados: Medição id=... não encontrada` |
| Excluir equipamento ou técnico que possui medições | `IntegrityError` (FOREIGN KEY) | `ErroBancoDados: Violação de integridade` |
| Conexão não aberta | verificação prévia | `ErroBancoDados: Conexão não aberta` |
| Qualquer outro erro do banco | `sqlite3.Error` | `ErroBancoDados: Erro SQL` |

**Transações.** Cada escrita roda dentro de `with self._conn:`, que confirma (commit) no sucesso e desfaz (rollback) em qualquer exceção. Um INSERT que falha não deixa registro parcial.

**Segurança.** Todas as consultas usam parâmetros (`?`). Nenhum valor digitado é concatenado ao SQL, o que elimina a injeção de SQL.

## 8. Validação do fluxo funcional

Executamos `python 05_main.py` e conferimos cada etapa.

| Etapa | Resultado observado |
|---|---|
| Criação das tabelas | 3 tabelas criadas sem erro |
| Instanciação e INSERT | 2 técnicos, 1 equipamento (703.1208) e 14 medições gravados; textos normalizados (`"  Jose Alcides   Rosa Junior "` virou `Jose Alcides Rosa Junior`; `mat-0001` virou `MAT-0001`); fabricante ausente gravado como `Não consta`, igual ao certificado |
| Consulta com JOIN | relatório com 14 parâmetros: 8 aprovados e 6 reprovados |
| UPDATE | `62P_POSIÇÃO 1` corrigida de 0,430 para 0,090 (digitada com vírgula): status passou de `REPROVADO` para `APROVADO` e o erro foi recalculado para 0,090 |
| DELETE | medição de teste inserida e excluída; total de medições voltou de 15 para 14 |
| Tratamento de erros | os 7 cenários de falha foram capturados com mensagem clara, sem interromper o programa |
| Relatório final | 9 aprovados e 5 reprovados, coerente com o UPDATE |

**Conferência com o documento real.** Os 14 parâmetros inseridos vêm do certificado de calibração nº 00091/2026. Os valores de **erro** calculados pelo sistema (0,002; 0,027; 0,004; 0,430; 0,003; 0,245; 0,004; 0,959; 0,006; 0,236; 0,001; 0,132; 0,004; 0,868) coincidem com a coluna *Erro* do certificado.

**Ponto de atenção para o cliente.** Os seis parâmetros de posição aparecem como reprovados porque o valor obtido supera a tolerância de 0,100 mm. O próprio certificado modelo mostra esses valores, então o resultado reflete o dado de origem. Vale validar com o João Carlos se o certificado modelo foi preenchido apenas como exemplo.

**Saída de exemplo (trecho do relatório):**

```
Equipamento : 703.1208 - Dispositivo de controle (fabricante: Não consta)
Técnico     : Jose Alcides Rosa Junior (matrícula MAT-0001)
Data        : 2026-08-26    Unidade: mm
 ID  PARÂMETRO             NOMINAL    TOL+    TOL-   OBTIDO    ERRO  STATUS
  1  PLANICIDADE_REF         0.000   0.050   0.000    0.002   0.002  APROVADO
  3  62P_DIÂMETRO 1          6.075   0.010  -0.010    6.079   0.004  APROVADO
  4  62P_POSIÇÃO 1           0.000   0.100   0.000    0.430   0.430  REPROVADO
Total: 14 parâmetros | aprovados: 8 | reprovados: 6
```

## 9. Rastreabilidade com os requisitos da AV 01

| Requisito | Atendimento no MVP Parte 1 |
|---|---|
| RF04 — calcular erro de cada característica | `Medicao.calcular_erro()` |
| RF06 — limites de tolerância e situação por característica | `limite_superior`, `limite_inferior`, `validar_status()` |
| RF07 — destacar características reprovadas | coluna `STATUS` do relatório |
| RF09 — manter cadastros | `inserir_*`, `buscar_*`, `atualizar_*` e `excluir_*` de técnicos e equipamentos |
| RF12 — consultar calibrações | `relatorio_calibracao()` e `listar_medicoes_do_equipamento()` |
| RNF03 — precisão de sete casas | `CASAS_DECIMAIS = 7` |
| RNF04 — rastreabilidade | data, técnico e equipamento gravados em cada medição |

## 10. Limitações e próximos passos (Parte 2)

- Ler o relatório da MMC (Excel) e consolidar os dois blocos de medição em Medida 1 e Medida 2 (RF01, RF02).
- Aplicar as regras de higienização RH01–RH30 e registrar o log de ingestão (RF03).
- Calcular o orçamento de incerteza conforme a EA-4/02, em vez de receber U como parâmetro (RF05).
- Cadastrar padrões (MMC 500.011) e bloquear a emissão quando o padrão estiver vencido (RN08).
- Gerar o certificado em PDF com numeração sequencial por ano (RF10, RF11).
- Criar a autenticação e o perfil de signatário autorizado (RN10).
