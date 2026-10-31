# MVP Schulz — Calibração de Instrumentos (Parte 1)

Projeto Aplicado I — UniSENAI/SC | Empresa parceira: **Schulz S.A.** (Laboratório de Metrologia)
Docentes: Prof. MSc. Hugo Menezes Barra e Prof. Rodrigo Losina

## Sobre o projeto

A Schulz emite entre 600 e 700 certificados de calibração por mês, e hoje boa parte do trabalho é manual: copiar resultados da máquina de medição para planilhas e conferir, linha a linha, se cada medida está dentro da tolerância.

Esta é a **Parte 1 do MVP**: as classes do sistema em Programação Orientada a Objetos (Python) e a persistência dos dados em um banco relacional **SQLite**. O sistema já calcula o erro de cada parâmetro e decide se ele está **APROVADO** ou **REPROVADO**.

## Estrutura do repositório

| Arquivo | Descrição |
|---|---|
| `03_banco.sql` | Script de criação das tabelas `tecnicos`, `equipamentos` e `medicoes` |
| `04_classes.py` | Classes `Tecnico`, `Equipamento`, `Medicao` e `BancoDados` (INSERT, SELECT, UPDATE e DELETE) |
| `05_main.py` | Demonstração: insere dados de teste, faz consulta com JOIN e exibe o relatório de calibração |
| `06_mvp_parte1.md` | Documentação técnica: padrões de POO, UML, tratamento de erros e validação do fluxo |

## Como executar

Requisito: Python 3 instalado (o módulo `sqlite3` já vem incluído).

```
python 05_main.py
```

O programa cria o arquivo `calibracao_schulz.db`, insere os 14 parâmetros do certificado de calibração nº 00091/2026 e imprime o relatório no terminal.

## Regras de negócio implementadas

- **Erro** = valor obtido − valor nominal.
- **Limites** = valor nominal + tolerância superior / inferior.
- **Status** = `REPROVADO` quando o valor obtido (considerando a incerteza expandida) ultrapassa algum dos limites; caso contrário, `APROVADO`.

## Próximos passos (Parte 2)

- Leitura do relatório da máquina de medição (Excel)
- Higienização dos dados de entrada
- Cálculo completo da incerteza de medição
- Geração do certificado em PDF
